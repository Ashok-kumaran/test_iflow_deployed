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

async def test_iflow_with_sample_payload_tool(integration_flow_id: str, version: str = "active") -> Dict[str, Any]:
    """
    Test an integration flow by generating and sending a sample payload.
    
    This tool:
    1. Gets the endpoint URL for the integration flow
    2. Analyzes the integration flow to understand its structure
    3. Generates a sample payload based on the flow structure
    4. Sends the payload to the endpoint and returns the response
    
    Args:
        integration_flow_id: Integration Flow ID
        version: 'active' or explicit version (e.g. 1.0.5)
    """
    try:
        return await test_iflow_with_sample_payload_tool_async(integration_flow_id, version)

    except Exception as e:
        print(f"""===> Exception in test_iflow_with_sample_payload_tool function [Exception]: {e}""")
        raise 
    
    finally:
        pass

async def test_iflow_with_sample_payload_tool_async(integration_flow_id: str, version: str = "active") -> Dict[str, Any]:
    """
    Test an integration flow by generating and sending a sample payload.
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
            
            # Step 2: Get the integration flow configuration to understand its structure
            config_url = (
                f"{API_BASE_URL}"
                f"/IntegrationDesigntimeArtifacts"
                f"(Id='{integration_flow_id}',Version='{version}')"
                f"/Configurations"
            )
            
            config_response = await client.get(config_url, headers=headers)
            config_response.raise_for_status()
            config_data = config_response.json()
            
            # Step 3: Generate sample payload based on the flow structure
            # Analyze the configuration to determine the expected payload format
            sample_payload = generate_sample_payload(config_data, integration_flow_id)
            
            # Step 4: Get CSRF token before sending the payload
            # First, make a HEAD request to get the CSRF token
            # Use CPI token for runtime calls
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
            
            # Step 5: Send the sample payload to the endpoint with CSRF token
            test_headers = {
                "Authorization": f"Bearer {cpi_access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-csrf-token": csrf_token
            }
            
            test_response = await client.post(
                test_url,
                headers=test_headers,
                json=sample_payload,
                timeout=30.0
            )
            
            # Get the response
            response_data = {
                "status_code": test_response.status_code,
                "headers": dict(test_response.headers),
                "body": None,
                "test_url": test_url,
                "integration_flow_id": integration_flow_id,
                "sample_payload": sample_payload
            }
            
            # Try to parse response body
            try:
                response_data["body"] = test_response.json()
            except:
                response_data["body"] = test_response.text
            
            return response_data

    except httpx.HTTPStatusError as e:
        print(f"""===> Exception in test_iflow_with_sample_payload_tool_async function [HTTPStatusError]: {e}
                       status code: {e.response.status_code}
                       response text: {e.response.text}""")
        raise 

    except httpx.RequestError as e:
        print(f"""===> Exception in test_iflow_with_sample_payload_tool_async function [RequestError]: {e}""")
        raise 

    except JSONDecodeError as e:
        print(f"""===> Exception in test_iflow_with_sample_payload_tool_async function [JSONDecodeError]: {e}""")
        raise 

    except KeyError as e:
        print(f"""===> Exception in test_iflow_with_sample_payload_tool_async function [KeyError]: {e}""")
        raise 

    except Exception as e:
        print(f"""===> Exception in test_iflow_with_sample_payload_tool_async function [Exception]: {e}""")
        raise 
    
    finally:
        pass


def generate_sample_payload(config_data: Dict[str, Any], integration_flow_id: str) -> Dict[str, Any]:
    """
    Generate a sample payload based on the integration flow configuration.
    
    This function analyzes the configuration to determine the expected payload format
    and generates a sample payload accordingly.
    """
    try:
        # Default sample payload
        sample_payload: Dict[str, Any] = {
            "message": f"Test message for integration flow: {integration_flow_id}",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": {
                "id": "12345",
                "name": "Test Data",
                "value": "Sample Value"
            }
        }
        
        # Analyze configuration to customize the payload
        if config_data and config_data.get("value"):
            configs = config_data["value"]
            
            # Look for configuration parameters that might indicate the expected format
            for config in configs:
                param_name = config.get("Name", "").lower()
                param_value = config.get("Value", "")
                
                # Check for common configuration patterns
                if "message" in param_name or "payload" in param_name:
                    # If there's a message type configuration, adjust the payload
                    if "xml" in str(param_value).lower():
                        sample_payload = {
                            "message": f"<message><id>12345</id><text>Test message for {integration_flow_id}</text></message>"
                        }
                    elif "json" in str(param_value).lower():
                        sample_payload = {
                            "message": f"Test message for {integration_flow_id}",
                            "id": "12345",
                            "timestamp": "2024-01-01T00:00:00Z"
                        }
                
                # Check for ID field configuration
                if "id" in param_name:
                    data_obj = sample_payload.get("data")
                    if isinstance(data_obj, dict):
                        data_obj["id"] = "TEST-12345"
                
                # Check for name field configuration
                if "name" in param_name:
                    data_obj = sample_payload.get("data")
                    if isinstance(data_obj, dict):
                        data_obj["name"] = "Test Data Item"
        
        return sample_payload
        
    except Exception as e:
        print(f"Error generating sample payload: {e}")
        # Return default payload on error
        return {
            "message": f"Test message for integration flow: {integration_flow_id}",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": {
                "id": "12345",
                "name": "Test Data",
                "value": "Sample Value"
            }
        }
