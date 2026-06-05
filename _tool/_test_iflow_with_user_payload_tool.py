import os
import asyncio
import httpx
import json
from typing import Dict, Any, Union
from json import JSONDecodeError
from dotenv import load_dotenv
from _util.token_manager import TokenManager, CPITokenManager

load_dotenv()
API_BASE_URL: str = os.getenv("API_BASE_URL", "")


async def test_iflow_with_user_payload_tool(
    integration_flow_id: str, 
    user_payload: Dict[str, Any],
    version: str = "active"
) -> Dict[str, Any]:
    """
    Test an integration flow by sending a user-provided sample payload.
    
    This tool:
    1. Gets the endpoint URL for the integration flow
    2. Sends the user-provided payload to the endpoint
    3. Returns the response
    
    Args:
        integration_flow_id: Integration Flow ID
        user_payload: User-provided payload to test
        version: 'active' or explicit version (e.g. 1.0.5)
    """
    try:
        return await test_iflow_with_user_payload_tool_async(integration_flow_id, user_payload, version)

    except Exception as e:
        print(f"""===> Exception in test_iflow_with_user_payload_tool function [Exception]: {e}""")
        raise 


async def test_iflow_with_user_payload_tool_async(
    integration_flow_id: str, 
    user_payload: Dict[str, Any],
    version: str = "active"
) -> Dict[str, Any]:
    """
    Test an integration flow by sending a user-provided sample payload.
    """
    try:
        # Step 1: Get the endpoint URL for the integration flow
        access_token = await TokenManager.get_token()
        
        # Get endpoint URL with EntryPoints expanded
        endpoint_url = (
            f"{API_BASE_URL}"
            f"/ServiceEndpoints"
            f"?$filter=Name eq '{integration_flow_id}'"
            f"&$expand=EntryPoints"
        )
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            # Get endpoint information
            endpoint_response = await client.get(endpoint_url, headers=headers)
            endpoint_response.raise_for_status()
            endpoint_data = endpoint_response.json()
            
            # Check if endpoint data exists (handle both OData formats)
            results = endpoint_data.get("d", {}).get("results", [])
            if not results:
                return {
                    "error": f"No endpoint found for integration flow: {integration_flow_id}",
                    "integration_flow_id": integration_flow_id
                }
            
            # Get the first endpoint
            endpoint = results[0]

            # Check if EntryPoints are expanded
            entry_points = endpoint.get("EntryPoints", {})
            entry_results = entry_points.get("results", [])

            if not entry_results:
                return {
                    "error": f"No entry points found for integration flow: {integration_flow_id}",
                    "endpoint": endpoint
                }

            # Get the first entry point URL
            first_entry_point = entry_results[0]
            test_url = first_entry_point.get("Url", "")

            if not test_url:
                return {
                    "error": f"No URL found in entry point for integration flow: {integration_flow_id}",
                    "entry_point": first_entry_point
                }
            
            # Step 2: Get CSRF token before sending the payload
            cpi_access_token = await CPITokenManager.get_token()
            csrf_headers = {
                "Authorization": f"Bearer {cpi_access_token}",
                "x-csrf-token": "Fetch"
            }
            
            csrf_response = await client.head(
                test_url,
                headers=csrf_headers,
                timeout=30.0
            )
            
            csrf_token = csrf_response.headers.get("x-csrf-token", "")
            
            # Step 3: Send the user-provided payload to the endpoint with CSRF token
            test_headers = {
                "Authorization": f"Bearer {cpi_access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-csrf-token": csrf_token
            }
            
            test_response = await client.post(
                test_url,
                headers=test_headers,
                json=user_payload,
                timeout=30.0
            )
            
            # Get the response
            response_data = {
                "status_code": test_response.status_code,
                "headers": dict(test_response.headers),
                "body": None,
                "test_url": test_url,
                "integration_flow_id": integration_flow_id,
                "user_payload": user_payload
            }
            
            # Try to parse response body
            try:
                response_data["body"] = test_response.json()
            except:
                response_data["body"] = test_response.text
            
            return response_data

    except httpx.HTTPStatusError as e:
        print(f"""===> Exception in test_iflow_with_user_payload_tool_async function [HTTPStatusError]: {e}
                       status code: {e.response.status_code}
                       response text: {e.response.text}""")
        raise 

    except httpx.RequestError as e:
        print(f"""===> Exception in test_iflow_with_user_payload_tool_async function [RequestError]: {e}""")
        raise 

    except JSONDecodeError as e:
        print(f"""===> Exception in test_iflow_with_user_payload_tool_async function [JSONDecodeError]: {e}""")
        raise 

    except KeyError as e:
        print(f"""===> Exception in test_iflow_with_user_payload_tool_async function [KeyError]: {e}""")
        raise 

    except Exception as e:
        print(f"""===> Exception in test_iflow_with_user_payload_tool_async function [Exception]: {e}""")
        raise
