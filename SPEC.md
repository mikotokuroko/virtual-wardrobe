# Virtual wardrobe for ChatGPT

## Problem Statement

When I ask what to wear, I want an answer I can act on with clothes I own. Some pieces appear in order emails, some I can photograph, and some purchases were gifts or returns. Rebuilding that context every time I ask for an outfit makes the advice hard to use.

## Solution

Give each invited tester a private wardrobe in ChatGPT. In their first chat, they can upload photos, describe an occasion and see an outfit assembled from their pieces. Later, they can ask the plugin to search Gmail, review purchases by order and add the pieces they kept.

## User Stories

1. As a tester, I want a private wardrobe, so that only my own items appear in my outfits.
2. As a new tester, I want to start with photos, so that I can get an outfit before connecting Gmail.
3. As a wardrobe owner, I want to upload tops, bottoms and accessories, so that the stylist can combine pieces from across my wardrobe.
4. As a wardrobe owner, I want to correct a piece’s description, so that the stylist uses its actual colour and category.
5. As a returning tester, I want my wardrobe available in a later chat, so that I can reuse earlier additions.
6. As a wardrobe owner, I want to describe an occasion in my own words, so that the outfit suits my plans.
7. As a wardrobe owner, I want to specify a piece to wear, so that the stylist builds the outfit around it.
8. As a wardrobe owner, I want to see the chosen pieces together with available photos, so that I can recognise the suggested combination.
9. As a wardrobe owner, I want to keep one piece and swap another, so that I can refine an outfit in conversation.
10. As a tester with an incomplete wardrobe, I want a partial outfit and a question about what else I own, so that I can fill the gap.
11. As a wardrobe owner, I want shopping suggestions only when I ask, so that everyday styling stays focused on my clothes.
12. As a Gmail user, I want to connect my own account and start a receipt search myself, so that I control when the plugin reads my mail.
13. As a buyer, I want to review detected purchases together by order, so that I can recognise the transaction.
14. As a buyer, I want to select the individual pieces I kept, so that gifts and returns stay out of my wardrobe.
15. As a repeat importer, I want prior choices remembered, so that the same purchase neither duplicates an item nor reopens a settled decision.
16. As a buyer with a text-only receipt, I want to use a recognisable description, so that a missing photo need not delay styling.
17. As a buyer with a vague receipt, I want to supply a description or photo, so that the stylist can identify the piece before using it.

## Implementation Decisions

- Use a ChatGPT plugin with durable per-owner storage. Scope wardrobe reads, writes, photos, Gmail authorisation and import decisions to the authenticated owner.
- Accept photos independently of email. Use the owner’s corrections when identifying and styling a wardrobe item.
- Keep receipt discovery separate from adding items. Present detected purchases by order and persist each review decision. Confirming a kept piece and recording its import must produce a single wardrobe item even if the request is retried.
- Search Gmail on explicit request using read-only access. A declined connection or failed search must leave the existing wardrobe usable.
- Select identifiable wardrobe items for outfits. Honour requested pieces and swaps, show available photos and use descriptions for text-only items. Ask for identifying details before styling a piece known only by a product code.

## Testing Decisions

- Proposed primary test boundary: the plugin as an authenticated ChatGPT user experiences it. Exercise photo intake, wardrobe persistence, receipt review and styling through public plugin operations. The workspace has no existing implementation or test suite.
- Use controlled receipt and photo examples. Check observable wardrobe contents, selected pieces and displayed results across turns. Allow multiple valid outfits and different wording.
- With Gmail disconnected, upload green trousers, two tops and a scarf. Request a dinner outfit including the trousers, then ask to swap the top. Verify the trousers remain, the replacement belongs to the owner and the result identifies each selected piece.
- Import an order with a kept item, a gift and a return. Confirm only the kept item, retry confirmation and repeat the search. Expect one wardrobe item and the earlier review choices. Verify a second tester cannot retrieve those items or purchases.
- Exercise a descriptive receipt without a photo and a code-only receipt. The first can contribute to an outfit after confirmation. The second needs identifying input. With a missing outfit piece, expect a partial result and a follow-up question.
- Confirm the first-outfit experience in ChatGPT itself, including image upload and whether the tester can recognise the pieces in the reply.

## Out of Scope

A standalone website, public rollout, providers beyond Gmail, background inbox monitoring and unsolicited shopping suggestions are outside the pilot.

## Further Notes

The pilot’s first success is a tester finding an outfit they would wear in their first chat. Gmail import helps grow that wardrobe over time.
