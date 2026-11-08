import asyncio
import json
import unittest

import test_wardrobe


class ReceiptReviewTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.pilot = test_wardrobe.WardrobeTest()
        await self.pilot.asyncSetUp()
        self.addCleanup(self.pilot.doCleanups)
        self.order = {"merchant": "Example Shop", "receipt_ref": "104"}

    async def choice(self, line, kept, user="alice", **details):
        result = await self.pilot.call("record_receipt_choice", {
            **self.order, "line_ref": line, "kept": kept, **details}, user)
        self.assertFalse(result.get("isError"), result)
        return json.loads(result["content"][0]["text"])

    async def test_review_retries_skip_gifts_and_returns(self):
        self.assertEqual((await self.pilot.call("reviewed_receipt_lines", self.order))
                         ["structuredContent"]["result"], [])
        first, second = await asyncio.gather(*[
            self.choice("DENIM-01", True, category="bottom", description="Blue jeans")
            for _ in range(2)])
        self.assertEqual(first, second)
        await self.choice("GIFT-SCARF", False)
        await self.choice("RETURNED-SHIRT", False)
        self.assertFalse((await self.choice("gift-scarf", True, description="Scarf"))["kept"])
        listed = (await self.pilot.call("list_items", {}))["structuredContent"]["result"]
        self.assertEqual([item["description"] for item in listed], ["Blue jeans"])
        shown = await self.pilot.call("show_outfit", {"item_ids": [first["item_id"]]})
        self.assertEqual([block["type"] for block in shown["content"]], ["text"])
        reviewed = (await self.pilot.call("reviewed_receipt_lines", self.order))["structuredContent"]["result"]
        self.assertEqual([(r["line_ref"], r["kept"]) for r in reviewed],
                         [("denim-01", True), ("gift-scarf", False), ("returned-shirt", False)])

    async def test_other_owner_and_accounts(self):
        item = await self.choice("linen", True, description="Linen shirt")
        private = await self.pilot.call("reviewed_receipt_lines", self.order, "bob")
        self.assertEqual(private["structuredContent"]["result"], [])
        denied = await self.pilot.call("show_item", {"item_id": item["item_id"]}, "bob")
        self.assertTrue(denied["isError"])
        await self.choice("linen", False, "bob")
        self.assertTrue((await self.choice("linen", False))["kept"])
        tools = (await self.pilot.rpc("tools/list", {})).json()["result"]["tools"]
        self.assertFalse(any("gmail" in tool["name"] for tool in tools))
