# 05: Add only the purchases the tester kept

**What to build:** A tester reviews an order and chooses which detected purchases become wardrobe items.

**Blocked by:** 04 Find Gmail purchases on demand

**Status:** ready-for-agent

- [ ] For an order containing jeans, a gift scarf and a returned shirt, confirm only the jeans. Verify only the jeans enter the wardrobe.
- [ ] Retry confirmation, including overlapping requests, and repeat the search. Verify exactly one wardrobe item exists and settled choices stay settled.
- [ ] Verify a second tester cannot retrieve or change the first tester’s purchase decisions.
