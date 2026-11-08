"""ChatGPT wardrobe plugin. Run with python wardrobe.py."""
import base64
import json
import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, NotRequired
from urllib.parse import urlsplit
from uuid import uuid4

from gmail_receipts import register_gmail

import httpx
from mcp.server.transport_security import TransportSecuritySettings
from mcp import types
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from pydantic import AnyHttpUrl, ConfigDict, Field, with_config
from typing_extensions import TypedDict


@dataclass(frozen=True)
class Settings:
    database: Path
    resource: str
    issuer: str
    introspection: str
    client: str
    secret: str
    invited: set[str]
    photo_hosts: set[str]
    gmail_client: str = ""
    gmail_secret: str = ""


@with_config(ConfigDict(extra="forbid"))
class Upload(TypedDict):
    download_url: str
    file_id: str
    mime_type: NotRequired[str]
    file_name: NotRequired[str]


Category = Literal["top", "bottom", "accessory"]
Label = Annotated[str, Field(min_length=1, max_length=300, pattern=r"\S")]
OutfitIDs = Annotated[list[str], Field(min_length=1, max_length=8)]
MAX_BYTES = 5 * 1024 * 1024


class Verifier:
    def __init__(self, settings, transport):
        self.settings = settings
        self.transport = transport

    async def verify_token(self, token: str) -> AccessToken | None:
        settings = self.settings
        async with httpx.AsyncClient(transport=self.transport) as client:
            response = await client.post(settings.introspection, data={"token": token},
                                         auth=(settings.client, settings.secret))
            response.raise_for_status()
            claims = response.json()
        audience = claims.get("aud", [])
        if isinstance(audience, str):
            audience = [audience]
        if not isinstance(claims.get("client_id"), str) or not claims["client_id"]:
            return None
        if (claims.get("active") is not True or claims.get("sub") not in settings.invited
                or settings.resource not in audience or claims.get("iss", settings.issuer) != settings.issuer):
            return None
        return AccessToken(token=token, client_id=claims["client_id"], subject=claims["sub"],
                           scopes=claims.get("scope", "").split(), expires_at=claims.get("exp"),
                           resource=settings.resource)


def owner():
    token = get_access_token()
    if token is None or not token.subject:
        raise ValueError("Sign in to access your wardrobe.")
    return token.subject


async def download_photo(url, hosts, transport):
    address = urlsplit(url)
    if (address.scheme != "https" or address.hostname not in hosts or address.username
            or address.password or address.port not in (443, None)):
        raise ValueError("Unsupported photo download host.")
    data = bytearray()
    async with httpx.AsyncClient(transport=transport, trust_env=False) as client:
        async with client.stream("GET", url) as response:
            if response.status_code != 200:
                raise ValueError("Upload the photo again to renew its download link.")
            async for chunk in response.aiter_bytes(65536):
                if len(data) + len(chunk) > MAX_BYTES:
                    raise ValueError("Choose a photo under 5 MiB.")
                data.extend(chunk)
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return bytes(data), "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return bytes(data), "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return bytes(data), "image/webp"
    raise ValueError("Choose a PNG, JPEG or WebP photo.")


def create_server(settings, transport=None):
    for url in (settings.resource, settings.issuer, settings.introspection):
        if not url.startswith("https://"):
            raise ValueError("Use HTTPS for OAuth endpoints.")
    server = FastMCP("Virtual wardrobe", stateless_http=True, json_response=True,
                     transport_security=TransportSecuritySettings(allowed_hosts=[urlsplit(settings.resource).netloc]),
                     instructions=(
                         "Inspect each attached garment photo, suggest its colour, category and "
                         "description, and ask the tester to confirm or correct before saving. "
                         "For an outfit request, call list_items. Choose complementary pieces "
                         "from those results for the requested occasion, including any piece "
                         "the tester asked to wear. Call show_outfit with the selected IDs in "
                         "display order. Describe the combination and why it suits the occasion. "
                         "For a swap, use swap_outfit_item with the last shown outfit, the piece "
                         "to replace and a suitable alternative from list_items. Preserve the "
                         "occasion and all other pieces. If the requested piece is missing, "
                         "show the suitable owned pieces with show_outfit and pass missing_piece "
                         "to ask what else the tester owns. If none fit, ask directly. "
                         "Only suggest shopping when the tester explicitly requests it. "
                         + Path(__file__).with_name("skills").joinpath(
                             "read-wardrobe-receipts", "SKILL.md"
                         ).read_text(encoding="utf-8").split("---", 2)[2].strip()
                     ),
                     token_verifier=Verifier(settings, transport),
                     auth=AuthSettings(issuer_url=AnyHttpUrl(settings.issuer),
                                       resource_server_url=AnyHttpUrl(settings.resource),
                                       required_scopes=["wardrobe"], validate_token_resource=True))

    def connect():
        db = sqlite3.connect(settings.database)
        db.row_factory = sqlite3.Row
        return db

    settings.database.touch(mode=0o600, exist_ok=True)
    settings.database.chmod(0o600)
    with closing(connect()) as db, db:
        db.execute("""CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY, owner TEXT NOT NULL, source TEXT NOT NULL,
            category TEXT NOT NULL, colour TEXT NOT NULL, description TEXT NOT NULL,
            photo BLOB NOT NULL, mime TEXT NOT NULL, UNIQUE(owner, source))""")

    fields = "id, category, colour, description"
    auth_meta = {"securitySchemes": [{"type": "oauth2", "scopes": ["wardrobe"]}]}

    @server.tool(meta={**auth_meta, "openai/fileParams": ["photo"]})
    async def save_photo(photo: Upload, category: Category, colour: Label, description: Label) -> dict:
        """Save one attached garment photo after the owner confirms the suggested details."""
        user = owner()
        with closing(connect()) as db:
            existing = db.execute(f"SELECT {fields} FROM items WHERE owner=? AND source=?",
                                  (user, photo["file_id"])).fetchone()
        if existing:
            return dict(existing)
        try:
            data, mime = await download_photo(photo["download_url"], settings.photo_hosts, transport)
        except httpx.RequestError:
            raise ValueError("Photo download failed. Try uploading the photo again.") from None
        with closing(connect()) as db, db:
            db.execute("""INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(owner, source) DO NOTHING""",
                       (str(uuid4()), user, photo["file_id"], category, colour, description, data, mime))
            return dict(db.execute(f"SELECT {fields} FROM items WHERE owner=? AND source=?",
                                   (user, photo["file_id"])).fetchone())

    @server.tool(meta=auth_meta)
    def show_item(item_id: str) -> list[types.TextContent | types.ImageContent]:
        """Show the owner's recorded details and original photo."""
        with closing(connect()) as db:
            row = db.execute(f"SELECT {fields}, photo, mime FROM items WHERE owner=? AND id=?",
                             (owner(), item_id)).fetchone()
        if row is None:
            raise ValueError("Wardrobe item unavailable.")
        return [types.TextContent(type="text", text=json.dumps({k: row[k] for k in fields.split(", ")})),
                types.ImageContent(type="image", mimeType=row["mime"],
                                   data=base64.b64encode(row["photo"]).decode())]

    @server.tool(meta=auth_meta, annotations=types.ToolAnnotations(readOnlyHint=True))
    def show_outfit(
        item_ids: OutfitIDs, missing_piece: Label | None = None,
    ) -> list[types.TextContent | types.ImageContent]:
        """Display the selected wardrobe items together, pairing each description with its photo."""
        if len(set(item_ids)) != len(item_ids):
            raise ValueError("Choose each wardrobe item only once.")
        content = []
        for item_id in item_ids:
            content.extend(show_item(item_id))
        if missing_piece:
            content.append(types.TextContent(type="text", text=(
                f"This is a partial outfit. What do you own that could work for {missing_piece}?"
            )))
        return content

    @server.tool(meta=auth_meta, annotations=types.ToolAnnotations(readOnlyHint=True))
    def swap_outfit_item(
        item_ids: OutfitIDs, replace_id: str, replacement_id: str,
    ) -> list[types.TextContent | types.ImageContent]:
        """Redisplay the last outfit with exactly one piece replaced, preserving order."""
        if item_ids.count(replace_id) != 1 or replacement_id in item_ids:
            raise ValueError("Select one current piece and a different wardrobe item.")
        with closing(connect()) as db:
            existing = db.execute("SELECT 1 FROM items WHERE owner=? AND id=?",
                                  (owner(), replace_id)).fetchone()
        if existing is None:
            raise ValueError("Wardrobe item unavailable.")
        return show_outfit([replacement_id if item == replace_id else item for item in item_ids])

    @server.tool(meta=auth_meta)
    def list_items() -> list[dict]:
        """Find the signed-in tester's saved wardrobe items, including their IDs."""
        with closing(connect()) as db:
            return [dict(row) for row in db.execute(
                f"SELECT {fields} FROM items WHERE owner=? ORDER BY rowid", (owner(),))]

    @server.tool(meta=auth_meta)
    def correct_item(item_id: str, category: Category | None = None,
                     colour: Label | None = None, description: Label | None = None) -> dict:
        """Update the owner's item details, carrying forward fields they did not change."""
        with closing(connect()) as db, db:
            row = db.execute(f"""UPDATE items SET category=coalesce(?, category),
                              colour=coalesce(?, colour), description=coalesce(?, description)
                              WHERE owner=? AND id=? RETURNING {fields}""",
                             (category, colour, description, owner(), item_id)).fetchone()
            if row is None:
                raise ValueError("Wardrobe item unavailable.")
            return dict(row)

    register_gmail(server, settings, connect, owner, auth_meta, transport)
    return server


if __name__ == "__main__":
    import logging

    # Signed attachment URLs contain short-lived credentials.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    os.umask(0o077)
    env = os.environ
    def values(name):
        return {value.strip() for value in env[name].split(",") if value.strip()}

    settings = Settings(Path(env.get("WARDROBE_DB", "wardrobe.sqlite3")),
                        env["WARDROBE_RESOURCE"], env["WARDROBE_ISSUER"],
                        env["WARDROBE_INTROSPECTION"], env["WARDROBE_CLIENT"],
                        env["WARDROBE_SECRET"], values("WARDROBE_INVITED"),
                        values("WARDROBE_PHOTO_HOSTS"), env.get("GMAIL_CLIENT_ID", ""),
                        env.get("GMAIL_CLIENT_SECRET", ""))
    create_server(settings).run(transport="streamable-http")
