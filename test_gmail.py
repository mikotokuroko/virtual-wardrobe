import base64
import json
import unittest
from dataclasses import replace
from urllib.parse import parse_qs, urlsplit

import httpx

from gmail_receipts import SCOPE
import test_wardrobe
from wardrobe import create_server


class GmailTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.pilot = test_wardrobe.WardrobeTest()
        await self.pilot.asyncSetUp()
        self.addCleanup(self.pilot.doCleanups)
        self.pilot.settings = replace(self.pilot.settings, gmail_client="test-client", gmail_secret="test-secret")
        original = self.pilot.external
        self.searches = []
        self.failure = False

        async def google(request):
            if request.url.host == "oauth2.googleapis.com":
                return httpx.Response(200, json={"scope": SCOPE, "access_token": "alice-gmail", "expires_in": 3600})
            if request.url.host != "gmail.googleapis.com":
                return await original.handle_async_request(request)
            self.assertEqual(request.headers["Authorization"], "Bearer alice-gmail")
            self.searches.append(request.url.path)
            if self.failure:
                return httpx.Response(503)
            if request.url.path.endswith("/messages"):
                return httpx.Response(200, json={"messages": [{"id": "m1"}, {"id": "m2"}]})
            body = ("Green trousers  $49.00\nSilk scarf  $20.00\nTotal  $69.00"
                    if request.url.path.endswith("/m1") else "Silk scarf  $20.00")
            raw = ("From: Shop <shop@example.org>\nSubject: Order #104\n\n" + body).encode()
            return httpx.Response(200, json={"raw": base64.urlsafe_b64encode(raw).decode()})

        self.pilot.external = httpx.MockTransport(google)

    async def connect(self, consent):
        reply = await self.pilot.call("connect_gmail", {})
        link = json.loads(reply["content"][0]["text"])["connect_url"]
        app = create_server(self.pilot.settings, self.pilot.external).streamable_http_app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="https://wardrobe.example") as browser:
            response = await browser.get(link)
            params = parse_qs(urlsplit(response.headers["location"]).query)
            self.assertEqual(params["scope"], [SCOPE])
            self.assertEqual(params["code_challenge_method"], ["S256"])
            callback = {"state": params["state"][0]}
            callback.update({"code": "test-code"} if consent else {"error": "access_denied"})
            result = await browser.get("/gmail/callback", params=callback)
            self.assertEqual(result.status_code, 200)
            self.assertEqual((await browser.get("/gmail/callback", params=callback)).status_code, 400)
        if consent:
            code = result.text.split()[-1]
            self.assertTrue((await self.pilot.call("finish_gmail_connection",
                                                   {"pairing_code": code}, "bob"))["isError"])
            paired = await self.pilot.call("finish_gmail_connection", {"pairing_code": code})
            self.assertFalse(paired.get("isError"))
        self.assertEqual(self.searches, [])

    async def test_search_groups_orders_and_isolates_owner(self):
        await self.connect(True)
        denied = await self.pilot.call("find_gmail_purchases", {}, "bob")
        self.assertTrue(denied["isError"])
        self.assertEqual(self.searches, [])
        result = await self.pilot.call("find_gmail_purchases", {})
        orders = json.loads(result["content"][0]["text"])["orders"]
        self.assertEqual(orders, [{"merchant": "shop@example.org", "order": "104",
                                   "items": ["Green trousers", "Silk scarf"]}])
        wardrobe = await self.pilot.call("list_items", {})
        self.assertEqual(wardrobe["structuredContent"]["result"], [])

    async def test_decline_and_outage_preserve_saved_item(self):
        saved = await self.pilot.call("save_photo", {"photo": self.pilot.file, **self.pilot.details})
        item = json.loads(saved["content"][0]["text"])
        await self.connect(False)
        self.assertTrue((await self.pilot.call("find_gmail_purchases", {}))["isError"])
        await self.connect(True)
        self.failure = True
        self.assertTrue((await self.pilot.call("find_gmail_purchases", {}))["isError"])
        after = await self.pilot.call("list_items", {})
        self.assertEqual(after["structuredContent"]["result"], [item])
