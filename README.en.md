# virtual-wardrobe

[简体中文](README.md)

Build a wardrobe on your Mac from garment photos and purchase receipts. Ask ChatGPT to put together outfits using the clothes you own.

## Start a conversation

Open the plugin and ask “Where do I start?” or try one of these:

- **Add a photo.** Attach a garment photo and say “Add this to my wardrobe.” Confirm its colour, category and description to save it. JPEG, PNG and WebP images up to 5 MiB are supported.
- **Add purchases.** Ask “Find my recent clothing receipts in Gmail.” You can also use connected Apple Mail or paste a receipt. Choose the pieces you kept. The plugin remembers those choices. For text-only pieces, it asks whether to find a product photo and prefers a garment-only image in the verified style and colour.
- **Choose an outfit.** Try “Style my white top for a formal interview.” You’ll see saved photos and any pieces missing from the outfit. For an open brief like “I want a whimsical siren look,” it shows two looks side by side when your wardrobe supports both.
- **Refine a look.** Say “Keep the trousers from the first look, swap the top and make it more mysterious.” You can share fit preferences or optional measurements such as height, weight or inseam for suggestions in that chat.

## Install on macOS

Use Python 3.11 or later and a Codex CLI with local plugin support. Run these commands in Terminal.

```sh
git clone https://github.com/mikotokuroko/virtual-wardrobe.git
cd virtual-wardrobe
pilot="$HOME/.local/share/wardrobe-pilot"
mkdir -p "$pilot"
cp wardrobe.py wardrobe_local.py "$pilot/"
cp -R skills "$pilot/"
python3 -m venv "$pilot/venv"
"$pilot/venv/bin/python" -m pip install -r requirements.txt
codex plugin marketplace add "$PWD/desktop"
codex plugin add wardrobe-local@wardrobe-pilot
```

Keep the cloned repository in place, restart the desktop app and select **virtual-wardrobe** in a new chat.

## Local storage

The wardrobe database and display-photo cache live in `~/Library/Application Support/Virtual Wardrobe Pilot/`. Ask “How much space is my wardrobe using on my Mac?” for the current wardrobe data and plugin installation sizes.
