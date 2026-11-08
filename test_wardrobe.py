import base64
import json
import tempfile
import unittest
from pathlib import Path

import httpx

from wardrobe import Settings, create_server


PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jHioAAAAASUVORK5CYII=")
RESOURCE = "https://wardrobe.example/mcp"


class WardrobeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.settings = Settings(Path(directory.name) / "items.db", RESOURCE,
                                 "https://id.example", "https://id.example/check",
                                 "client", "secret", {"alice", "bob"}, {"files.example"})
        def external(request):
            if request.url.host == "files.example":
                return httpx.Response(200, content=PNG)
            from urllib.parse import parse_qs
            user = parse_qs(request.content.decode())["token"][0]
            return httpx.Response(200, json={"active": True, "sub": user,
                "client_id": "shared-chatgpt-client", "aud": RESOURCE, "scope": "wardrobe"})
        self.external = httpx.MockTransport(external)
        self.file = {"file_id": "file-photo", "download_url": "https://files.example/photo"}
        self.details = {"category": "top", "colour": "blue", "description": "cotton blouse"}

    async def rpc(self, method, params, user="alice"):
        server = create_server(self.settings, self.external)
        app = server.streamable_http_app()
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                         base_url="https://wardrobe.example") as client:
                return await client.post("/mcp", headers={"Authorization": "Bearer " + user,
                    "Accept": "application/json, text/event-stream"}, json={
                        "jsonrpc": "2.0", "id": 1, "method": method, "params": params})

    async def call(self, name, arguments, user="alice"):
        response = await self.rpc("tools/call", {"name": name, "arguments": arguments}, user)
        response.raise_for_status()
        return response.json()["result"]

    async def test_anonymous_discovery_keeps_inventory_private(self):
        app = create_server(self.settings, self.external).streamable_http_app()
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                         base_url="https://wardrobe.example") as client:
                async def post(method, params):
                    return await client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                                           "method": method, "params": params})
                init = await post("initialize", {"protocolVersion": "2025-03-26"})
                self.assertEqual(init.json()["result"]["protocolVersion"], "2025-03-26")
                listing = await post("tools/list", {})
                self.assertIn("show_outfit", [t["name"] for t in listing.json()["result"]["tools"]])
                denied = await post("tools/call", {"name": "list_items", "arguments": {}})
                self.assertEqual(denied.status_code, 401)

    async def test_save_then_retrieve(self):
        listing = (await self.rpc("tools/list", {})).json()["result"]["tools"]
        tool = next(t for t in listing if t["name"] == "save_photo")
        self.assertEqual(tool["_meta"]["openai/fileParams"], ["photo"])
        saved = await self.call("save_photo", {"photo": self.file, **self.details})
        item = json.loads(saved["content"][0]["text"])
        self.assertEqual(item["colour"], "blue")
        viewed = await self.call("show_item", {"item_id": item["id"]})
        self.assertEqual(base64.b64decode(viewed["content"][1]["data"]), PNG)

    async def test_correct_and_find_in_later_chat(self):
        saved = await self.call("save_photo", {"photo": self.file, **self.details})
        item = json.loads(saved["content"][0]["text"])
        corrected = {**self.details, "colour": "green"}
        result = await self.call("correct_item", {"item_id": item["id"], "colour": "green"})
        self.assertFalse(result.get("isError"))
        await self.call("save_photo", {"photo": self.file, **self.details})
        listed = await self.call("list_items", {})
        self.assertEqual(listed["structuredContent"]["result"], [{"id": item["id"], **corrected}])

    async def test_private_to_signed_in_tester(self):
        saved = await self.call("save_photo", {"photo": self.file, **self.details})
        item = json.loads(saved["content"][0]["text"])
        self.assertEqual((await self.call("list_items", {}, "bob"))["structuredContent"]["result"], [])
        for tool, args in [("show_item", {}), ("correct_item", {"description": "wrong owner"})]:
            result = await self.call(tool, {"item_id": item["id"], **args}, "bob")
            self.assertTrue(result["isError"])
            self.assertNotIn("cotton blouse", str(result))
        unchanged = await self.call("list_items", {})
        self.assertEqual(unchanged["structuredContent"]["result"], [item])
        denied = await self.rpc("tools/list", {}, "uninvited")
        self.assertEqual(denied.status_code, 401)

    async def save_sample_wardrobe(self):
        items = []
        for category, colour, description in [
            ("bottom", "green", "trousers"), ("top", "white", "linen shirt"),
            ("top", "blue", "tee"), ("accessory", "grey", "scarf"),
        ]:
            photo = {**self.file, "file_id": description}
            saved = await self.call("save_photo", {"photo": photo, "category": category,
                                    "colour": colour, "description": description})
            items.append(json.loads(saved["content"][0]["text"]))
        return items

    async def test_show_selected_outfit(self):
        items = await self.save_sample_wardrobe()
        selected = [items[i] for i in (0, 1, 3)]
        ids = [item["id"] for item in selected]
        outfit = await self.call("show_outfit", {"item_ids": ids})
        self.assertFalse(outfit.get("isError"))
        blocks = outfit["content"]
        self.assertEqual([json.loads(block["text"]) for block in blocks[::2]], selected)
        self.assertEqual([base64.b64decode(block["data"]) for block in blocks[1::2]], [PNG] * 3)
        foreign = await self.call("save_photo", {"photo": self.file, **self.details}, "bob")
        ids.append(json.loads(foreign["content"][0]["text"])["id"])
        denied = await self.call("show_outfit", {"item_ids": ids})
        self.assertTrue(denied["isError"])
        self.assertFalse(any(block["type"] == "image" for block in denied["content"]))

    async def test_swap_keeps_trousers_and_scarf(self):
        trousers, shirt, tee, scarf = await self.save_sample_wardrobe()
        args = {"item_ids": [piece["id"] for piece in (trousers, shirt, scarf)],
                "replace_id": shirt["id"], "replacement_id": tee["id"]}
        result = await self.call("swap_outfit_item", args)
        self.assertEqual([json.loads(block["text"]) for block in result["content"][::2]],
                         [trousers, tee, scarf])
        other = await self.call("save_photo", {"photo": self.file, **self.details}, "bob")
        args["replacement_id"] = json.loads(other["content"][0]["text"])["id"]
        refused = await self.call("swap_outfit_item", args)
        self.assertTrue(refused["isError"])
        self.assertFalse(any(block["type"] == "image" for block in refused["content"]))

    async def test_missing_piece_returns_partial_outfit_and_question(self):
        trousers, *_ = await self.save_sample_wardrobe()
        result = await self.call("show_outfit", {"item_ids": [trousers["id"]],
                                                 "missing_piece": "formal shoes"})
        details, photo, question = result["content"]
        self.assertEqual(json.loads(details["text"]), trousers)
        self.assertEqual(photo["type"], "image")
        self.assertIn("What do you own", question["text"])
        self.assertIn("formal shoes", question["text"])
