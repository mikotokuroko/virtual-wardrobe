"""Single-user stdio entry point for the desktop plugin."""
import os
import subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from wardrobe import register_tools, styling_instructions


def main():
    os.umask(0o077)
    root = Path.home() / "Library" / "Application Support" / "Virtual Wardrobe Pilot"
    photos = root / "photos"
    photos.mkdir(parents=True, exist_ok=True, mode=0o700)
    server = FastMCP("Virtual Wardrobe Pilot Local", instructions=styling_instructions())
    register_tools(server, root / "wardrobe.sqlite3", {"files.oaiusercontent.com", "files.openai.com"},
                   lambda: "local", None, {}, photos)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def get_storage_usage() -> dict[str, int]:
        """Measure allocated local disk space in KiB. The plugin install is separate."""
        def disk_kib(path: Path) -> int:
            output = subprocess.check_output(["/usr/bin/du", "-sk", str(path)], text=True)
            return int(output.split(maxsplit=1)[0])

        return {
            "wardrobe_data_total_kib": disk_kib(root),
            "display_photo_cache_kib_included_in_total": disk_kib(photos),
            "plugin_install_kib_separate": disk_kib(Path(__file__).resolve().parent),
        }

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
