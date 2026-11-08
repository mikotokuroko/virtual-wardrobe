# 06: Style purchases that lack photos

**What to build:** A tester uses a confirmed purchase in an outfit when its description identifies it, and can supply missing details for an ambiguous piece.

**Blocked by:** 02 Get a first outfit in ChatGPT, 05 Add only the purchases the tester kept

**Status:** ready-for-agent

- [x] Confirm black wide-leg trousers from a receipt without a usable photo. Request an outfit with them and verify the trousers appear by description.
- [x] Confirm a code-only piece labelled Style 4102. Ask to style it and verify the plugin requests identifying input before recommending it.
- [x] Try a short description and a photo in separate cases. Verify each identifies the existing item for styling and preserves a single wardrobe entry.

Local MCP tests cover text-only styling, the identification prompt, and both description and photo updates on the original receipt item. Photo retries preserve its ID. Live ChatGPT verification is pending.
