from fastmcp import FastMCP
from typing import Dict, Any

from _tool._get_an_integration_package_tool import get_an_integration_package_tool
from _tool._get_all_integration_package_tool import get_all_integration_package_tool
from _tool._get_an_integration_flow_zip_tool import get_an_integration_flow_zip_tool
from _tool._get_an_endpoint_of_an_integration_flow_tool import get_an_endpoint_of_an_integration_flow_tool
from _tool._get_configration_of_an_intergrairon_flow_tool import get_configration_of_an_intergrairon_flow_tool
from _tool._get_endpoint_url_by_id_tool import get_endpoint_url_by_id_tool
from _tool._test_iflow_with_sample_payload_tool import test_iflow_with_sample_payload_tool
from _tool._generate_sample_payload_with_llm import generate_sample_payload_with_llm
from _tool._test_iflow_with_user_payload_tool import test_iflow_with_user_payload_tool

mcp = FastMCP("iflow_test_mcp_server")
#Tool 1
@mcp.tool(name="get_integration_package_by_id", description="Fetch an SAP CPI Integration Package by its ID.")
async def get_an_integration_package(integration_package_id: str):
    """
    Args:
        integration_package_id: Integration Package ID (example: "MyPackage")
    """
    try:
        results = await get_an_integration_package_tool(integration_package_id)
        return results
    
    except Exception as e:
        print(f"===> Exception in get_an_integration_package function: {e}")
        raise
        
    finally:
        pass     

#Tool 2 
@mcp.tool(name="get_all_integration_packages",  description="List all SAP CPI Integration Packages.")
async def get_all_integration_package():
    """ Returns all integration packages available in the tenant. """
    try:
        results = await get_all_integration_package_tool()
        return results
    
    except Exception as e:
        print(f"===> Exception in get_all_integration_package function: {e}")
        raise
        
    finally:
        pass     

#Tool 3
@mcp.tool(name="get_an_iflow_zip",  description="Download an SAP CPI Integration Flow as a ZIP file.")
async def get_an_integration_flow_zip(integration_flow_id: str, version: str = "active"):
    """
    Notes:
        Integration flows of configure-only packages cannot be downloaded.

    Args:
        integration_flow_id: Integration Flow ID
        version: "active" or an explicit version (example: "1.0.5")
    """
    try:
        results = await get_an_integration_flow_zip_tool(integration_flow_id, version)
        # print(type(results))
        return results
    
    except Exception as e:
        print(f"===> Exception in get_an_integration_flow_zip function: {e}")
        raise
        
    finally:
        pass     

#Tool 4
@mcp.tool(name="get_all_endpoint_of_an_integration_flow", 
description="List all endpoints exposed by deployed SAP CPI integration flows.")
async def get_an_endpoint_of_an_integration_flow():
    """ Returns endpoints for deployed integration flows. """
    try:
        results = await get_an_endpoint_of_an_integration_flow_tool()
        return results
   
    except Exception as e:
        print(f"===> Exception in get_an_endpoint_of_an_integration_flow function: {e}")
        raise
       
    finally:
        pass
   
#Tool 5
@mcp.tool(name="get_configration_of_an_intergrairon_flow", 
description="Get configuration parameters (key/value pairs) of an SAP CPI integration flow.")
async def get_configration_of_an_intergrairon_flow(integration_flow_id: str, version: str = "active"):
    """
    Args:
        integration_flow_id: Integration Flow ID
        version: "active" or an explicit version (example: "1.0.5")
    """
    try:
        results = await get_configration_of_an_intergrairon_flow_tool(integration_flow_id, version)
        return results
    
    except Exception as e:
        print(f"===> Exception in get_configration_of_an_intergrairon_flow function: {e}")
        raise
        
    finally:
        pass

#Tool 6
@mcp.tool(name="get_endpoint_url_by_id", 
          description="Get the endpoint URL of a deployed SAP CPI integration flow by ID.")
async def get_endpoint_url_by_id(integration_flow_id: str):
    """
    Args:
        integration_flow_id: Integration Flow ID
    """
    try:
        results = await get_endpoint_url_by_id_tool(integration_flow_id)
        return results
    
    except Exception as e:
        print(f"===> Exception in get_endpoint_url_by_id function: {e}")
        raise
        
    finally:
        pass

#Tool 7
@mcp.tool(name="test_iflow_with_sample_payload", description="Generate a sample payload and test an SAP CPI integration flow endpoint.")
async def test_iflow_with_sample_payload(integration_flow_id: str, version: str = "active"):
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
        results = await test_iflow_with_sample_payload_tool(integration_flow_id, version)
        return results
    
    except Exception as e:
        print(f"===> Exception in test_iflow_with_sample_payload function: {e}")
        raise
        
    finally:
        pass

#Tool 8
@mcp.tool(name="test_iflow_with_user_payload", 
description="Send a user-provided payload to an SAP CPI integration flow endpoint and return the response.")
async def test_iflow_with_user_payload_tool_wrapper(integration_flow_id: str, user_payload: Dict[str, Any], version: str = "active"):
    """
    Test an integration flow by sending a user-provided sample payload.
    
    This tool:
    1. Gets the endpoint URL for the integration flow
    2. Sends the user-provided payload to the endpoint
    3. Returns the response
    
    Args:
        integration_flow_id: Integration Flow ID
        user_payload: User-provided payload to test (JSON object)
        version: 'active' or explicit version (e.g. 1.0.5)
    """
    try:
        results = await test_iflow_with_user_payload_tool(integration_flow_id, user_payload, version)
        return results
    
    except Exception as e:
        print(f"===> Exception in test_iflow_with_user_payload function: {e}")
        raise
        
    finally:
        pass

#Tool 9
@mcp.tool(name="generate_sample_payload", description="Use realistic sample payload for an SAP CPI iFlow.")
async def generate_sample_payload_with_llm_tool(integration_flow_id: str, version: str = "active"):
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
        results = await generate_sample_payload_with_llm(integration_flow_id, version)
        return results
    
    except Exception as e:
        print(f"===> Exception in generate_sample_payload_with_llm_tool function: {e}")
        raise
        
    finally:
        pass