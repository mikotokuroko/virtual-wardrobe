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
                         + "\n\n".join(
                             (Path(__file__).with_name("skills") / name / "SKILL.md")
                             .read_text(encoding="utf-8").split("---", 2)[2].strip()
                             for name in ("style-wardrobe-outfit", "read-wardrobe-receipts")
                         )
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

        db.execute("""CREATE TABLE IF NOT EXISTS receipt_decisions (
            owner TEXT NOT NULL, merchant TEXT NOT NULL, receipt TEXT NOT NULL,
            line TEXT NOT NULL, item_id TEXT, PRIMARY KEY(owner, merchant, receipt, line))""")
        # Retire credentials issued by the previous direct Gmail integration.
        for table in ("gmail_links", "gmail_pairing", "gmail_accounts"):
            db.execute(f"DROP TABLE IF EXISTS {table}")

    fields = "id, category, colour, description"
    auth_meta = {"securitySchemes": [{"type": "oauth2", "scopes": ["wardrobe"]}]}

    @server.tool(meta={**auth_meta, "openai/fileParams": ["photo"]})
    async def save_photo(photo: Upload, category: Category, colour: Label, description: Label,
                         existing_item_id: str | None = None) -> dict:
        """Save a confirmed garment photo. Pass existing_item_id when identifying a saved receipt item."""
        user = owner()
        with closing(connect()) as db:
            existing = db.execute(f"SELECT {fields} FROM items WHERE owner=? AND source=?",
                                  (user, photo["file_id"])).fetchone()
            if existing_item_id is not None:
                target = db.execute("SELECT 1 FROM items WHERE owner=? AND id=?",
                                    (user, existing_item_id)).fetchone()
                if target is None:
                    raise ValueError("Wardrobe item unavailable.")
        if existing:
            if existing_item_id is not None and existing["id"] != existing_item_id:
                raise ValueError("This photo already belongs to another wardrobe item.")
            return dict(existing)
        try:
            data, mime = await download_photo(photo["download_url"], settings.photo_hosts, transport)
        except httpx.RequestError:
            raise ValueError("Photo download failed. Try uploading the photo again.") from None
        with closing(connect()) as db, db:
            if existing_item_id is not None:
                try:
                    row = db.execute(f"""UPDATE items SET source=?, category=?, colour=?, description=?,
                                       photo=?, mime=? WHERE owner=? AND id=? AND length(photo)=0
                                       RETURNING {fields}""",
                                     (photo["file_id"], category, colour, description, data, mime,
                                      user, existing_item_id)).fetchone()
                except sqlite3.IntegrityError:
                    raise ValueError("This photo already belongs to another wardrobe item.") from None
                if row is None:
                    row = db.execute(f"SELECT {fields} FROM items WHERE owner=? AND id=? AND source=?",
                                     (user, existing_item_id, photo["file_id"])).fetchone()
                if row is None:
                    raise ValueError("This wardrobe item already has a photo.")
                return dict(row)
            db.execute("""INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(owner, source) DO NOTHING""",
                       (str(uuid4()), user, photo["file_id"], category, colour, description, data, mime))
            return dict(db.execute(f"SELECT {fields} FROM items WHERE owner=? AND source=?",
                                   (user, photo["file_id"])).fetchone())

    def item_content(item_id: str, for_outfit: bool) -> list[types.TextContent | types.ImageContent]:
        with closing(connect()) as db:
            row = db.execute(f"SELECT {fields}, photo, mime FROM items WHERE owner=? AND id=?",
                             (owner(), item_id)).fetchone()
        if row is None:
            raise ValueError("Wardrobe item unavailable.")
        if for_outfit and row["category"] == "unknown":
            raise ValueError(f"Please identify {row['description']} with a short description or photo before styling it.")
        content = [types.TextContent(type="text", text=json.dumps({k: row[k] for k in fields.split(", ")}))]
        if row["photo"]:
            content.append(types.ImageContent(type="image", mimeType=row["mime"],
                                              data=base64.b64encode(row["photo"]).decode()))
        return content

    @server.tool(meta=auth_meta)
    def show_item(item_id: str) -> list[types.TextContent | types.ImageContent]:
        """Show the owner's recorded details and any available photo."""
        return item_content(item_id, for_outfit=False)

    @server.tool(meta=auth_meta, annotations=types.ToolAnnotations(readOnlyHint=True))
    def reviewed_receipt_lines(merchant: Label, receipt_ref: Label) -> list[dict]:
        """Look up settled line references before presenting an order for review."""
        with closing(connect()) as db:
            rows = db.execute("""SELECT line, item_id FROM receipt_decisions
                              WHERE owner=? AND merchant=? AND receipt=? ORDER BY line""",
                              (owner(), merchant.strip().casefold(), receipt_ref.strip().casefold()))
            return [{"line_ref": row["line"], "kept": row["item_id"] is not None,
                     "item_id": row["item_id"]} for row in rows]

    @server.tool(meta=auth_meta)
    def record_receipt_choice(merchant: Label, receipt_ref: Label, line_ref: Label,
                              kept: bool, description: Label | None = None,
                              category: Category | None = None, colour: Label | None = None) -> dict:
        """Record an explicit keep or skip for one receipt unit. Replays return its original decision."""
        user = owner()
        key = (user, merchant.strip().casefold(), receipt_ref.strip().casefold(), line_ref.strip().casefold())
        with closing(connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("""SELECT item_id FROM receipt_decisions
                                  WHERE owner=? AND merchant=? AND receipt=? AND line=?""", key).fetchone()
            if existing:
                item_id = existing["item_id"]
            else:
                item_id = None
                if kept:
                    if not description:
                        raise ValueError("Provide the confirmed piece's description.")
                    item_id = str(uuid4())
                    db.execute("""INSERT INTO items (id, owner, source, category, colour, description, photo, mime)
                               VALUES (?, ?, ?, ?, ?, ?, X'', '')""",
                               (item_id, user, "receipt:" + item_id, category or "unknown",
                                colour or "unknown", description))
                db.execute("INSERT INTO receipt_decisions VALUES (?, ?, ?, ?, ?)", (*key, item_id))
        return {"line_ref": key[-1], "kept": item_id is not None, "item_id": item_id}

    @server.tool(meta=auth_meta, annotations=types.ToolAnnotations(readOnlyHint=True))
    def show_outfit(
        item_ids: OutfitIDs, missing_piece: Label | None = None,
    ) -> list[types.TextContent | types.ImageContent]:
        """Display the selected wardrobe items together, pairing each description with its photo."""
        if len(set(item_ids)) != len(item_ids):
            raise ValueError("Choose each wardrobe item only once.")
        content = []
        for item_id in item_ids:
            content.extend(item_content(item_id, for_outfit=True))
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
                        values("WARDROBE_PHOTO_HOSTS"))
    create_server(settings).run(transport="streamable-http")
