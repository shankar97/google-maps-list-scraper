### Maps Extractor MCP Service

This MCP server mirrors the API's fetch behavior and exposes a single tool: `fetch_list`.

### Run the MCP server

```bash
start.sh
```

The server exposes an MCP tool named `fetch_list(url: str)` which returns:

```json
{
  "list_description": "string | null",
  "items": [
    {"name": "str|null", "rating": "str|null", "description": "str|null", "price": "str|null"}
  ]
}
```

It internally calls `app.lib.map_content.fetch.fetch_places` and runs the same checks as the FastAPI service.

### Local claude desktop integration
Add the following blob to your claude_desktop_config.json
```
"mapslist": {
  "command": "<relative-path-to-repo>/start.sh"
}
```


### API Server
There is a FastAPI server setup in the `app` for testing the library method. Alternatively if you want to debug you can start a python shell in the repository and import the fetch method directly to run.
