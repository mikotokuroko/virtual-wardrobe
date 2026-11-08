# 03: Refine an outfit and handle missing pieces

**What to build:** A tester adjusts a suggested outfit in conversation and can still use the pieces available when their wardrobe is incomplete.

**Blocked by:** 02 Get a first outfit in ChatGPT

**Status:** ready-for-agent

- [ ] Given an outfit with green trousers and two suitable tops in the wardrobe, ask to keep the trousers and swap the top. Verify the trousers remain and the alternate top is shown.
- [ ] When a requested piece is missing, show a partial outfit using owned pieces and ask what else the tester owns.
- [ ] Offer shopping suggestions only when the tester requests them.

## Comments

Local MCP tests verified swapping the shirt while keeping the trousers and scarf, rejecting another tester’s replacement, and returning an owned partial outfit with a question about missing formal shoes. The plugin instructs ChatGPT to offer shopping suggestions only on explicit request. Live conversational behaviour remains pending.
