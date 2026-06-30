# iFlow Test MCP Server

An MCP (Model Context Protocol) server built with [FastMCP](https://github.com/jlowin/fastmcp) that exposes tools for testing and inspecting SAP Cloud Platform Integration (CPI) integration flows (iFlows). It enables AI agents and MCP-compatible clients to interact with SAP CPI design-time and runtime APIs.

## Tools

| Tool | Description |
|------|-------------|
| `get_integration_package_by_id` | Fetch an SAP CPI Integration Package by its ID |
| `get_all_integration_packages` | List all integration packages in the tenant |
| `get_an_iflow_zip` | Download an iFlow as a ZIP archive |
| `get_all_endpoint_of_an_integration_flow` | List all endpoints exposed by deployed iFlows |
| `get_configration_of_an_intergrairon_flow` | Get configuration key/value pairs of an iFlow |
| `get_endpoint_url_by_id` | Get the runtime endpoint URL of an iFlow by ID |
| `test_iflow_with_sample_payload` | Auto-generate a sample payload and test an iFlow endpoint |
| `test_iflow_with_user_payload` | Send a user-provided payload to an iFlow endpoint |
| `generate_sample_payload` | Analyze an iFlow and generate a realistic test payload via LLM |
| `create_wbs` | Create a WBS element in SAP via the CPI iFlow endpoint (auto-generates a unique ProjectExternalID) |
| `create_maintenance_order` | Create a Maintenance Order in SAP via the CPI iFlow endpoint using a fixed standard payload |
| `download-iflow` | Download and extract iFlow ZIP, returning its structure and metadata |
| `get-iflow-endpoint` | Resolve the runtime endpoint URL via OData API |
| `get-iflow-configuration` | Retrieve iFlow configuration parameters |
| `test-iflow-with-payload` | Send an HTTP request to a CPI iFlow endpoint (supports OAuth, Basic Auth, CSRF) |
| `generate-sample-payload-with-llm` | Analyze iFlow structure and return LLM instructions for payload generation |
| `get-message-logs` | Fetch message processing error/log details by message ID |

## Architecture

```
main.py                  # Entry point — starts FastMCP HTTP server
mcp_tools.py             # Lightweight MCP tool wrappers (async)
server_tools.py          # Core tool implementations with auth/CSRF logic
_tool/                   # Per-tool implementation modules
_util/                   # Shared utility helpers
```

### Authentication

Two separate OAuth2 credential sets are used:

- **Design-time API** (`API_*`): OData APIs for package/iFlow metadata, ZIP downloads, configurations, and message logs.
- **Runtime** (`CPI_*`): Calling deployed iFlow HTTP endpoints. Supports OAuth2 client credentials, HTTP Basic Auth, or `auto` mode (tries OAuth first, falls back to Basic).

CSRF tokens are fetched automatically for `POST`, `PUT`, and `DELETE` requests. Token refresh and retry on `401`/`403` are handled transparently.

## Requirements

- Python >= 3.13
- Dependencies: `fastmcp`, `fastapi`, `langchain`, `sap-ai-sdk-gen`, `httpx`, `requests`, `python-dotenv`

Install with [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

Or with pip:

```bash
pip install -r requirements.txt
```

## Configuration

Copy or set the following environment variables (or use a `.env` file):

```env
# SAP CPI Design-time API (OData)
API_BASE_URL=
API_OAUTH_CLIENT_ID=
API_OAUTH_CLIENT_SECRET=
API_OAUTH_TOKEN_URL=

# SAP CPI Runtime
CPI_BASE_URL=
CPI_OAUTH_CLIENT_ID=
CPI_OAUTH_CLIENT_SECRET=
CPI_OAUTH_TOKEN_URL=

# CPI HTTP Basic Auth (alternative to OAuth)
CPI_BASIC_AUTH_USERNAME=
CPI_BASIC_AUTH_PASSWORD=
CPI_AUTH_METHOD=oauth   # oauth | basic | auto

# SAP AI Core (for LLM-based payload generation)
AICORE_AUTH_URL=
AICORE_CLIENT_ID=
AICORE_CLIENT_SECRET=
AICORE_RESOURCE_GROUP=default
AICORE_BASE_URL=
LLM_DEPLOYMENT_ID=
```

## Running Locally

```bash
python main.py
```

The server starts on `http://0.0.0.0:8080` by default. Override with the `PORT` environment variable.

## Deployment

The project includes a Cloud Foundry `manifest.yaml` for deployment to SAP BTP:

```bash
cf push
```

The `Procfile` is also included for platforms that use it:

```
web: python main.py
```
