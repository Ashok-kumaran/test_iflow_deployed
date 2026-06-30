"""
SAP CPI iFlow Testing MCP Server

This FastMCP server provides tools to:
1. Download and analyze SAP CPI iFlows
2. Use LLM to generate appropriate sample payloads
3. Test iFlows with generated payloads
4. Validate iFlow functionality and safety
"""

import os
import io
import json
import logging
import random
import zipfile
import requests
import xml.etree.ElementTree as ET

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastmcp import FastMCP
from _tool._get_an_integration_package_tool import get_an_integration_package_tool
from _tool._get_all_integration_package_tool import get_all_integration_package_tool

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass  # If dotenv not available or .env doesn't exist, use environment variables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("mcp_tools")


def _log_call(tool: str, **kwargs) -> None:
    parts = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
    logger.info("[CALL] %s | %s", tool, parts)


def _log_response(tool: str, result: Any) -> None:
    summary = repr(result)
    if len(summary) > 600:
        summary = summary[:600] + "..."
    logger.info("[RESPONSE] %s | %s", tool, summary)


def _log_error(tool: str, exc: Exception) -> None:
    logger.error("[ERROR] %s | %s: %s", tool, type(exc).__name__, exc)


# Initialize FastMCP server
mcp = FastMCP("SAP CPI iFlow Test Tools")

# Environment variables for SAP CPI credentials
API_BASE_URL = os.getenv("API_BASE_URL")
API_OAUTH_CLIENT_ID = os.getenv("API_OAUTH_CLIENT_ID")
API_OAUTH_CLIENT_SECRET = os.getenv("API_OAUTH_CLIENT_SECRET")
API_OAUTH_TOKEN_URL = os.getenv("API_OAUTH_TOKEN_URL")

CPI_BASE_URL = os.getenv("CPI_BASE_URL")
CPI_OAUTH_CLIENT_ID = os.getenv("CPI_OAUTH_CLIENT_ID")
CPI_OAUTH_CLIENT_SECRET = os.getenv("CPI_OAUTH_CLIENT_SECRET")
CPI_OAUTH_TOKEN_URL = os.getenv("CPI_OAUTH_TOKEN_URL")
# HTTP Basic Auth for runtime endpoints (alternative to OAuth)
CPI_BASIC_AUTH_USERNAME = os.getenv("CPI_BASIC_AUTH_USERNAME")
CPI_BASIC_AUTH_PASSWORD = os.getenv("CPI_BASIC_AUTH_PASSWORD")
CPI_AUTH_METHOD = os.getenv("CPI_AUTH_METHOD", "oauth")  # 'oauth', 'basic', or 'auto'


class OAuth2TokenManager:
    """Manages OAuth2 tokens for SAP CPI API authentication with expiry tracking"""
    
    def __init__(self, client_id: Optional[str], client_secret: Optional[str], token_url: Optional[str]):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self._token = None
        self._token_expiry = None
        self._expiry_buffer = timedelta(minutes=5)  # Refresh 5 minutes before actual expiry

    def is_configured(self) -> bool:
        return all([self.client_id, self.client_secret, self.token_url])
    
    def get_token(self) -> str:
        """Get a valid OAuth2 access token, refreshing if expired"""
        if not self.is_configured():
            raise ValueError("OAuth configuration is missing for token retrieval")
        if self._token is None or self._is_token_expired():
            self._token, self._token_expiry = self._fetch_token()
        return self._token
    
    def _is_token_expired(self) -> bool:
        """Check if token is expired or will expire soon"""
        if self._token_expiry is None:
            return True
        return datetime.now() >= self._token_expiry
    
    def _fetch_token(self) -> tuple[str, datetime]:
        """Fetch a new access token from the OAuth2 endpoint"""
        if not self.is_configured():
            raise ValueError("OAuth configuration is missing for token fetch")
        # Type narrowing: after is_configured() check, these are guaranteed to be str
        token_url = self.token_url or ""
        client_id = self.client_id or ""
        client_secret = self.client_secret or ""
        
        response = requests.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        token_data = response.json()
        token = token_data["access_token"]
        
        # Calculate expiry time (default to 3600 seconds if not provided)
        expires_in = token_data.get("expires_in", 3600)
        expiry_time = datetime.now() + timedelta(seconds=expires_in) - self._expiry_buffer
        
        return token, expiry_time
    
    def refresh_token(self):
        """Force refresh the access token"""
        if not self.is_configured():
            raise ValueError("OAuth configuration is missing for token refresh")
        self._token, self._token_expiry = self._fetch_token()


class CSRFTokenManager:
    """
    Manages CSRF tokens for SAP CPI API authentication.
    Fetches fresh token from base CPI URL for each request.
    CSRF tokens are REQUIRED when using Basic Auth, OPTIONAL for OAuth.
    """
    
    def __init__(self):
        self._failure_cache = set()  # Track (url, auth_method) where CSRF fetch has failed
    
    def get_token(self, session: requests.Session, endpoint_url: str, headers: Dict[str, str], auth_method: str = "oauth") -> Optional[str]:
        """
        Fetch a fresh CSRF token from the deployed iFlow endpoint.
        
        Args:
            session: requests.Session object for making requests
            endpoint_url: The actual endpoint URL where the request will be sent
            headers: Base headers to use in the request
            auth_method: Authentication method ("oauth" or "basic")
        
        Returns:
            CSRF token string if available, None if not available
        """
        # Don't keep retrying URLs where CSRF fetch has failed
        cache_key = (endpoint_url, auth_method.lower())
        if cache_key in self._failure_cache:
            return None

        # Always fetch a fresh token for each request (no caching)
        token = self._fetch_token_safe(session, endpoint_url, headers, auth_method)

        if token:
            # Remove from failure cache if we successfully got a token
            self._failure_cache.discard(cache_key)
            return token
        else:
            # Mark this URL as having failed CSRF fetch
            self._failure_cache.add(cache_key)
            return None
    
    def _fetch_token_safe(self, session: requests.Session, url: str, headers: Dict[str, str], auth_method: str = "oauth") -> Optional[str]:
        """
        Safely attempt to fetch CSRF token without raising exceptions.
        Returns None if fetch fails for any reason (which is acceptable).
        
        Args:
            session: requests.Session object
            url: URL endpoint to fetch token from
            headers: Base headers to include
            auth_method: Authentication method ("oauth" or "basic")
        
        Returns:
            CSRF token if successful, None otherwise
        """
        try:
            csrf_headers = dict(headers)
            csrf_headers["X-CSRF-Token"] = "Fetch"
            
            # For Basic Auth, include Basic Auth credentials in the CSRF fetch request
            auth: Optional[tuple[str, str]] = None
            if auth_method.lower() == "basic" and CPI_BASIC_AUTH_USERNAME and CPI_BASIC_AUTH_PASSWORD:
                auth = (CPI_BASIC_AUTH_USERNAME, CPI_BASIC_AUTH_PASSWORD)
                # Remove OAuth token if present, will use Basic Auth instead
                csrf_headers.pop("Authorization", None)
            
            # Try simple GET with short timeout
            response = session.get(url, headers=csrf_headers, auth=auth, timeout=10)
            
            # Accept 200, 404, and 405 (some endpoints return 404/405 but still provide token)
            if response.status_code in (200, 401, 403, 404, 405):
                token = (
                    response.headers.get("X-CSRF-Token") or 
                    response.headers.get("x-csrf-token") or
                    response.headers.get("X-Csrf-Token")
                )
                
                if token and token.lower() not in ("required", "fetch", ""):
                    return token
        except Exception:
            # Silent fail - CSRF token fetch failure is not critical
            pass
        
        return None
    
    def reset_failure_tracking(self, url: str, auth_method: str = "oauth") -> None:
        """Reset failure tracking for a URL+auth method (use when retrying with fresh tokens)."""
        cache_key = (url, auth_method.lower())
        if cache_key in self._failure_cache:
            self._failure_cache.discard(cache_key)
    
    def clear_failure_cache(self) -> None:
        """Clear failure tracking cache"""
        self._failure_cache.clear()


# Token managers
api_token_manager = OAuth2TokenManager(
    API_OAUTH_CLIENT_ID,
    API_OAUTH_CLIENT_SECRET,
    API_OAUTH_TOKEN_URL
)

runtime_token_manager = OAuth2TokenManager(
    CPI_OAUTH_CLIENT_ID,
    CPI_OAUTH_CLIENT_SECRET,
    CPI_OAUTH_TOKEN_URL
)

csrf_token_manager = CSRFTokenManager()


# Validate required environment variables
if not API_BASE_URL:
    raise ValueError("Missing required environment variable: API_BASE_URL")
if not CPI_BASE_URL:
    raise ValueError("Missing required environment variable: CPI_BASE_URL")
if not all([API_OAUTH_CLIENT_ID, API_OAUTH_CLIENT_SECRET, API_OAUTH_TOKEN_URL]):
    raise ValueError("Missing required API OAuth environment variables: API_OAUTH_CLIENT_ID, API_OAUTH_CLIENT_SECRET, API_OAUTH_TOKEN_URL")

# Validate CPI authentication config (either OAuth or Basic Auth required)
if CPI_AUTH_METHOD.lower() == "oauth":
    if not all([CPI_OAUTH_CLIENT_ID, CPI_OAUTH_CLIENT_SECRET, CPI_OAUTH_TOKEN_URL]):
        raise ValueError("Missing required CPI OAuth environment variables: CPI_OAUTH_CLIENT_ID, CPI_OAUTH_CLIENT_SECRET, CPI_OAUTH_TOKEN_URL")
elif CPI_AUTH_METHOD.lower() == "basic":
    if not all([CPI_BASIC_AUTH_USERNAME, CPI_BASIC_AUTH_PASSWORD]):
        raise ValueError("Missing required CPI HTTP Basic Auth environment variables: CPI_BASIC_AUTH_USERNAME, CPI_BASIC_AUTH_PASSWORD")
elif CPI_AUTH_METHOD.lower() == "auto":
    has_oauth = all([CPI_OAUTH_CLIENT_ID, CPI_OAUTH_CLIENT_SECRET, CPI_OAUTH_TOKEN_URL])
    has_basic = all([CPI_BASIC_AUTH_USERNAME, CPI_BASIC_AUTH_PASSWORD])
    if not (has_oauth or has_basic):
        raise ValueError("Missing required CPI authentication variables. Provide either OAuth credentials (CPI_OAUTH_CLIENT_ID, CPI_OAUTH_CLIENT_SECRET, CPI_OAUTH_TOKEN_URL) or Basic Auth credentials (CPI_BASIC_AUTH_USERNAME, CPI_BASIC_AUTH_PASSWORD)")


def _has_cpi_oauth() -> bool:
    return all([CPI_OAUTH_CLIENT_ID, CPI_OAUTH_CLIENT_SECRET, CPI_OAUTH_TOKEN_URL])


def _has_cpi_basic() -> bool:
    return all([CPI_BASIC_AUTH_USERNAME, CPI_BASIC_AUTH_PASSWORD])


def _resolve_runtime_auth(headers: Dict[str, str]) -> tuple[str, Optional[tuple[str, str]], Dict[str, str]]:
    """
    Resolve runtime authentication method and headers.
    Returns (auth_method, auth_tuple, headers).
    """
    preferred = (CPI_AUTH_METHOD or "oauth").lower()
    candidates: List[str] = []

    if preferred == "auto":
        if _has_cpi_oauth():
            candidates.append("oauth")
        if _has_cpi_basic():
            candidates.append("basic")
    elif preferred in ("oauth", "basic"):
        candidates.append(preferred)
    else:
        candidates.append(preferred)

    last_error: Optional[Exception] = None
    for method in candidates:
        method_lower = method.lower()
        working_headers = dict(headers)
        if method_lower == "oauth" and _has_cpi_oauth():
            try:
                token = runtime_token_manager.get_token()
                working_headers["Authorization"] = f"Bearer {token}"
                return "oauth", None, working_headers
            except Exception as e:
                last_error = e
                continue

        if method_lower == "basic" and _has_cpi_basic():
            working_headers.pop("Authorization", None)
            # These are guaranteed non-None because _has_cpi_basic() checks them
            username = CPI_BASIC_AUTH_USERNAME or ""
            password = CPI_BASIC_AUTH_PASSWORD or ""
            return "basic", (username, password), working_headers

    if last_error:
        raise last_error
    raise ValueError("No valid CPI authentication method configured")


def _get_csrf_token_with_fallback(
    session: requests.Session,
    headers: Dict[str, str],
    auth_method: str,
    candidate_urls: List[str]
) -> Optional[str]:
    for candidate_url in candidate_urls:
        token = csrf_token_manager.get_token(
            session=session,
            endpoint_url=candidate_url,
            headers=headers,
            auth_method=auth_method
        )
        if token:
            return token
    return None


def parse_odata_xml_response(xml_content: str) -> Dict[str, Any]:
    """Parse OData XML (Atom) response to extract data"""
    try:
        root = ET.fromstring(xml_content)
        
        # OData Atom XML namespaces
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'm': 'http://schemas.microsoft.com/ado/2007/08/dataservices/metadata',
            'd': 'http://schemas.microsoft.com/ado/2007/08/dataservices'
        }
        
        results = []
        
        # Find all entry elements
        for entry in root.findall('.//atom:entry', namespaces):
            result = {}
            
            # Extract properties from content/properties
            properties = entry.find('.//m:properties', namespaces)
            if properties is not None:
                for prop in properties:
                    # Remove namespace prefix from tag
                    tag = prop.tag.split('}')[-1] if '}' in prop.tag else prop.tag
                    result[tag] = prop.text if prop.text else ''
            
            if result:
                results.append(result)
        
        return {'d': {'results': results}}
    
    except Exception:
        # If XML parsing fails, return empty structure
        return {'d': {'results': []}}



def parse_iflow_xml(xml_content: str) -> Dict[str, Any]:
    """Parse iFlow XML to extract key information"""
    try:
        root = ET.fromstring(xml_content)
        
        # Extract namespaces
        namespaces = {
            'ifl': 'http://www.sap.com/ifl',
            'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL'
        }
        
        # Detect sender adapters
        sender_adapters = []
        for sender in root.findall('.//bpmn2:participant[@processRef]', namespaces):
            name = sender.get('name', 'Unknown')
            sender_adapters.append(name)
        
        # Detect receiver adapters
        receiver_adapters = []
        for receiver in root.findall('.//bpmn2:endEvent', namespaces):
            name = receiver.get('name', 'Unknown')
            receiver_adapters.append(name)
        
        # Detect data format
        data_format = "Unknown"
        if 'JSON' in xml_content or 'json' in xml_content.lower():
            data_format = "JSON"
        elif 'XML' in xml_content or 'xml' in xml_content.lower():
            data_format = "XML"
        
        # Detect HTTP method from process
        http_method = "POST"  
        if 'GET' in xml_content:
            http_method = "GET"
        elif 'PUT' in xml_content:
            http_method = "PUT"
        elif 'DELETE' in xml_content:
            http_method = "DELETE"
        
        return {
            "sender_adapters": sender_adapters,
            "receiver_adapters": receiver_adapters,
            "data_format": data_format,
            "http_method": http_method,
            "has_mapping": "mapping" in xml_content.lower() or "xslt" in xml_content.lower(),
            "has_scripting": "script" in xml_content.lower() or "groovy" in xml_content.lower()
        }
    except Exception as e:
        return {"error": f"Failed to parse iFlow XML: {str(e)}"}


def _download_iflow_internal(integration_flow_id: str, version: str = "active") -> Dict[str, Any]:
    """Internal function to download iFlow - used by both tool and other functions"""
    try:
        token = api_token_manager.get_token()
        
        # Download iFlow ZIP
        url = f"{API_BASE_URL}/IntegrationDesigntimeArtifacts(Id='{integration_flow_id}',Version='{version}')/$value"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 401:
            api_token_manager.refresh_token()
            token = api_token_manager.get_token()
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )
        
        response.raise_for_status()
        
        # Extract ZIP content
        zip_buffer = io.BytesIO(response.content)
        iflow_data = {
            "integration_flow_id": integration_flow_id,
            "version": version,
            "files": [],
            "iflow_xml": None,
            "metadata": {}
        }
        
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            for file_info in zip_file.filelist:
                file_name = file_info.filename
                iflow_data["files"].append(file_name)
                
                # Extract main iFlow XML
                if file_name.endswith('.iflw'):
                    content = zip_file.read(file_name).decode('utf-8')
                    iflow_data["iflow_xml"] = content
                    iflow_data["metadata"] = parse_iflow_xml(content)
                
                # Extract XSD schemas if present
                elif file_name.endswith('.xsd'):
                    content = zip_file.read(file_name).decode('utf-8')
                    if "schemas" not in iflow_data:
                        iflow_data["schemas"] = {}
                    iflow_data["schemas"][file_name] = content
        
        return iflow_data
    
    except Exception as e:
        return {"error": f"Failed to download iFlow: {str(e)}"}

#Tool 1 find-package-by-id
@mcp.tool(
    name="get_integration_package_by_id",
    description=(
        "Fetch details of a single SAP CPI Integration Package by its exact ID. "
        "Use this when you already know the package ID and need its metadata such as name, version, short text, and vendor. "
        "Returns package details as a JSON object. "
        "If you don't know the package ID yet, call get_all_integration_packages first to discover available packages."
    )
)
async def get_an_integration_package(integration_package_id: str):
    """
    Args:
        integration_package_id: Integration Package ID (example: "MyPackage")
    """
    _log_call("get_integration_package_by_id", integration_package_id=integration_package_id)
    try:
        results = await get_an_integration_package_tool(integration_package_id)
        _log_response("get_integration_package_by_id", results)
        return results
    except Exception as e:
        _log_error("get_integration_package_by_id", e)
        raise

#Tool 2 get-all-packages
@mcp.tool(
    name="get_all_integration_packages",
    description=(
        "List all SAP CPI Integration Packages available in the tenant. "
        "Use this as a discovery step to find package IDs before working with specific packages or their integration flows. "
        "Returns a list of packages, each with an ID, name, short description, version, and vendor. "
        "Once you have a package ID, use get_integration_package_by_id for details or download-iflow to inspect a specific flow inside that package."
    )
)
async def get_all_integration_package():
    """ Returns all integration packages available in the tenant. """
    _log_call("get_all_integration_packages")
    try:
        results = await get_all_integration_package_tool()
        _log_response("get_all_integration_packages", results)
        return results
    except Exception as e:
        _log_error("get_all_integration_packages", e)
        raise

#Tool 3
@mcp.tool(
    name="download-iflow",
    description=(
        "Download an SAP CPI Integration Flow (iFlow) as a ZIP and extract its internals. "
        "Returns the list of files in the ZIP, the raw iFlow definition XML (.iflw), any XSD schemas, "
        "and parsed metadata including sender/receiver adapters, HTTP method, data format, and whether the flow uses mapping or scripting. "
        "Use this before generate-sample-payload-with-llm to understand the iFlow structure. "
        "Parameters: integration_flow_id (required) — the iFlow artifact ID; version (optional, default 'active')."
    )
)
def download_iflow(integration_flow_id: str, version: str = "active") -> Dict[str, Any]:
    _log_call("download-iflow", integration_flow_id=integration_flow_id, version=version)
    result = _download_iflow_internal(integration_flow_id, version)
    _log_response("download-iflow", result)
    return result

#Tool 4
@mcp.tool(
    name="get-iflow-endpoint",
    description=(
        "Get the live runtime HTTP endpoint URL for a deployed SAP CPI Integration Flow. "
        "Use this when you need to know the exact URL to call the iFlow (e.g., before using test-iflow-with-payload). "
        "The iFlow must already be deployed to the runtime for this to return results — design-time only artifacts will return no endpoints. "
        "Returns the endpoint URL string. "
        "Parameter: integration_flow_id — the iFlow artifact ID or its display name."
    )
)
def get_iflow_endpoint(integration_flow_id: str) -> Dict[str, Any]:
    _log_call("get-iflow-endpoint", integration_flow_id=integration_flow_id)
    try:
        token = api_token_manager.get_token()

        if not API_BASE_URL:
            raise ValueError("API_BASE_URL environment variable is not set")
        url = API_BASE_URL
        if "ServiceEndpoints" not in url:
            url = f"{API_BASE_URL}/ServiceEndpoints"

        params = {
            "$filter": f"Name eq '{integration_flow_id}'",
            "$expand": "EntryPoints",
            "$format": "json"
        }
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 401:
            runtime_token_manager.refresh_token()
            token = runtime_token_manager.get_token()
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, params=params)

        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        if "xml" in content_type:
            data = parse_odata_xml_response(response.text)
        else:
            data = response.json()

        entries = []
        urls = []

        if isinstance(data.get("d"), dict):
            for service in data["d"].get("results", []):
                entry_points = service.get("EntryPoints", {}).get("results", [])
                for ep in entry_points:
                    url = ep.get("Url")
                    if url:
                        urls.append(url)

        # Example: take first URL if you expect only one
        endpoint_url = urls[0] if urls else "unabe to fetch url"

        result = {
            "integration_flow_id": integration_flow_id,
            "count": len(entries),
            "endpoints": endpoint_url
        }
        _log_response("get-iflow-endpoint", result)
        return result

    except Exception as e:
        _log_error("get-iflow-endpoint", e)
        return {"error": f"Failed to get endpoint: {str(e)}"}


#Tool 5
@mcp.tool(
    name="generate-sample-payload-with-llm",
    description=(
        "Analyze an SAP CPI iFlow and produce a structured analysis that helps an LLM generate a realistic test payload. "
        "Downloads the iFlow, inspects its adapters, data format (JSON/XML), HTTP method, XSD schemas, and scripting steps, "
        "then returns that analysis together with LLM instructions. "
        "The calling agent should read the returned 'analysis' and 'llm_instructions' fields and use them to generate the actual payload. "
        "Call this BEFORE test-iflow-with-payload when you don't yet have a payload. "
        "Parameters: integration_flow_id (required); llm_prompt (optional custom instruction override); version (optional, default 'active')."
    )
)
def generate_sample_payload_with_llm(
    integration_flow_id: str,
    llm_prompt: Optional[str] = None,
    version: str = "active"
) -> Dict[str, Any]:
    _log_call("generate-sample-payload-with-llm", integration_flow_id=integration_flow_id, version=version)
    # Get comprehensive iFlow analysis
    iflow_data = _download_iflow_internal(integration_flow_id, version)
    
    if "error" in iflow_data:
        return {"error": iflow_data["error"]}
    
    metadata = iflow_data.get("metadata", {})
    
    # Build comprehensive analysis
    analysis = f"""
=== SAP CPI iFlow Analysis for Payload Generation ===

Integration Flow ID: {integration_flow_id}
Version: {version}

--- Adapter Information ---
Sender Adapters: {', '.join(metadata.get('sender_adapters', ['Not detected']))}
Receiver Adapters: {', '.join(metadata.get('receiver_adapters', ['Not detected']))}

--- Data Format ---
Expected Format: {metadata.get('data_format', 'Unknown')}
HTTP Method: {metadata.get('http_method', 'unknown')}

--- Processing Capabilities ---
Has Data Mapping: {metadata.get('has_mapping', False)}
Has Scripting/Transformation: {metadata.get('has_scripting', False)}

--- Available Schemas ---
"""
    
    # Add schema information if available
    if "schemas" in iflow_data:
        analysis += f"Found {len(iflow_data['schemas'])} XSD schema(s):\n"
        for schema_name, schema_content in iflow_data['schemas'].items():
            analysis += f"\n--- Schema: {schema_name} ---\n"
            # Extract root elements from schema
            try:
                schema_root = ET.fromstring(schema_content)
                elements = schema_root.findall('.//{http://www.w3.org/2001/XMLSchema}element[@name]')
                if elements:
                    element_names = [name for elem in elements[:5] if (name := elem.get('name')) is not None]
                    analysis += "Root elements: " + ', '.join(element_names) + "\n"
                    analysis += f"\nSchema Content (first 1000 chars):\n{schema_content[:1000]}\n"
            except:
                analysis += "Schema parsing failed\n"
    else:
        analysis += "No XSD schemas found in iFlow package\n"
    
    analysis += """
--- Recommended Actions for LLM ---
Based on this analysis, please generate a realistic sample payload that:
1. Matches the expected data format (JSON/XML)
2. Contains realistic business data (e.g., order, customer, product info)
3. Includes all required fields based on schemas (if available)
4. Uses appropriate data types and structures
5. Can be used to test the iFlow end-to-end

Please generate a complete, valid sample payload suitable for testing this iFlow.
"""
    
    default_prompt = """
Based on the iFlow analysis above, generate a realistic sample payload.

Consider:
- The data format (JSON/XML)
- Any schemas or field definitions
- Typical business scenarios (orders, customers, products, etc.)
- Required vs optional fields

Provide the payload in the correct format, ready to send to the iFlow endpoint.
"""
    
    result = {
        "integration_flow_id": integration_flow_id,
        "analysis": analysis,
        "llm_instructions": llm_prompt or default_prompt,
        "note": "The calling agent should now use this analysis to generate an appropriate payload"
    }
    _log_response("generate-sample-payload-with-llm", result)
    return result


def _send_http_request(
    session: requests.Session,
    http_method: str,
    url: str,
    payload: str,
    headers: Dict[str, str],
    auth: Optional[tuple[str, str]] = None
) -> requests.Response:
    """
    Helper to send HTTP request with proper error handling and timeouts.
    Returns a Response object (never raises, always returns a response).
    """
    try:
        if http_method.upper() == "GET":
            return session.get(url, headers=headers, auth=auth, timeout=60)
        elif http_method.upper() == "POST":
            return session.post(url, data=payload, headers=headers, auth=auth, timeout=60)
        elif http_method.upper() == "PUT":
            return session.put(url, data=payload, headers=headers, auth=auth, timeout=60)
        elif http_method.upper() == "DELETE":
            return session.delete(url, headers=headers, auth=auth, timeout=60)
        else:
            response = requests.Response()
            response.status_code = 400
            response._content = f"Unsupported HTTP method: {http_method}".encode()
            return response
    except requests.exceptions.Timeout:
        response = requests.Response()
        response.status_code = 504
        response._content = b"Request timeout after 60 seconds"
        return response
    except Exception as e:
        response = requests.Response()
        response.status_code = 500
        response._content = str(e).encode()
        return response

#Tool 7 test-iflow-with-payload

@mcp.tool(
    name="test-iflow-with-payload",
    description=(
        "Send an HTTP request to a deployed SAP CPI Integration Flow endpoint and validate the response. "
        "Handles authentication (OAuth or Basic Auth) and CSRF token fetching automatically, with one retry on 401/403. "
        "Returns a result dict with test_status ('SUCCESS' or 'FAILED'), http_status code, auth method used, csrf_token_used flag, "
        "the full response body, and response headers. "
        "Use get-iflow-endpoint first if you need the endpoint URL. "
        "Use generate-sample-payload-with-llm first if you need help constructing the payload. "
        "Parameters: "
        "integration_flow_id (required) — iFlow artifact ID or name; "
        "endpoint_path (required) — relative path after the base URL, e.g. 'http/my_iflow'; "
        "payload (required) — request body as a string (JSON or XML); "
        "content_type (optional, default 'application/json') — MIME type of the payload; "
        "http_method (optional, default 'POST') — GET, POST, PUT, or DELETE; "
        "csrf_endpoint_path (optional) — alternate relative path to fetch the CSRF token from if the main endpoint doesn't support it; "
        "header (optional) — dict of additional HTTP headers to include in the request."
    )
)
def test_iflow_with_payload(
    integration_flow_id: str,
    payload: str,
    endpoint_path: str,
    content_type: str = "application/json",
    http_method: str = "POST",
    csrf_endpoint_path: Optional[str] = None,
    header: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    _log_call("test-iflow-with-payload",
              integration_flow_id=integration_flow_id,
              endpoint_path=endpoint_path,
              http_method=http_method,
              content_type=content_type,
              payload_preview=payload[:200] + "..." if len(payload) > 200 else payload)

    # ---------------------------------------
    # 1. Build URLs
    # ---------------------------------------
    endpoint_path = endpoint_path.lstrip("/")
    url = f"{CPI_BASE_URL}/{endpoint_path}"

    csrf_url = url
    if csrf_endpoint_path:
        csrf_endpoint_path = csrf_endpoint_path.lstrip("/")
        csrf_url = f"{CPI_BASE_URL}/{csrf_endpoint_path}"

    session = requests.Session()

    # ---------------------------------------
    # 2. Decide AUTH (OAuth, Basic, or Auto)
    # ---------------------------------------
    headers = {
        "Content-Type": content_type,
        "Accept": "*/*"
    }
    logger.info("[test-iflow-with-payload] extra headers from caller: %s", header)
    if header:
        for hdr_key in header:
            value=header[hdr_key]
            headers[hdr_key]= value
    # If entity provided → also send in header (optional CPI pattern)
    # if entity:
        # headers["entity"] = entity

    auth_method_used, auth, headers = _resolve_runtime_auth(headers)

    # ---------------------------------------
    # 3. Fetch CSRF token (if required)
    # ---------------------------------------
    csrf_token = None
    fallback_used = False

    if http_method.upper() in ("POST", "PUT", "DELETE"):
        csrf_candidates = [csrf_url]
        if csrf_url != url:
            csrf_candidates.append(url)

        csrf_token = _get_csrf_token_with_fallback(
            session=session,
            headers=headers,
            auth_method=auth_method_used,
            candidate_urls=csrf_candidates
        )

        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

    # ---------------------------------------
    # 4. Send HTTP request
    # ---------------------------------------
    response = _send_http_request(
        session=session,
        http_method=http_method,
        url=url,
        payload=payload,
        headers=headers,
        auth=auth
    )

    # ---------------------------------------
    # 5. Retry ONCE on 401/403
    # ---------------------------------------
    if response.status_code in (401, 403):

        if auth_method_used == "oauth":
            try:
                runtime_token_manager.refresh_token()
                headers["Authorization"] = f"Bearer {runtime_token_manager.get_token()}"
            except Exception:
                if _has_cpi_basic():
                    auth_method_used = "basic"
                    auth = (CPI_BASIC_AUTH_USERNAME, CPI_BASIC_AUTH_PASSWORD)
                    headers.pop("Authorization", None)
                    fallback_used = True

        elif auth_method_used == "basic" and _has_cpi_oauth():
            auth_method_used = "oauth"
            auth = None
            headers["Authorization"] = f"Bearer {runtime_token_manager.get_token()}"
            fallback_used = True

        # Retry CSRF
        if http_method.upper() in ("POST", "PUT", "DELETE"):
            csrf_token_manager.reset_failure_tracking(csrf_url, auth_method=auth_method_used)

            csrf_candidates = [csrf_url]
            if csrf_url != url:
                csrf_candidates.append(url)

            csrf_token = _get_csrf_token_with_fallback(
                session=session,
                headers=headers,
                auth_method=auth_method_used,
                candidate_urls=csrf_candidates
            )

            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token
            else:
                headers.pop("X-CSRF-Token", None)

        final_auth: Optional[tuple[str, str]] = None
        if isinstance(auth, tuple) and len(auth) == 2:
            final_auth = (auth[0], auth[1])  # type: ignore

        response = _send_http_request(
            session=session,
            http_method=http_method,
            url=url,
            payload=payload,
            headers=headers,
            auth=final_auth
        )

    # ---------------------------------------
    # 6. Build result
    # ---------------------------------------
    success = 200 <= response.status_code < 300
    response_body = response.text
    try:
        data = response.json()
        logger.info("[test-iflow-with-payload] response body (JSON): %s",
                    str(data)[:400] + "..." if len(str(data)) > 400 else data)
        response_body = data
    except json.JSONDecodeError:
        logger.info("[test-iflow-with-payload] response body (text): %s",
                    response_body[:400] + "..." if len(response_body) > 400 else response_body)

    result = {
        "integration_flow_id": integration_flow_id,
        "endpoint_url": url,
        "test_status": "SUCCESS" if success else "FAILED",
        "http_status": response.status_code,
        "auth_method": auth_method_used,
        "auth_fallback_used": fallback_used,
        "csrf_token_used": csrf_token is not None,
        "request": {
            "content_type": content_type,
            "payload_preview": payload[:500] + "..." if len(payload) > 500 else payload
        },
        "response": {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response_body,
            "body_length": len(response.text)
        }
    }
    _log_response("test-iflow-with-payload", {
        "test_status": result["test_status"],
        "http_status": result["http_status"],
        "auth_method": result["auth_method"],
        "csrf_token_used": result["csrf_token_used"],
    })
    return result

#Tool 7
@mcp.tool(
    name="get-iflow-configuration",
    description=(
        "Fetch the design-time configuration parameters (key/value pairs) of an SAP CPI Integration Flow. "
        "Configuration parameters typically include adapter settings such as endpoint paths, target system URLs, and timeout values. "
        "Use this to understand how an iFlow is configured before testing it, or to verify parameter values without downloading the full ZIP. "
        "Returns a 'configurations' dict mapping ParameterKey → ParameterValue. "
        "Parameters: integration_flow_id (required); version (optional, default 'active')."
    )
)
def get_iflow_configuration(integration_flow_id: str, version: str = "active") -> Dict[str, Any]:
    _log_call("get-iflow-configuration", integration_flow_id=integration_flow_id, version=version)
    try:
        token = api_token_manager.get_token()

        url = f"{API_BASE_URL}/IntegrationDesigntimeArtifacts(Id='{integration_flow_id}',Version='{version}')/Configurations"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 401:
            api_token_manager.refresh_token()
            token = api_token_manager.get_token()
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )

        response.raise_for_status()

        # Try JSON first, fall back to XML if needed
        try:
            data = response.json()
        except Exception:
            # Response is likely XML (OData Atom format)
            data = parse_odata_xml_response(response.text)

        configurations = {}
        if "d" in data and "results" in data["d"]:
            for config in data["d"]["results"]:
                param_key = config.get("ParameterKey")
                param_value = config.get("ParameterValue")
                configurations[param_key] = param_value

        result = {
            "integration_flow_id": integration_flow_id,
            "version": version,
            "configurations": configurations
        }
        _log_response("get-iflow-configuration", result)
        return result

    except Exception as e:
        _log_error("get-iflow-configuration", e)
        return {"error": f"Failed to get configurations: {str(e)}"}

#Tool 9
@mcp.tool(
    name="get-message-logs",
    description=(
        "Fetch the error details and full log text for a failed SAP CPI message using its Message Processing Log ID. "
        "Use this to diagnose why an iFlow invocation failed — for example, when test-iflow-with-payload returns a non-2xx status "
        "and you need to see the root cause error from the CPI runtime. "
        "The message_id is typically visible in the CPI monitoring UI (Operations → Message Monitor) or returned in error response headers. "
        "Returns 'logs' (raw error text), 'success' flag, and 'log_length'. "
        "Parameter: message_id (required) — the GUID of the message processing log entry."
    )
)
def get_message_logs(message_id: str) -> Dict[str, Any]:
    """
    Fetch message error/log details from SAP CPI MessageProcessingLogs API.

    Args:
        message_id: Message Processing Log ID

    Returns:
        Error/log text and metadata
    """
    _log_call("get-message-logs", message_id=message_id)
    try:
        # ---------------------------------------
        # 1. Get OAuth token (API OAuth)
        # ---------------------------------------
        token = api_token_manager.get_token()

        # ---------------------------------------
        # 2. Build URL using API_BASE_URL
        # ---------------------------------------
        url = f"{API_BASE_URL}/MessageProcessingLogs('{message_id}')/ErrorInformation/$value"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "text/plain"
        }

        # ---------------------------------------
        # 3. Call CPI API
        # ---------------------------------------
        response = requests.get(url, headers=headers, timeout=60)

        # Retry once if token expired
        if response.status_code == 401:
            api_token_manager.refresh_token()
            token = api_token_manager.get_token()

            headers["Authorization"] = f"Bearer {token}"
            response = requests.get(url, headers=headers, timeout=60)

        # ---------------------------------------
        # 4. Handle response
        # ---------------------------------------
        if response.status_code == 200:
            result = {
                "success": True,
                "message_id": message_id,
                "logs": response.text,
                "log_length": len(response.text)
            }
            _log_response("get-message-logs", {"success": True, "log_length": result["log_length"]})
            return result

        result = {
            "success": False,
            "message_id": message_id,
            "status_code": response.status_code,
            "error": response.text
        }
        _log_response("get-message-logs", result)
        return result

    except Exception as e:
        _log_error("get-message-logs", e)
        return {
            "success": False,
            "message_id": message_id,
            "error": str(e)
        }

#Tool 10
@mcp.tool(
    name="create_wbs",
    description=(
        "Create a WBS (Work Breakdown Structure) element in SAP S/4HANA via the CPI iFlow endpoint. "
        "Automatically generates a unique 17-digit ProjectExternalID (base '14000000000000' + random 3-digit suffix) on every call, "
        "so you do not need to provide one. "
        "Required parameters: planned_start_date and planned_end_date — both in YYYY-MM-DD format (e.g. '2026-05-13'). "
        "Optional: project_profile_code (default 'ZMCRPPM') — the SAP project profile that controls WBS behaviour. "
        "Returns: status_code (HTTP), project_external_id (the auto-generated ID that was used), and the SAP response body."
    )
)
def create_wbs(
    planned_start_date: str,
    planned_end_date: str,
    project_profile_code: str = "ZMCRPPM"
) -> Dict[str, Any]:
    """
    Args:
        planned_start_date: Planned start date in YYYY-MM-DD format (e.g. "2026-05-13")
        planned_end_date: Planned end date in YYYY-MM-DD format (e.g. "2026-10-30")
        project_profile_code: SAP project profile code (default: "ZMCRPPM")
    """
    _log_call("create_wbs",
              planned_start_date=planned_start_date,
              planned_end_date=planned_end_date,
              project_profile_code=project_profile_code)
    suffix = random.randint(100, 999)
    project_external_id = f"14000000000000{suffix}"

    payload = json.dumps({
        "ProjectProfileCode": project_profile_code,
        "ProjectExternalID": project_external_id,
        "PlannedStartDate": planned_start_date,
        "PlannedEndDate": planned_end_date
    })

    url = f"{CPI_BASE_URL}/http/create_wbs"
    session = requests.Session()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    auth_method_used, auth, headers = _resolve_runtime_auth(headers)

    csrf_token = _get_csrf_token_with_fallback(session, headers, auth_method_used, [url])
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token

    response = _send_http_request(session, "POST", url, payload, headers, auth)

    if response.status_code in (401, 403):
        if auth_method_used == "oauth":
            runtime_token_manager.refresh_token()
            headers["Authorization"] = f"Bearer {runtime_token_manager.get_token()}"
        csrf_token_manager.reset_failure_tracking(url, auth_method=auth_method_used)
        csrf_token = _get_csrf_token_with_fallback(session, headers, auth_method_used, [url])
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token
        else:
            headers.pop("X-CSRF-Token", None)
        response = _send_http_request(session, "POST", url, payload, headers, auth)

    response.raise_for_status()

    try:
        response_body = response.json()
    except Exception:
        response_body = response.text

    result = {
        "status_code": response.status_code,
        "project_external_id": project_external_id,
        "response_body": response_body
    }
    _log_response("create_wbs", result)
    return result


_MAINTENANCE_ORDER_PAYLOAD = {
    "MaintenanceOrderType": "YBA1",
    "MaintenanceOrderDesc": "Test",
    "MaintOrdBasicStartDateTime": "2026-06-04T10:40:00+05:30",
    "MaintOrdBasicEndDateTime": "2026-07-22T07:17:00+05:30",
    "MainWorkCenter": "RES-0100",
    "MainWorkCenterPlant": "1710",
    "MaintenancePlanningPlant": "1710",
    "MaintenancePlant": "1710",
    "FunctionalLocation": "1710-SPA-SAC-PLAR1-CLR2",
    "to_MaintenanceOrderOperation": {
        "results": [
            {
                "MaintenanceOrderOperation": "0010",
                "MaintenanceOrderSubOperation": "",
                "OperationControlKey": "YBM1",
                "WorkCenter": "RES-0100",
                "Plant": "1710",
                "OperationDescription": "OP1",
                "NumberOfCapacities": 0,
                "OperationWorkPercent": 0,
                "OperationCalculationControl": "",
                "ActivityType": "",
                "DeliveryTimeInDays": "0",
                "MaintenanceObjectListItem": 0,
                "AllMaintOrdCompCmtdQtsAreKept": False,
                "to_MaintOrderOpComponent_2": {
                    "results": [
                        {
                            "Product": "SP001",
                            "BaseUnit": "PC",
                            "Plant": "1710",
                            "QuantityInUnitOfEntry": "1",
                            "MaintComponentItemCategory": "L",
                            "GoodsMovementIsAllowed": True,
                            "QuantityIsFixed": True,
                            "MatlCompIsMarkedForBackflush": False,
                            "MaintOrdOpCompIsBulkProduct": False,
                            "RqmtDateIsEnteredManually": False,
                            "SrvcSchedgIsAlignedWthOpWrkCtr": False
                        }
                    ]
                }
            }
        ]
    }
}

#Tool 11
@mcp.tool(
    name="create_maintenance_order",
    description=(
        "Create a Maintenance Order in SAP S/4HANA via the CPI iFlow endpoint. "
        "No parameters are needed — the request payload is fully predefined: "
        "order type YBA1, description 'Test', work center RES-0100, planning plant 1710, "
        "functional location 1710-SPA-SAC-PLAR1-CLR2, one operation (0010, key YBM1) with component SP001 (quantity 1 PC). "
        "Returns: status_code (HTTP) and the SAP response body containing the created order number and details."
    )
)
def create_maintenance_order() -> Dict[str, Any]:
    """ Creates a Maintenance Order in SAP with a predefined standard payload. """
    _log_call("create_maintenance_order")
    url = f"{CPI_BASE_URL}/http/create_maintenance_order"
    payload = json.dumps(_MAINTENANCE_ORDER_PAYLOAD)

    session = requests.Session()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    auth_method_used, auth, headers = _resolve_runtime_auth(headers)

    csrf_token = _get_csrf_token_with_fallback(session, headers, auth_method_used, [url])
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token

    response = _send_http_request(session, "POST", url, payload, headers, auth)

    if response.status_code in (401, 403):
        if auth_method_used == "oauth":
            runtime_token_manager.refresh_token()
            headers["Authorization"] = f"Bearer {runtime_token_manager.get_token()}"
        csrf_token_manager.reset_failure_tracking(url, auth_method=auth_method_used)
        csrf_token = _get_csrf_token_with_fallback(session, headers, auth_method_used, [url])
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token
        else:
            headers.pop("X-CSRF-Token", None)
        response = _send_http_request(session, "POST", url, payload, headers, auth)

    response.raise_for_status()

    try:
        response_body = response.json()
    except Exception:
        response_body = response.text

    result = {
        "status_code": response.status_code,
        "response_body": response_body
    }
    _log_response("create_maintenance_order", result)
    return result
