import os
from server_tools import mcp
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port
    )
