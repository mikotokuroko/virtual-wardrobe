# 04: Find Gmail purchases on demand

**What to build:** A tester connects their own Gmail account and asks the plugin to find orders for review.

**Blocked by:** 01 Save a wardrobe item from a photo

**Status:** ready-for-agent

- [ ] Request read-only authorisation and search the connected account only when its owner asks.
- [ ] Show detected purchases grouped by order. Discovery alone leaves wardrobe contents unchanged.
- [ ] Verify another tester cannot view the results or search the first tester’s mailbox.
- [ ] After declined access or a failed search, verify the tester can still use the existing wardrobe.

## Comments

Implemented optional read-only Gmail consent, browser-to-wardrobe pairing and explicit paginated receipt search. Local MCP tests with simulated Google endpoints cover grouped results, cross-owner isolation, declined consent and search failure. Live Gmail consent and merchant receipt recognition remain to be checked with a configured pilot OAuth client.
