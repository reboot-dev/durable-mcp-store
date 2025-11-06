# durable-mcp-store
An store checkout example using Reboot's durable-mcp-python, mcp, and mcp-ui.

# To run backend:
- `uv sync`
- `source .venv/bin/activate`
- `rbt dev run`


# To run mcp-ui components:
- `cd web`
- Once: `npm install`
- `npm run dev`

# Connect to Goose
- Open Extension -> Add custom extension
- Extension name, e.g., "Shopping"
- Type: Streamable HTTP
- Description: "A collection of Reboot-backed shopping endpoints"
- Select "Add Extension"