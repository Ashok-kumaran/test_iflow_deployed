import os
import asyncio
import httpx
from typing import Dict, Any
from json import JSONDecodeError
# from _util.token_gen import get_access_token
from _util.token_manager import TokenManager

API_BASE_URL = os.getenv("API_BASE_URL")

async def get_all_integration_package_tool() -> Dict[str, Any]:
    try:
        return await get_all_integration_package_tool_async()

    except Exception as e:
        print(f"""===> Exception in get_all_integration_package_tool function [Exception]: {e}""")
        raise 
    
    finally:
        pass

async def get_all_integration_package_tool_async() -> Dict[str, Any]:
    try:
        # access_token = await get_access_token()
        access_token = await TokenManager.get_token()
        url = (
            f"{API_BASE_URL}"
            f"/IntegrationPackages" 
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json" # "application/xml|json"
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=headers)

        response.raise_for_status()
        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            data = response.json()
            # print(type(data))
            return data
        else:
            data = response.text
            return data

    except httpx.HTTPStatusError as e:
        print(f"""===> Exception in get_all_integration_package_tool_async function [HTTPStatusError]: {e}
                       status code: {e.response.status_code}
                       response text: {e.response.text}""")
        raise 

    except httpx.RequestError as e:
        print(f"""===> Exception in get_all_integration_package_tool_async function [RequestError]: {e}""")
        raise 

    except JSONDecodeError as e:
        print(f"""===> Exception in get_all_integration_package_tool_async function [JSONDecodeError]: {e}""")
        raise 

    except KeyError as e:
        print(f"""===> Exception in get_all_integration_package_tool_async function [KeyError]: {e}""")
        raise 

    except Exception as e:
        print(f"""===> Exception in get_all_integration_package_tool_async function [Exception]: {e}""")
        raise 
    
    finally:
        pass

