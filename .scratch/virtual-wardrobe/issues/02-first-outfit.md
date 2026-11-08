# 02: Get a first outfit in ChatGPT

**What to build:** A tester describes an occasion and sees a combination of their own pieces in the same chat.

**Blocked by:** 01 Save a wardrobe item from a photo

**Status:** ready-for-agent

- [ ] In ChatGPT with Gmail disconnected, upload green trousers, two tops and a scarf. Ask for a casual dinner outfit including the trousers.
- [ ] Verify the outfit honours the occasion and includes the requested trousers. Every selection belongs to the tester.
- [ ] Display the chosen pieces together with their available photos and verify the tester can recognise them.

## Comments

Implemented outfit selection instructions for ChatGPT and the authenticated outfit display tool. The local MCP integration test exercises a four-piece wardrobe, returns the selected trousers, shirt and scarf with their photos in order, and rejects a selection containing another tester’s item. Live occasion matching and photo recognition in ChatGPT remain pending.
