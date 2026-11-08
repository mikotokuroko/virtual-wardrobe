# 05: Add only the purchases the tester kept

**What to build:** A tester reviews an order and chooses which detected purchases become wardrobe items.

**Blocked by:** 04 Find Gmail purchases on demand

**Status:** ready-for-agent

- [x] For an order containing jeans, a gift scarf and a returned shirt, confirm only the jeans. Verify only the jeans enter the wardrobe.
- [x] Retry confirmation, including overlapping requests, and repeat the search. Verify exactly one wardrobe item exists and settled choices stay settled.
- [x] Verify a second tester cannot retrieve or change the first tester’s purchase decisions.

## Implementation

Local MCP tests verified the confirmed-item handoff, overlapping retries, settled skips and per-owner isolation using synthetic mail-plugin results. The combined workflow still needs a live wardrobe connection in ChatGPT.
