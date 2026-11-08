# Virtual wardrobe pilot

This Python 3.11+ MCP server lets an invited tester save, correct and retrieve clothing photos through ChatGPT. ChatGPT inspects the attachment and proposes details in the conversation. The server stores the confirmed description and original photo in SQLite.

## Run locally

Create a virtual environment, install the dependencies, and run the HTTP integration tests.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v
```

## Connect to ChatGPT

Use a persistent private database directory and an HTTPS reverse proxy to the server on loopback port 8000. Preserve the public Host header and route both MCP and OAuth discovery requests to the server. Configure an OAuth provider that supports ChatGPT's authorization-code flow with PKCE, the wardrobe resource audience, and token introspection using client-secret Basic authentication. Register the redirect URI shown by ChatGPT.

Set the following variables in the server environment, then run `python wardrobe.py`.

| Variable | Value |
| --- | --- |
| WARDROBE_RESOURCE | Public HTTPS MCP URL ending in /mcp |
| WARDROBE_ISSUER | OAuth authorization server issuer |
| WARDROBE_INTROSPECTION | Provider's HTTPS token introspection endpoint |
| WARDROBE_CLIENT and WARDROBE_SECRET | Resource server credentials for introspection |
| WARDROBE_INVITED | Comma-separated OAuth subject IDs of invited testers |
| WARDROBE_PHOTO_HOSTS | Exact trusted hostnames that serve ChatGPT attachment downloads. Configure only dedicated trusted file origins. |
| WARDROBE_DB | Persistent SQLite database path. Defaults to wardrobe.sqlite3 in the working directory. |

Configure the provider to issue user tokens with the wardrobe scope, resource audience and stable subject. Connect the MCP URL in ChatGPT using the provider's ChatGPT client registration. No Gmail connection is needed.

For the live acceptance check, attach a JPEG, PNG or WebP garment photo (up to 5 MiB). Ask to add it, review the suggested colour and category, then confirm or correct them. Open a fresh chat and ask to see the saved piece. Sign in as a second tester and verify they cannot retrieve or change the first tester’s item.

## Receipt review with connected mail plugins

Enable the wardrobe and the desired mail plugin in the same conversation. Ask, for example,
“Use Gmail to find my clothing receipts in the ads account.” Apple Mail can serve the same
role wherever the host offers that connector. Each mail plugin manages its own mailbox
permissions. The wardrobe still uses its own sign-in for private storage.

ChatGPT reads the receipt, shows the pieces by order, and records the owner's keep or skip
choices. Repeating a settled choice returns the original result. Text-only pieces are
available across chats. Only confirmed item details and receipt review keys go to the
wardrobe server. Existing photo wardrobes are preserved when upgrading, and obsolete
local Gmail connection records are removed on startup.
