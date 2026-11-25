import base64
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from test_wardrobe import PNG
from wardrobe import register_tools


class RemoveItemTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.database = self.root / "items.db"
        self.user = "alice"
        # Start with the schema and a photo saved by an earlier installation.
        with sqlite3.connect(self.database) as db:
            db.execute("""CREATE TABLE items (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, source TEXT NOT NULL,
                category TEXT NOT NULL, colour TEXT NOT NULL, description TEXT NOT NULL,
                photo BLOB NOT NULL, mime TEXT NOT NULL, UNIQUE(owner, source))""")
            db.execute("""INSERT INTO items VALUES
                ('legacy', 'alice', 'file-old', 'top', 'red', 'Shirt', ?, 'image/png')""", (PNG,))
        self.start_server()

    def start_server(self):
        self.server = register_tools(FastMCP("local"), self.database, {"files.example"},
                                     lambda: self.user, httpx.MockTransport(
                                         lambda request: httpx.Response(200, content=PNG)), {}, self.root)

    async def result(self, tool, **args):
        content = await self.server.call_tool(tool, args)
        return content[1] if isinstance(content, tuple) else json.loads(content[0].text)

    async def test_returned_variant_stays_settled_across_restart_and_restore(self):
        order = {"merchant": "Shop", "receipt_ref": "42"}
        choices = {"kept": True, "description": "Shirt", "colour": "red", "category": "top"}
        selected = await self.result("record_receipt_choice", **order, **choices, line_ref="S-red-1")
        sibling = await self.result("record_receipt_choice", **order, **choices, line_ref="M-red-1")
        item_id = selected["item_id"]
        variants = (await self.result("list_items", receipt_details=True))["result"]
        self.assertEqual([(r["line_ref"], r["id"]) for r in variants if r["line_ref"]],
                         [("s-red-1", item_id), ("m-red-1", sibling["item_id"])])
        for _ in range(2):
            state = await self.result("remove_item", item_id=item_id)
            self.assertEqual(state["status"], "removed")
        self.start_server()
        archived = (await self.result("list_items", status="removed", receipt_details=True))["result"]
        self.assertEqual([(r["id"], r["line_ref"]) for r in archived], [(item_id, "s-red-1")])
        replay = await self.result("record_receipt_choice", **order, **choices, line_ref="S-red-1")
        self.assertEqual(replay, {"kept": False, "item_id": None, "line_ref": "s-red-1"})
        self.assertIn(replay, (await self.result("reviewed_receipt_lines", **order))["result"])
        active = (await self.result("list_items"))["result"]
        self.assertEqual([r["id"] for r in active], ["legacy", sibling["item_id"]])
        for tool, args in [("show_item", {"item_id": item_id}),
                           ("show_outfit", {"item_ids": [item_id]}),
                           ("swap_outfit_item", {"item_ids": [item_id], "replace_id": item_id,
                                                 "replacement_id": "legacy"}),
                           ("correct_item", {"item_id": item_id, "colour": "blue"}),
                           ("set_product_photo", {"item_id": item_id,
                                                  "image_url": "https://venroy.com.au/photo"})]:
            with self.subTest(tool=tool), self.assertRaises(ToolError):
                await self.server.call_tool(tool, args)
        for _ in range(2):
            restored = await self.result("restore_item", item_id=item_id)
            self.assertEqual(restored["id"], item_id)
        self.assertEqual(await self.result("record_receipt_choice", **order, **choices, line_ref="S-red-1"),
                         selected)

    async def test_other_owner_cannot_change_or_discover_removed_item(self):
        self.user = "bob"
        with self.assertRaisesRegex(ToolError, "unavailable"):
            await self.result("remove_item", item_id="legacy")
        self.user = "alice"
        await self.result("remove_item", item_id="legacy")
        self.user = "bob"
        self.assertEqual((await self.result("list_items", status="removed"))["result"], [])
        with self.assertRaisesRegex(ToolError, "unavailable"):
            await self.result("restore_item", item_id="legacy")

    async def test_legacy_uploaded_photo_survives_removal_and_duplicate_upload(self):
        await self.result("remove_item", item_id="legacy")
        with self.assertRaisesRegex(ToolError, "removed"):
            await self.result("save_photo", photo={"file_id": "file-old",
                              "download_url": "https://files.example/sample"},
                              category="top", colour="blue", description="Duplicate")
        self.assertEqual((await self.result("list_items"))["result"], [])
        await self.result("restore_item", item_id="legacy")
        content, _ = await self.server.call_tool("show_item", {"item_id": "legacy"})
        self.assertEqual(base64.b64decode(content[-1].data), PNG)
        self.assertEqual(json.loads(content[0].text)["colour"], "red")
