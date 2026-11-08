---
name: style-wardrobe-outfit
description: Choose or refine an outfit from the owner's saved wardrobe for an occasion, including requests built around a specific piece.
---

Use list_items to see what the owner has. Start with any piece they asked to wear.
Choose the remaining pieces for their occasion, dress code and stated preferences.
Use the recorded colours, cuts and fabrics to judge how the pieces work together.
For example, for dinner around green trousers, choose a suitable owned top and add
an accessory if it helps the look. Use show_item if a photo would settle a choice.

Call show_outfit with the selected IDs in display order. Name the actual pieces and
give one concrete reason the combination suits the request. An identified receipt
item can be styled by description alone. For an ambiguous item such as “Style 4102,”
ask for a short description or photo before recommending it.

For “keep the trousers, swap the top,” use swap_outfit_item with the last shown IDs,
the current top and a suitable replacement from the wardrobe. Preserve the occasion
and the other pieces. If there is no suitable replacement, say what is missing.
Use show_outfit with the available pieces and missing_piece to ask what else the
owner has. If none fit, ask directly. Suggest shopping only on explicit request.
