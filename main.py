from fastmcp import FastMCP

# Minimal MCP server that exposes a single tool: fetch_list
# This mirrors the API's fetch behavior by calling app.lib.map_content.fetch.fetch_places

mcp = FastMCP("Maps Extractor MCP")


@mcp.tool()
def fetch_list(url: str) -> dict:
    """Fetch a Google Maps list page and return parsed places.

    Args:
        url: The Google Maps URL to scrape.

    Returns:
        A dict with keys: "list_description" (str | None) and "items" (list of dicts).
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be a non-empty string")

    # Import inside the function so this module can import without optional deps
    # when only listing tools or introspecting
    from app.lib.map_content.fetch import fetch_places

    return fetch_places(url)


if __name__ == "__main__":
    mcp.run()


