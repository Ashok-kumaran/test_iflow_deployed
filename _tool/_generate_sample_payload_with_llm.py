import os
import asyncio
import httpx
import json
import zipfile
import io
from typing import Dict, Any, Union, List
from json import JSONDecodeError
from dotenv import load_dotenv
from _util.token_manager import TokenManager, CPITokenManager

load_dotenv()
API_BASE_URL: str = os.getenv("API_BASE_URL", "")


async def generate_sample_payload_with_llm(integration_flow_id: str, version: str = "active") -> Dict[str, Any]:
    """
    Generate a sample payload for an integration flow using LLM analysis.
    
    This tool:
    1. Gets the endpoint URL for the integration flow
    2. Downloads the integration flow zip file
    3. Analyzes the flow structure (adapter type, schemas, etc.)
    4. Uses LLM to generate an appropriate sample payload based on the analysis
    5. Sends the payload to the endpoint and returns the response
    
    Args:
        integration_flow_id: Integration Flow ID
        version: 'active' or explicit version (e.g. 1.0.5)
    """
    try:
        return await generate_sample_payload_with_llm_async(integration_flow_id, version)

    except Exception as e:
        print(f"""===> Exception in generate_sample_payload_with_llm function [Exception]: {e}""")
        raise


async def generate_sample_payload_with_llm_async(integration_flow_id: str, version: str = "active") -> Dict[str, Any]:
    """
    Generate a sample payload for an integration flow using LLM analysis.
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
            
            # Step 2: Get the integration flow configuration
            config_url = (
                f"{API_BASE_URL}"
                f"/IntegrationDesigntimeArtifacts"
                f"(Id='{integration_flow_id}',Version='{version}')"
                f"/Configurations"
            )
            
            config_response = await client.get(config_url, headers=headers)
            config_response.raise_for_status()
            config_data = config_response.json()
            
            # Step 3: Download the integration flow zip file
            zip_url = (
                f"{API_BASE_URL}"
                f"/IntegrationDesigntimeArtifacts"
                f"(Id='{integration_flow_id}',Version='{version}')/$value"
            )
            
            zip_response = await client.get(
                zip_url,
                headers={**headers, "Accept": "application/zip"},
                timeout=30.0
            )
            zip_response.raise_for_status()
            
            # Extract and analyze the zip file
            zip_bytes = zip_response.content
            flow_analysis = await analyze_integration_flow_zip(zip_bytes, integration_flow_id)
            
            # Step 4: Generate sample payload using LLM
            sample_payload = await generate_payload_with_llm(
                integration_flow_id=integration_flow_id,
                config_data=config_data,
                flow_analysis=flow_analysis
            )
            
            # Step 5: Get CSRF token before sending the payload
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
            
            # Step 6: Send the sample payload to the endpoint with CSRF token
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
                "sample_payload": sample_payload,
                "flow_analysis": flow_analysis
            }
            
            # Try to parse response body
            try:
                response_data["body"] = test_response.json()
            except:
                response_data["body"] = test_response.text
            
            return response_data

    except httpx.HTTPStatusError as e:
        print(f"""===> Exception in generate_sample_payload_with_llm_async function [HTTPStatusError]: {e}
                       status code: {e.response.status_code}
                       response text: {e.response.text}""")
        raise

    except httpx.RequestError as e:
        print(f"""===> Exception in generate_sample_payload_with_llm_async function [RequestError]: {e}""")
        raise

    except JSONDecodeError as e:
        print(f"""===> Exception in generate_sample_payload_with_llm_async function [JSONDecodeError]: {e}""")
        raise

    except KeyError as e:
        print(f"""===> Exception in generate_sample_payload_with_llm_async function [KeyError]: {e}""")
        raise

    except Exception as e:
        print(f"""===> Exception in generate_sample_payload_with_llm_async function [Exception]: {e}""")
        raise


async def analyze_integration_flow_zip(zip_bytes: bytes, integration_flow_id: str) -> Dict[str, Any]:
    """
    Analyze the integration flow zip file to extract structure and metadata.
    
    Returns a dictionary containing:
    - adapter_type: The type of adapter (SOAP, REST, IDoc, SFTP, etc.)
    - has_xml_schema: Whether XML schemas are present
    - has_json_schema: Whether JSON schemas are present
    - has_wSDL: Whether WSDL files are present
    - has_openAPI: Whether OpenAPI/Swagger files are present
    - file_structure: List of important files in the flow
    - configuration_hints: Hints from configuration files
    """
    analysis = {
        "adapter_type": "unknown",
        "has_xml_schema": False,
        "has_json_schema": False,
        "has_wSDL": False,
        "has_openAPI": False,
        "file_structure": [],
        "configuration_hints": [],
        "xml_schemas": [],
        "json_schemas": [],
        "wSDL_content": None,
        "openAPI_content": None
    }
    
    try:
        # Extract zip file
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            # Analyze file structure
            for file_path in file_list:
                analysis["file_structure"].append(file_path)
                
                # Check for adapter type indicators
                lower_path = file_path.lower()
                
                # SOAP adapter indicators
                if lower_path.endswith('.wsdl') or 'soap' in lower_path:
                    analysis["adapter_type"] = "SOAP"
                    analysis["has_wSDL"] = True
                    
                    # Try to extract WSDL content
                    try:
                        with zip_ref.open(file_path) as file:
                            analysis["wSDL_content"] = file.read().decode('utf-8', errors='ignore')[:5000]  # First 5KB
                    except:
                        pass
                
                # REST adapter indicators
                elif lower_path.endswith(('.json', '.yaml', '.yml')) and ('openapi' in lower_path or 'swagger' in lower_path):
                    analysis["adapter_type"] = "REST"
                    analysis["has_openAPI"] = True
                    
                    # Try to extract OpenAPI content
                    try:
                        with zip_ref.open(file_path) as file:
                            content = file.read().decode('utf-8', errors='ignore')
                            analysis["openAPI_content"] = content[:5000]  # First 5KB
                    except:
                        pass
                
                # IDoc adapter indicators
                elif 'idoc' in lower_path or lower_path.endswith('.xsd') and 'idoc' in lower_path:
                    analysis["adapter_type"] = "IDoc"
                    analysis["has_xml_schema"] = True
                    
                    # Try to extract XSD content
                    try:
                        with zip_ref.open(file_path) as file:
                            content = file.read().decode('utf-8', errors='ignore')
                            analysis["xml_schemas"].append(content[:3000])  # First 3KB
                    except:
                        pass
                
                # SFTP/FTP adapter indicators
                elif 'sftp' in lower_path or 'ftp' in lower_path or 'file' in lower_path:
                    analysis["adapter_type"] = "File"
                
                # JMS adapter indicators
                elif 'jms' in lower_path or 'queue' in lower_path or 'topic' in lower_path:
                    analysis["adapter_type"] = "JMS"
                
                # RFC adapter indicators
                elif 'rfc' in lower_path or 'bapi' in lower_path:
                    analysis["adapter_type"] = "RFC"
                
                # Generic XML schema
                elif lower_path.endswith('.xsd'):
                    analysis["has_xml_schema"] = True
                    try:
                        with zip_ref.open(file_path) as file:
                            content = file.read().decode('utf-8', errors='ignore')
                            analysis["xml_schemas"].append(content[:3000])
                    except:
                        pass
                
                # Generic JSON schema
                elif lower_path.endswith('.json') and 'schema' in lower_path:
                    analysis["has_json_schema"] = True
                    try:
                        with zip_ref.open(file_path) as file:
                            content = file.read().decode('utf-8', errors='ignore')
                            analysis["json_schemas"].append(content[:3000])
                    except:
                        pass
                
                # Configuration files
                elif lower_path.endswith('.properties') or lower_path.endswith('.cfg') or 'config' in lower_path:
                    try:
                        with zip_ref.open(file_path) as file:
                            content = file.read().decode('utf-8', errors='ignore')
                            analysis["configuration_hints"].append(content[:2000])
                    except:
                        pass
            
            # If adapter type is still unknown, try to infer from file patterns
            if analysis["adapter_type"] == "unknown":
                if analysis["has_wSDL"]:
                    analysis["adapter_type"] = "SOAP"
                elif analysis["has_openAPI"]:
                    analysis["adapter_type"] = "REST"
                elif analysis["has_xml_schema"] and any('idoc' in f.lower() for f in file_list):
                    analysis["adapter_type"] = "IDoc"
                elif any('sftp' in f.lower() or 'ftp' in f.lower() or 'file' in f.lower() for f in file_list):
                    analysis["adapter_type"] = "File"
                elif any('jms' in f.lower() or 'queue' in f.lower() or 'topic' in f.lower() for f in file_list):
                    analysis["adapter_type"] = "JMS"
                elif any('rfc' in f.lower() or 'bapi' in f.lower() for f in file_list):
                    analysis["adapter_type"] = "RFC"
                elif analysis["has_json_schema"]:
                    analysis["adapter_type"] = "REST"
                elif analysis["has_xml_schema"]:
                    analysis["adapter_type"] = "SOAP"
            
            return analysis
            
    except Exception as e:
        print(f"Error analyzing integration flow zip: {e}")
        return analysis


async def generate_payload_with_llm(
    integration_flow_id: str,
    config_data: Dict[str, Any],
    flow_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a sample payload using LLM analysis.
    
    This function creates a detailed prompt for the LLM to generate an appropriate
    sample payload based on the integration flow configuration and analysis.
    """
    
    # Build a comprehensive prompt for the LLM
    prompt = f"""
You are an expert in SAP Cloud Platform Integration (CPI) and integration flow testing. 
Your task is to generate a sample payload for testing an integration flow.

**Integration Flow Details:**
- Integration Flow ID: {integration_flow_id}
- Adapter Type: {flow_analysis.get('adapter_type', 'unknown')}
- Has WSDL: {flow_analysis.get('has_wSDL', False)}
- Has OpenAPI: {flow_analysis.get('has_openAPI', False)}
- Has XML Schema: {flow_analysis.get('has_xml_schema', False)}
- Has JSON Schema: {flow_analysis.get('has_json_schema', False)}

**Configuration Parameters:**
{json.dumps(config_data.get('value', []), indent=2) if config_data.get('value') else 'No configuration parameters found'}

**File Structure Analysis:**
{json.dumps(flow_analysis.get('file_structure', []), indent=2)}

**Additional Analysis:**
{json.dumps({k: v for k, v in flow_analysis.items() if k not in ['file_structure', 'xml_schemas', 'json_schemas', 'wSDL_content', 'openAPI_content']}, indent=2)}

**Instructions:**
1. Analyze the adapter type and configuration to determine the expected payload format
2. Generate a sample payload that matches the integration flow's requirements
3. For SOAP/XML adapters, generate valid XML
4. For REST/JSON adapters, generate valid JSON
5. For IDoc adapters, generate valid IDoc XML structure
6. For File adapters, generate appropriate file content
7. For JMS adapters, generate appropriate message structure
8. For RFC adapters, generate appropriate RFC structure
9. The payload should be realistic and testable
10. Return ONLY the JSON payload (no additional text or explanation)

**Expected Output Format:**
Return a JSON object that represents the sample payload. For example:
- For JSON-based flows: {{"field1": "value1", "field2": "value2"}}
- For XML-based flows: Return as a string or structured object

**Important:** Do not include any explanatory text. Return ONLY the payload.
"""

    # In a real implementation, you would call an LLM API here
    # For now, we'll generate a smart default based on the analysis
    
    # Smart default generation based on analysis
    adapter_type = flow_analysis.get('adapter_type', 'unknown')
    
    if adapter_type == 'SOAP':
        # Generate XML payload for SOAP
        return {
            "message": f"<soap:Envelope xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/'><soap:Body><TestMessage><id>12345</id><text>Test message for {integration_flow_id}</text></TestMessage></soap:Body></soap:Envelope>"
        }
    
    elif adapter_type == 'REST':
        # Generate JSON payload for REST
        return {
            "id": "12345",
            "message": f"Test message for {integration_flow_id}",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": {
                "testField": "Sample Value",
                "status": "active"
            }
        }
    
    elif adapter_type == 'IDoc':
        # Generate IDoc XML payload
        return {
            "message": f"<?xml version='1.0'?><IDOC><E1EDK03><MSGFN>004</MSGFN><DOCNUM>12345</DOCNUM><TEST>Test IDoc for {integration_flow_id}</TEST></E1EDK03></IDOC>"
        }
    
    elif adapter_type == 'File':
        # Generate file content
        return {
            "message": f"Test file content for {integration_flow_id}\nLine 1: Test data\nLine 2: More test data\n"
        }
    
    elif adapter_type == 'JMS':
        # Generate JMS message
        return {
            "message": f"Test JMS message for {integration_flow_id}",
            "properties": {
                "messageId": "12345",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            "body": {
                "data": "Sample payload"
            }
        }
    
    elif adapter_type == 'RFC':
        # Generate RFC structure
        return {
            "message": f"Test RFC call for {integration_flow_id}",
            "function": "TEST_FUNCTION",
            "parameters": {
                "IMPORTING": {"PARAM1": "value1"},
                "EXPORTING": {"PARAM2": "value2"}
            }
        }
    
    else:
        # Generic JSON payload
        return {
            "message": f"Test message for integration flow: {integration_flow_id}",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": {
                "id": "12345",
                "name": "Test Data",
                "value": "Sample Value"
            }
        }
