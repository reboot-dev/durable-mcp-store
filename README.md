# durable-mcp-store

An AI store example using Reboot's durable-mcp-python, mcp, and mcp-ui.

# To run backend:

- `uv sync`
- `source .venv/bin/activate`
- `rbt dev run`
- To simulate a failure run: `FAIL_CHECKOUT=true rbt dev run`

# To run mcp-ui components:

- `cd web`
- Once: `npm install`
- `npm run dev`

# Connect to Goose

Note: Goose must have an API key for e.g., OpenAI, Claude.
Tested with Anthropic's claude-sonnet-4.0.

- Open Extension -> Add custom extension.
- Extension name, e.g., "RebootShop".
- Type: Streamable HTTP.
- Description: "A collection of Reboot-backed shopping endpoints".
- Endpoint `http://127.0.0.1:9991/mcp`
- Select "Add Extension".
- Query examples: "Show me some shoes," "Show me my orders," "Show me my cart."
