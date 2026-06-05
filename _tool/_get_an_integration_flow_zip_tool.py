import os
import asyncio
import httpx
from typing import Dict, Any
from json import JSONDecodeError
# from _util.token_gen import get_access_token
from _util.token_manager import TokenManager
from _util.int_suite_service import i_flow_path
from _util.file_ops import write_zip_file

API_BASE_URL = os.getenv("API_BASE_URL")

async def get_an_integration_flow_zip_tool(integration_flow_id: str, version: str = "active") -> Dict[str, Any]:
    try:
        return await get_an_integration_flow_zip_tool_async(integration_flow_id, version)

    except Exception as e:
        print(f"""===> Exception in get_an_integration_flow_zip_tool function [Exception]: {e}""")
        raise 
    
    finally:
        pass

async def get_an_integration_flow_zip_tool_async(integration_flow_id: str, version: str = "active") -> Dict[str, Any]:
    try:
        # access_token = await get_access_token()
        access_token = await TokenManager.get_token()
        url = (
            f"{API_BASE_URL}"
            f"/IntegrationDesigntimeArtifacts"
            f"(Id='{integration_flow_id}',Version='{version}')/$value"
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/zip" # "application/xml|json|zip"
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=headers)

        response.raise_for_status()
        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            data = response.json()
            # print(type(data))
            return data
        
        elif "application/zip" in content_type:
            zip_bytes = response.content
            path = i_flow_path(integration_flow_id)
            write_zip_file(path, zip_bytes)
            data = response.text
            # print(type(data))
            return data
        
        else:
            data = response.text
            return data

    except httpx.HTTPStatusError as e:
        print(f"""===> Exception in get_an_integration_flow_zip_tool_async function [HTTPStatusError]: {e}
                       status code: {e.response.status_code}
                       response text: {e.response.text}""")
        raise 

    except httpx.RequestError as e:
        print(f"""===> Exception in get_an_integration_flow_zip_tool_async function [RequestError]: {e}""")
        raise 

    except JSONDecodeError as e:
        print(f"""===> Exception in get_an_integration_flow_zip_tool_async function [JSONDecodeError]: {e}""")
        raise 

    except KeyError as e:
        print(f"""===> Exception in get_an_integration_flow_zip_tool_async function [KeyError]: {e}""")
        raise 

    except Exception as e:
        print(f"""===> Exception in get_an_integration_flow_zip_tool_async function [Exception]: {e}""")
        raise 
    
    finally:
        pass

