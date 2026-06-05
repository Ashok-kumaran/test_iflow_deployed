# import os
# import json
# import zipfile
# import re
# import httpx
# from typing import Optional, Any, Dict, Union
# from fastmcp import FastMCP

# # CPI Design-time tools (keep)
# from _tool._get_an_integration_flow_zip_tool import get_an_integration_flow_zip_tool
# from _tool._get_an_endpoint_of_an_integration_flow_tool import get_an_endpoint_of_an_integration_flow_tool

# # Runtime tools (keep)
# from _util.token_manager import TokenManager
# from _util.runtime_test import send_runtime_payload

# # Local helper (keep)
# from _util.int_suite_service import i_flow_path
# from _tool._get_all_integration_package_tool import get_all_integration_package_tool
# from _tool._get_an_integration_flow_of_an_integration_package_tool import get_an_integration_flow_of_an_integration_package_tool
# from _tool._get_configration_of_an_intergrairon_flow_tool import get_configuration_of_an_integration_flow_tool
# from _tool._get_an_integration_package_tool import get_an_integration_package_tool

# mcp = FastMCP("iflow_test_mcp_server")
    
# # -------------------------------------------------------------------
# # Helper: safely decode bytes
# # -------------------------------------------------------------------
# def _decode_bytes(data: bytes) -> str:
#     for enc in ("utf-8", "utf-16", "latin-1"):
#         try:
#             return data.decode(enc)
#         except Exception:
#             pass
#     return data.decode("utf-8", errors="ignore")


# def _find_iflow_xml_inside_zip(zip_path: str) -> Dict[str, Any]:
#     """
#     Best-effort extraction of the main iFlow model XML from the CPI artifact ZIP.
#     """
#     if not zip_path or not os.path.exists(zip_path):
#         return {"ok": False, "error": f"ZIP not found at path: {zip_path}"}

#     candidates = []
#     try:
#         with zipfile.ZipFile(zip_path, "r") as z:
#             names = z.namelist()

#             # Common likely candidates
#             for n in names:
#                 low = n.lower()
#                 if low.endswith(".iflw") or low.endswith(".iflmap"):
#                     candidates.append(n)
#                 if low.endswith(".xml") and ("iflow" in low or "integration" in low or "flow" in low):
#                     candidates.append(n)

#             # fallback any xml
#             if not candidates:
#                 candidates = [n for n in names if n.lower().endswith(".xml")]

#             if not candidates:
#                 return {"ok": False, "error": "No XML found in ZIP artifact"}

#             pick = candidates[0]
#             raw = z.read(pick)
#             return {
#                 "ok": True,
#                 "zip_path": zip_path,
#                 "file_name": pick,
#                 "xml_text": _decode_bytes(raw),
#                 "all_candidate_files": candidates[:20],
#             }

#     except Exception as e:
#         return {"ok": False, "error": str(e)}


# def ensure_runtime_rt_url(url: str) -> str:
#     """
#     Convert CPI design-time host to runtime host.

#     Example:
#       https://xxx.it-cpi019.cfapps.us10-002.hana.ondemand.com/http/abc
#    -> https://xxx.it-cpi019-rt.cfapps.us10-002.hana.ondemand.com/http/abc

#     If already -rt or pattern not matched, return as-is.
#     """
#     if not url or not isinstance(url, str):
#         return url

#     # already runtime host
#     if re.search(r"\.it-cpi\d+-rt\.cfapps\.", url):
#         return url

#     # convert design-time -> runtime
#     return re.sub(r"\.it-cpi(\d+)\.cfapps\.", r".it-cpi\1-rt.cfapps.", url)

# # -------------------------------------------------------------------
# # TOOL 1: get-iflow (download zip)
# # -------------------------------------------------------------------
# @mcp.tool(name="get-iflow")
# async def get_an_integration_flow_zip(
#     integration_flow_id: str,
#     version: str = "active",
# ):
#     """
#     Download an integration flow as ZIP file (design-time).
#     Args:
#         integration_flow_id: Integration Flow ID
#         version: 'active' or explicit version (e.g. 1.0.5)
#     """
#     try:
#         results = await get_an_integration_flow_zip_tool(integration_flow_id, version)
#         return results
#     except Exception as e:
#         return {"ok": False, "error": str(e)}


# # -------------------------------------------------------------------
# # TOOL 2: get-iflow-xml (extract xml from downloaded zip)
# # -------------------------------------------------------------------
# @mcp.tool(name="get-iflow-xml")
# async def get_iflow_xml_text(
#     integration_flow_id: str,
#     version: str = "active"
# ):
#     """
#     Download the iFlow ZIP and extract the main iFlow XML/model as plain text.
#     Args:
#         integration_flow_id: iFlow Artifact ID
#         version: 'active' or explicit version (e.g. 1.0.5)
#     """
#     try:
#         # ensure ZIP exists locally
#         await get_an_integration_flow_zip_tool(integration_flow_id, version)

#         zip_path = i_flow_path(integration_flow_id)
#         xml_info = _find_iflow_xml_inside_zip(zip_path)
#         return xml_info

#     except Exception as e:
#         return {"ok": False, "error": str(e)}


# # # -------------------------------------------------------------------
# # # TOOL 3: get-iflow-endpoint (raw list of all deployed endpoints)
# # # -------------------------------------------------------------------
# # @mcp.tool(name="get-iflow-endpoint")
# # async def get_an_endpoint_of_an_integration_flow():
# #     """
# #     Get all endpoints provided for deployed integration flows (raw endpoint list).
# #     Returns raw deployed endpoints response.
# #     """
# #     try:
# #         results = await get_an_endpoint_of_an_integration_flow_tool()
# #         return results
# #     except Exception as e:
# #         return {"ok": False, "error": str(e)}


# # # -------------------------------------------------------------------
# # # TOOL 4: find-iflow-runtime-endpoints (filter endpoints for one iflow)
# # # -------------------------------------------------------------------
# # @mcp.tool(name="find-iflow-runtime-endpoints",
# #     description="Find deployed endpoints for an iFlow and normalize URLs to runtime (-rt) host."
# # )
# # async def find_iflow_runtime_endpoints(
# #     integration_flow_id: str,
# #     url_contains: Optional[str] = None,
# # ) -> Dict[str, Any]:
# #     try:
# #         data = await get_an_endpoint_of_an_integration_flow_tool()

# #         endpoints = []
# #         if isinstance(data, dict):
# #             endpoints = (
# #                 data.get("endpoints")
# #                 or data.get("Endpoints")
# #                 or data.get("d", {}).get("results")
# #                 or []
# #             )
# #         if not isinstance(endpoints, list):
# #             endpoints = []

# #         matches = []
# #         for ep in endpoints:
# #             if not isinstance(ep, dict):
# #                 continue

# #             url = (
# #                 ep.get("url")
# #                 or ep.get("URL")
# #                 or ep.get("endpointUrl")
# #                 or ep.get("endpoint")
# #                 or ""
# #             )

# #             blob = json.dumps(ep, ensure_ascii=False).lower()
# #             if integration_flow_id.lower() not in blob:
# #                 continue

# #             if url_contains and url_contains.lower() not in str(url).lower():
# #                 continue

# #             fixed = ensure_runtime_rt_url(str(url))

# #             ep_out = dict(ep)
# #             ep_out["url_original"] = url
# #             ep_out["url_runtime"] = fixed
# #             matches.append(ep_out)

# #         chosen_url = None
# #         if matches:
# #             # prefer /http/ endpoints if present
# #             http_matches = [m for m in matches if "/http/" in str(m.get("url_runtime", "")).lower()]
# #             chosen_url = (http_matches[0]["url_runtime"] if http_matches else matches[0]["url_runtime"])

# #         return {
# #             "ok": True,
# #             "iflow_id": integration_flow_id,
# #             "count": len(matches),
# #             "chosen_url": chosen_url,
# #             "matches": matches
# #         }

# #     except Exception as e:
# #         return {"ok": False, "error": str(e)}

# # # -------------------------------------------------------------------
# # # TOOL 5: call-cpi-iflow-runtime (ONE-SHOT runtime test)
# # #   ✅ Supports GET/POST/PUT/PATCH/DELETE
# # #   ✅ Supports none/bearer/basic/auto auth
# # #   ✅ For GET: payload dict/list -> query params; payload str -> ignored (warning)
# # # -------------------------------------------------------------------
# # @mcp.tool(name="call-cpi-iflow-runtime")
# # async def call_cpi_iflow_runtime(
# #     endpoint_url: str,
# #     content_type: str = "application/json",
# #     payload: Union[dict, str, list, None] = None,
# #     timeout_seconds: float = 30.0,
# #     method: str = "POST",  # GET | POST | PUT | PATCH | DELETE
# #     auth_mode: str = "none",   # none | bearer | basic | auto
# #     basic_user: Optional[str] = None,
# #     basic_pass: Optional[str] = None,
# #     use_csrf: bool = False,
# #     csrf_fetch_url: Optional[str] = None,
# # ) -> Dict[str, Any]:
# #     try:
# #         normalized_endpoint_url = ensure_runtime_rt_url(endpoint_url)
# #         method_u = (method or "POST").upper()

# #         # --------------------------------------------
# #         # Internal helper: execute one HTTP call
# #         # --------------------------------------------
# #         async def _do_request(
# #             *,
# #             _auth_mode: str,
# #             _access_token: Optional[str] = None,
# #         ) -> Dict[str, Any]:
# #             """
# #             Executes a request using httpx directly so we can support GET + payload.
# #             For non-GET methods we reuse send_runtime_payload() (keeps CSRF handling).
# #             """
# #             headers = {"Accept": "*/*"}

# #             # Content-Type only makes sense when sending body (POST/PUT/PATCH/DELETE)
# #             if method_u != "GET":
# #                 headers["Content-Type"] = content_type

# #             req_auth = None
# #             if _auth_mode == "basic":
# #                 if not basic_user or not basic_pass:
# #                     return {"ok": False, "error": "basic_user/basic_pass required for auth_mode=basic"}
# #                 req_auth = (basic_user, basic_pass)

# #             elif _auth_mode == "bearer":
# #                 if not _access_token:
# #                     return {"ok": False, "error": "access_token required for auth_mode=bearer"}
# #                 headers["Authorization"] = f"Bearer {_access_token}"

# #             elif _auth_mode == "none":
# #                 pass
# #             else:
# #                 return {"ok": False, "error": f"Invalid auth_mode: {_auth_mode}"}

# #             # ✅ GET case: use query params instead of body
# #             if method_u == "GET":
# #                 params = None
# #                 warning = None

# #                 if isinstance(payload, dict):
# #                     # dict -> query string
# #                     params = payload
# #                 elif isinstance(payload, list):
# #                     # not typical for query params; stringify it
# #                     params = {"payload": json.dumps(payload)}
# #                     warning = "GET payload was a list; sent as ?payload=<json>"
# #                 elif isinstance(payload, str):
# #                     # GET body is not reliable; ignore string payload
# #                     warning = "GET with string payload is ignored; use query params dict instead"
# #                 elif payload is None:
# #                     pass
# #                 else:
# #                     warning = f"GET payload type {type(payload)} not supported; ignored"

# #                 async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
# #                     resp = await client.request(
# #                         method="GET",
# #                         url=normalized_endpoint_url,
# #                         headers=headers,
# #                         params=params,
# #                         auth=req_auth,
# #                     )

# #                 return {
# #                     "ok": resp.status_code < 400,
# #                     "step": "runtime_get",
# #                     "endpoint_url_original": endpoint_url,
# #                     "endpoint_url_normalized": normalized_endpoint_url,
# #                     "http_method": "GET",
# #                     "http_status": resp.status_code,
# #                     "response_headers": dict(resp.headers),
# #                     "response_body": resp.text,
# #                     "auth_mode_used": _auth_mode,
# #                     "warning": warning,
# #                 }

# #             # ✅ Non-GET: use your existing send_runtime_payload (keeps CSRF behavior)
# #             return await send_runtime_payload(
# #                 endpoint_url=normalized_endpoint_url,
# #                 content_type=content_type,
# #                 payload=payload,
# #                 timeout_seconds=timeout_seconds,
# #                 auth_mode=_auth_mode,
# #                 basic_user=basic_user,
# #                 basic_pass=basic_pass,
# #                 access_token=_access_token,
# #                 use_csrf=use_csrf,
# #                 csrf_fetch_url=csrf_fetch_url,
# #             )

# #         # --------------------------------------------
# #         # AUTO mode: none -> bearer -> basic
# #         # --------------------------------------------
# #         if auth_mode == "auto":
# #             # 1) NONE
# #             result = await _do_request(_auth_mode="none")
# #             if result.get("ok"):
# #                 result["auth_mode_used"] = "none"
# #                 return result

# #             # 2) BEARER
# #             access_token = await TokenManager.get_runtime_token()
# #             result = await _do_request(_auth_mode="bearer", _access_token=access_token)
# #             if result.get("ok"):
# #                 result["auth_mode_used"] = "bearer"
# #                 return result

# #             # 3) BASIC
# #             if basic_user and basic_pass:
# #                 result = await _do_request(_auth_mode="basic")
# #                 result["auth_mode_used"] = "basic"
# #                 return result

# #             # failed auto
# #             return {
# #                 **result,
# #                 "endpoint_url_original": endpoint_url,
# #                 "endpoint_url_normalized": normalized_endpoint_url,
# #                 "auth_mode_used": "auto_failed",
# #             }

# #         # --------------------------------------------
# #         # Manual mode: none/bearer/basic
# #         # --------------------------------------------
# #         access_token = None
# #         if auth_mode == "bearer":
# #             access_token = await TokenManager.get_runtime_token()

# #         result = await _do_request(_auth_mode=auth_mode, _access_token=access_token)

# #         # unify response metadata
# #         result.setdefault("endpoint_url_original", endpoint_url)
# #         result.setdefault("endpoint_url_normalized", normalized_endpoint_url)
# #         result["http_method"] = method_u
# #         return result

# #     except Exception as e:
# #         return {
# #             "ok": False,
# #             "error": str(e),
# #             "endpoint_url_original": endpoint_url,
# #             "http_method": (method or "POST").upper(),
# #         }

# CPI_BASE_URL = os.getenv("CPI_BASE_URL", "").rstrip("/")

# def _extract_sender_url_path_from_iflow_xml(xml_text: str) -> Optional[str]:
#     """
#     Extract the HTTPS Sender urlPath from the iFlow BPMN XML.
#     Example: <key>urlPath</key><value>/aif/mcp</value>
#     """
#     if not xml_text:
#         return None

#     # works with whitespace/newlines
#     m = re.search(r"<key>\s*urlPath\s*</key>\s*<value>\s*([^<\s]+)\s*</value>", xml_text, re.IGNORECASE)
#     if not m:
#         return None

#     url_path = m.group(1).strip()
#     if not url_path.startswith("/"):
#         url_path = "/" + url_path
#     return url_path


# def _build_runtime_http_endpoint(cpi_base_url: str, url_path: str) -> str:
#     """
#     Build runtime endpoint for CPI HTTP/HTTPS Sender:
#       https://<tenant>-rt.../http/<urlPath-without-leading-http>
#     """
#     base = (cpi_base_url or "").rstrip("/")
#     path = (url_path or "").strip()

#     if not base.startswith(("http://", "https://")):
#         raise ValueError(f"CPI_BASE_URL is invalid or missing protocol: {base}")

#     if not path.startswith("/"):
#         path = "/" + path

#     return f"{base}/http{path}"


# @mcp.tool(
#     name="test-iflow-runtime-by-id",
#     description="Download iFlow XML, extract HTTPS sender urlPath, build runtime URL from CPI_BASE_URL, and send payload."
# )
# async def test_iflow_runtime_by_id(
#     integration_flow_id: str,
#     payload: Union[dict, list, str],
#     content_type: str = "application/json",
#     method: str = "POST",
#     timeout_seconds: float = 30.0,
#     auth_mode: str = "bearer",  # default bearer because your senderAuthType=RoleBased
#     use_csrf: bool = False,
# ) -> Dict[str, Any]:
#     try:
#         if not CPI_BASE_URL:
#             return {"ok": False, "step": "config", "error": "CPI_BASE_URL env var is missing"}

#         # 1) Get XML
#         xml_info = await get_iflow_xml_text(integration_flow_id=integration_flow_id)
#         if not xml_info.get("ok"):
#             return {"ok": False, "step": "get-iflow-xml", "integration_flow_id": integration_flow_id, "error": xml_info.get("error")}

#         xml_text = xml_info.get("xml_text") or ""

#         # 2) Extract urlPath
#         url_path = _extract_sender_url_path_from_iflow_xml(xml_text)
#         if not url_path:
#             return {
#                 "ok": False,
#                 "step": "extract-urlPath",
#                 "integration_flow_id": integration_flow_id,
#                 "error": "Could not find sender urlPath in iFlow XML (no <key>urlPath</key>)",
#             }

#         # 3) Build runtime endpoint
#         endpoint_url = _build_runtime_http_endpoint(CPI_BASE_URL, url_path)

#         # 4) Auth selection
#         access_token: Optional[str] = None
#         if auth_mode == "bearer":
#             access_token = await TokenManager.get_runtime_token()

#         # 5) Call runtime
#         # NOTE: send_runtime_payload is POST-based in your current util
#         # If you want GET support, keep using your "call-cpi-iflow-runtime" wrapper.
#         method_u = (method or "POST").upper()

#         if method_u == "GET":
#             headers = {"Accept": "*/*"}
#             if auth_mode == "bearer" and access_token:
#                 headers["Authorization"] = f"Bearer {access_token}"

#             async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
#                 resp = await client.get(endpoint_url, headers=headers, params=(payload if isinstance(payload, dict) else None))

#             return {
#                 "ok": resp.status_code < 400,
#                 "step": "runtime_get",
#                 "integration_flow_id": integration_flow_id,
#                 "sender_urlPath": url_path,
#                 "endpoint_url": endpoint_url,
#                 "http_status": resp.status_code,
#                 "response_headers": dict(resp.headers),
#                 "response_body": resp.text,
#                 "auth_mode_used": auth_mode,
#             }

#         result = await send_runtime_payload(
#             endpoint_url=endpoint_url,
#             content_type=content_type,
#             payload=payload,
#             timeout_seconds=timeout_seconds,
#             auth_mode=auth_mode,
#             access_token=access_token,
#             use_csrf=use_csrf,
#             csrf_fetch_url=None,
#         )

#         return {
#             **result,
#             "integration_flow_id": integration_flow_id,
#             "sender_urlPath": url_path,
#             "endpoint_url": endpoint_url,
#         }

#     except Exception as e:
#         return {"ok": False, "step": "exception", "integration_flow_id": integration_flow_id, "error": str(e)}


# # -------------------------------------------------------------------
# # TOOL 6: get-integration-package (design-time)
# # -------------------------------------------------------------------


# @mcp.tool(name="find-package-by-id", description="Get an integration package by ID. Args: integration_package_id: Integration Package ID")
# async def get_an_integration_package(integration_package_id: str):

#     try:
#         results = await get_an_integration_package_tool(integration_package_id)
#         return results
#     except Exception as e:
#         print(f"===> Exception in get_an_integration_package: {e}")
#         raise

# # -------------------------------------------------------------------
# # TOOL 7: get-all-packages 
# # -------------------------------------------------------------------

# @mcp.tool(name="get-all-packages", description="Get all integration packages.")
# async def get_all_integration_package():

#     try:
#         results = await get_all_integration_package_tool()
#         return results
#     except Exception as e:
#         print(f"===> Exception in get_all_integration_package: {e}")
#         raise


# # -------------------------------------------------------------------
# # TOOL 8: get-all-iflow
# # -------------------------------------------------------------------
# @mcp.tool(name="get-all-iflow", description="Get all integration flows in an integration package. Args: integration_package_id: Integration Package ID, integration_flow_id: Integration Flow ID, version: 'active' or explicit version (e.g. 1.0.5)")
# async def get_an_integration_flow_of_an_integration_package(
#     integration_package_id: str,
#     integration_flow_id: str,
#     version: str = "active",
# ):

#     try:
#         results = await get_an_integration_flow_of_an_integration_package_tool(
#             integration_package_id,
#             integration_flow_id,
#             version,
#         )
#         return results
#     except Exception as e:
#         print(f"===> Exception in get_an_integration_flow_of_an_integration_package: {e}")
#         raise


# # -------------------------------------------------------------------
# # TOOL 9: get-iflow-configuration
# # -------------------------------------------------------------------
# @mcp.tool(name="get-iflow-configration", description="Get configuration parameters (key/value pairs) of an integration artifact by ID and version.")
# async def get_configuration_of_an_integration_flow(
#     integration_flow_id: str,
#     version: str = "active",
# ):

#     try:
#         results = await get_configuration_of_an_integration_flow_tool(integration_flow_id, version)
#         return results
#     except Exception as e:
#         print(f"===> Exception in get_configuration_of_an_integration_flow: {e}")
#         raise


# # -------------------------------------------------------------------
# # TOOL 10: verify-iflow-endpoint (HEAD request)
# # -------------------------------------------------------------------
# @mcp.tool(
#     name="verify-iflow-endpoint",
#     description="Verify if an iFlow endpoint is reachable (HEAD request). Supports none/bearer/basic."
# )
# async def verify_iflow_endpoint(
#     endpoint_url: str,
#     auth_mode: str = "none",   # none|bearer|basic
#     basic_user: Optional[str] = None,
#     basic_pass: Optional[str] = None,
# ) -> Dict[str, Any]:

#     normalized = ensure_runtime_rt_url(endpoint_url)

#     try:
#         headers = {}
#         req_auth = None

#         if auth_mode == "bearer":
#             access_token = await TokenManager.get_runtime_token()
#             headers["Authorization"] = f"Bearer {access_token}"

#         elif auth_mode == "basic":
#             if not basic_user or not basic_pass:
#                 return {"ok": False, "error": "basic_user/basic_pass required for auth_mode=basic"}
#             req_auth = (basic_user, basic_pass)

#         elif auth_mode == "none":
#             pass
#         else:
#             return {"ok": False, "error": f"Invalid auth_mode: {auth_mode}"}

#         async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
#             if req_auth is None:
#                 resp = await client.head(normalized, headers=headers)
#             else:
#                 resp = await client.head(normalized, headers=headers, auth=req_auth)


#         return {
#             "ok": resp.status_code < 400,
#             "status": resp.status_code,
#             "url_tested": normalized,
#             "auth_mode_used": auth_mode,
#             "reachable": resp.status_code in [200, 405],
#         }

#     except Exception as e:
#         return {"ok": False, "error": str(e), "url_tested": normalized, "auth_mode_used": auth_mode}

# # -------------------------------------------------------------------
# # PROMPTS (for client-side LLM usage)
# # -------------------------------------------------------------------

# @mcp.prompt(name="detect-sender-adapter",
#     description="Given CPI iFlow XML, detect the sender adapter type and return strict JSON."
# )
# def detect_sender_adapter_prompt(iflow_xml: str) -> str:
#     return f"""
# You are an SAP CPI expert.

# Task:
# From the iFlow XML, identify the SENDER adapter type.

# Return format (STRICT JSON):
# {{
#   "senderAdapter": "HTTPS" | "HTTP" | "SOAP" | "SFTP" | "IDOC" | "OData" | "Unknown",
#   "confidence": 0.0,
#   "evidence": "short reason"
# }}

# Rules:
# - Return ONLY valid JSON
# - Do NOT add extra keys
# - If unsure, return senderAdapter="Unknown"

# iFlow XML:
# {iflow_xml}
# """.strip()


# @mcp.prompt(name="generate-runtime-payload",
#     description="Given CPI iFlow XML, generate a strict JSON runtime test payload {contentType,payload}."
# )
# def generate_runtime_payload_prompt(iflow_xml: str) -> str:
#     return f"""
# You are an SAP CPI payload generator.

# Task:
# Generate a runtime test request payload for the iFlow.

# Return format (STRICT JSON):
# {{
#   "contentType": "application/json",
#   "payload": {{
#     "...": "..."
#   }}
# }}

# Rules:
# - MUST be valid JSON
# - payload MUST be an object (not a string)
# - If schema is unknown, return minimal safe payload

# iFlow XML:
# {iflow_xml}
# """.strip()


# @mcp.prompt(name="validate-runtime-payload",
#     description="Validate a generated runtime payload JSON and fix it to valid strict JSON if needed."
# )
# def validate_runtime_payload_prompt(payload_text: str) -> str:
#     return f"""
# You are a strict JSON validator.

# Input may be invalid JSON. Fix it and return ONLY strict valid JSON with format:

# {{
#   "contentType": "application/json",
#   "payload": {{ }}
# }}

# Input:
# {payload_text}
# """.strip()
# # -------------------------------------------------------------------

import os
import json
import zipfile
import re
import httpx
from typing import Optional, Any, Dict, Union
from fastmcp import FastMCP

# CPI Design-time tools (keep)
from _tool._get_an_integration_flow_zip_tool import get_an_integration_flow_zip_tool
from _tool._get_an_endpoint_of_an_integration_flow_tool import get_an_endpoint_of_an_integration_flow_tool

# ✅ CPI Runtime endpoints (official API-driven)
from _util.cpi_runtime_endpoints import fetch_runtime_endpoints, pick_best_http_endpoint

# ✅ Auth token manager for CPI APIs
from _util.token_manager import TokenManager

# ✅ Runtime sender (POST etc)
from _util.runtime_test import send_runtime_payload

# Local helper (keep)
from _util.int_suite_service import i_flow_path
from _tool._get_all_integration_package_tool import get_all_integration_package_tool
from _tool._get_an_integration_flow_of_an_integration_package_tool import (
    get_an_integration_flow_of_an_integration_package_tool,
)
from _tool._get_configration_of_an_intergrairon_flow_tool import (
    get_configuration_of_an_integration_flow_tool,
)
from _tool._get_an_integration_package_tool import get_an_integration_package_tool

mcp = FastMCP("iflow_test_mcp_server")

# -------------------------------------------------------------------
# Helper: safely decode bytes
# -------------------------------------------------------------------
def _decode_bytes(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except Exception:
            pass
    return data.decode("utf-8", errors="ignore")


def _find_iflow_xml_inside_zip(zip_path: str) -> Dict[str, Any]:
    """
    Best-effort extraction of the main iFlow model XML from the CPI artifact ZIP.
    NOTE: XML is ONLY used for analysis/payload generation - NOT for endpoint building.
    """
    if not zip_path or not os.path.exists(zip_path):
        return {"ok": False, "error": f"ZIP not found at path: {zip_path}"}

    candidates = []
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            names = z.namelist()

            # Common likely candidates
            for n in names:
                low = n.lower()
                if low.endswith(".iflw") or low.endswith(".iflmap"):
                    candidates.append(n)
                if low.endswith(".xml") and (
                    "iflow" in low or "integration" in low or "flow" in low
                ):
                    candidates.append(n)

            # fallback any xml
            if not candidates:
                candidates = [n for n in names if n.lower().endswith(".xml")]

            if not candidates:
                return {"ok": False, "error": "No XML found in ZIP artifact"}

            pick = candidates[0]
            raw = z.read(pick)
            return {
                "ok": True,
                "zip_path": zip_path,
                "file_name": pick,
                "xml_text": _decode_bytes(raw),
                "all_candidate_files": candidates[:20],
            }

    except Exception as e:
        return {"ok": False, "error": str(e)}


# -------------------------------------------------------------------
# TOOL 1: get-iflow (download zip)
# -------------------------------------------------------------------
@mcp.tool(name="get-iflow")
async def get_an_integration_flow_zip(
    integration_flow_id: str,
    version: str = "active",
):
    """
    Download an integration flow as ZIP file (design-time).
    Args:
        integration_flow_id: Integration Flow ID
        version: 'active' or explicit version (e.g. 1.0.5)
    """
    try:
        results = await get_an_integration_flow_zip_tool(integration_flow_id, version)
        return results
    except Exception as e:
        return {"ok": False, "error": str(e)}


# -------------------------------------------------------------------
# TOOL 2: get-iflow-xml (extract xml from downloaded zip)
# -------------------------------------------------------------------
@mcp.tool(name="get-iflow-xml")
async def get_iflow_xml_text(integration_flow_id: str, version: str = "active"):
    """
    Download the iFlow ZIP and extract the main iFlow XML/model as plain text.
    Args:
        integration_flow_id: iFlow Artifact ID
        version: 'active' or explicit version (e.g. 1.0.5)
    """
    try:
        # ensure ZIP exists locally
        await get_an_integration_flow_zip_tool(integration_flow_id, version)

        zip_path = i_flow_path(integration_flow_id)
        xml_info = _find_iflow_xml_inside_zip(zip_path)
        return xml_info

    except Exception as e:
        return {"ok": False, "error": str(e)}


# -------------------------------------------------------------------
# ✅ TOOL 3: get-deployed-endpoints-from-cpi
# -------------------------------------------------------------------
@mcp.tool(name="get-deployed-endpoints-from-cpi")
async def get_deployed_endpoints_from_cpi(iflow_id: str) -> Dict[str, Any]:
    """
    Fetch deployed runtime endpoints for an iFlow directly from CPI
    using IntegrationRuntimeArtifacts('<id>')/Endpoints.
    """
    api_base_url = os.getenv("API_BASE_URL", "").rstrip("/")
    if not api_base_url:
        return {"ok": False, "error": "API_BASE_URL env var is missing"}

    token = await TokenManager().get_token()
    return await fetch_runtime_endpoints(
        api_base_url=api_base_url, access_token=token, iflow_id=iflow_id
    )


# -------------------------------------------------------------------
# ✅ TOOL 4: test-iflow-runtime-by-id (NO URL BUILDING)
# -------------------------------------------------------------------
@mcp.tool(
    name="test-iflow-runtime-by-id",
    description="Fetch deployed endpoint from CPI IntegrationRuntimeArtifacts('<id>')/Endpoints and send payload."
)
async def test_iflow_runtime_by_id(
    integration_flow_id: str,
    payload: Union[dict, list, str],
    content_type: str = "application/json",
    method: str = "POST",
    timeout_seconds: float = 30.0,
    auth_mode: str = "auto",  # ✅ none | bearer | basic | auto
    basic_user: Optional[str] = None,
    basic_pass: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        api_base_url = os.getenv("API_BASE_URL", "").rstrip("/")
        if not api_base_url:
            return {"ok": False, "step": "config", "error": "API_BASE_URL env var is missing"}

        # 1) Fetch deployed endpoints via official API
        token = await TokenManager().get_token()

        ep_res = await fetch_runtime_endpoints(
            api_base_url=api_base_url,
            access_token=token,
            iflow_id=integration_flow_id,
            timeout_seconds=timeout_seconds,
        )

        if not ep_res.get("ok"):
            return {
                "ok": False,
                "step": "fetch_endpoints",
                "integration_flow_id": integration_flow_id,
                "details": ep_res,
            }

        endpoints = ep_res.get("endpoints", [])
        chosen = pick_best_http_endpoint(endpoints)

        if not chosen:
            return {
                "ok": False,
                "step": "choose_endpoint",
                "integration_flow_id": integration_flow_id,
                "error": "No deployed endpoints found (is iFlow deployed?)",
                "endpoints": endpoints,
            }

        endpoint_url = chosen.get("Url") or chosen.get("url")
        if not endpoint_url:
            return {"ok": False, "step": "endpoint_url_missing", "chosen": chosen}

        method_u = (method or "POST").upper()

        async def _do_call(_auth_mode: str) -> Dict[str, Any]:
            access_token: Optional[str] = None

            if _auth_mode == "bearer":
                access_token = await TokenManager.get_runtime_token()

            if method_u == "GET":
                headers = {"Accept": "*/*"}
                req_auth = None

                if _auth_mode == "bearer" and access_token:
                    headers["Authorization"] = f"Bearer {access_token}"
                elif _auth_mode == "basic":
                    if not basic_user or not basic_pass:
                        return {"ok": False, "error": "basic_user/basic_pass required for auth_mode=basic"}
                    req_auth = (basic_user, basic_pass)

                async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
                    resp = await client.get(
                        endpoint_url,
                        params=(payload if isinstance(payload, dict) else None),
                        headers=headers,
                        auth=req_auth,
                    )

                return {
                    "ok": resp.status_code < 400,
                    "http_status": resp.status_code,
                    "response_headers": dict(resp.headers),
                    "response_body": resp.text[:2000],
                    "auth_mode_used": _auth_mode,
                }

            # ✅ POST/PUT/PATCH/DELETE -> use your runtime util
            return await send_runtime_payload(
                endpoint_url=endpoint_url,
                content_type=content_type,
                payload=payload,
                timeout_seconds=timeout_seconds,
                method=method_u,         # ✅ FIX: respect GET/PUT/PATCH/DELETE too
                auth_mode=_auth_mode,
                basic_user=basic_user,
                basic_pass=basic_pass,
                access_token=access_token,
                use_csrf=False,          # ✅ IMPORTANT: runtime sender doesn't need CSRF
                csrf_fetch_url=None,
            )


        # ✅ AUTO mode: none -> bearer -> basic
        if auth_mode == "auto":
            res1 = await _do_call("none")
            if res1.get("ok"):
                return {
                    "ok": True,
                    "step": "runtime_call",
                    "integration_flow_id": integration_flow_id,
                    "endpoint_used": endpoint_url,
                    "endpoint_meta": chosen,
                    "runtime_response": res1,
                }

            res2 = await _do_call("bearer")
            if res2.get("ok"):
                return {
                    "ok": True,
                    "step": "runtime_call",
                    "integration_flow_id": integration_flow_id,
                    "endpoint_used": endpoint_url,
                    "endpoint_meta": chosen,
                    "runtime_response": res2,
                }

            if basic_user and basic_pass:
                res3 = await _do_call("basic")
                return {
                    "ok": bool(res3.get("ok", False)),
                    "step": "runtime_call",
                    "integration_flow_id": integration_flow_id,
                    "endpoint_used": endpoint_url,
                    "endpoint_meta": chosen,
                    "runtime_response": res3,
                }

            return {
                "ok": False,
                "step": "runtime_call",
                "integration_flow_id": integration_flow_id,
                "endpoint_used": endpoint_url,
                "endpoint_meta": chosen,
                "error": "AUTO auth failed. Tried none -> bearer -> basic(not provided).",
                "last_response": res2,
            }

        # ✅ Manual mode
        res = await _do_call(auth_mode)
        return {
            "ok": bool(res.get("ok", False)),
            "step": "runtime_call",
            "integration_flow_id": integration_flow_id,
            "endpoint_used": endpoint_url,
            "endpoint_meta": chosen,
            "runtime_response": res,
        }

    except Exception as e:
        return {
            "ok": False,
            "step": "exception",
            "integration_flow_id": integration_flow_id,
            "error": str(e),
        }

# -------------------------------------------------------------------
# TOOL 5: find-package-by-id (design-time)
# -------------------------------------------------------------------
@mcp.tool(
    name="find-package-by-id",
    description="Get an integration package by ID. Args: integration_package_id: Integration Package ID",
)
async def get_an_integration_package(integration_package_id: str):
    try:
        results = await get_an_integration_package_tool(integration_package_id)
        return results
    except Exception as e:
        return {"ok": False, "error": str(e)}


# -------------------------------------------------------------------
# TOOL 6: get-all-packages
# -------------------------------------------------------------------
@mcp.tool(name="get-all-packages", description="Get all integration packages.")
async def get_all_integration_package():
    try:
        results = await get_all_integration_package_tool()
        return results
    except Exception as e:
        return {"ok": False, "error": str(e)}


# -------------------------------------------------------------------
# TOOL 7: get-all-iflow (by package)
# -------------------------------------------------------------------
@mcp.tool(
    name="get-all-iflow",
    description="Get all integration flows in an integration package. Args: integration_package_id: Integration Package ID",
)
async def get_an_integration_flow_of_an_integration_package(
    integration_package_id: str,
):
    try:
        results = await get_an_integration_flow_of_an_integration_package_tool(
            integration_package_id
        )
        return results
    except Exception as e:
        return {"ok": False, "error": str(e)}


# -------------------------------------------------------------------
# TOOL 8: get-iflow-configuration
# -------------------------------------------------------------------
@mcp.tool(
    name="get-iflow-configration",
    description="Get configuration parameters (key/value pairs) of an integration artifact by ID and version.",
)
async def get_configuration_of_an_integration_flow(
    integration_flow_id: str,
    version: str = "active",
):
    try:
        results = await get_configuration_of_an_integration_flow_tool(integration_flow_id, version)
        return results
    except Exception as e:
        return {"ok": False, "error": str(e)}


# -------------------------------------------------------------------
# TOOL 9: verify-iflow-endpoint (HEAD request)
# -------------------------------------------------------------------
@mcp.tool(
    name="verify-iflow-endpoint",
    description="Verify if an iFlow endpoint is reachable (HEAD request). Does not modify URL.",
)
async def verify_iflow_endpoint(
    endpoint_url: str,
) -> Dict[str, Any]:
    """
    ✅ Verifies endpoint directly (no runtime URL guessing).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.head(endpoint_url, headers={"Accept": "*/*"})

        return {
            "ok": resp.status_code < 400,
            "status": resp.status_code,
            "url_tested": endpoint_url,
            "reachable": resp.status_code in [200, 405],
        }

    except Exception as e:
        return {"ok": False, "error": str(e), "url_tested": endpoint_url}


# -------------------------------------------------------------------
# PROMPTS (for client-side LLM usage)
# -------------------------------------------------------------------
@mcp.prompt(
    name="detect-sender-adapter",
    description="Given CPI iFlow XML, detect the sender adapter type and return strict JSON.",
)
def detect_sender_adapter_prompt(iflow_xml: str) -> str:
    return f"""
You are an SAP CPI expert.

Task:
From the iFlow XML, identify the SENDER adapter type.

Return format (STRICT JSON):
{{
  "senderAdapter": "HTTPS" | "HTTP" | "SOAP" | "SFTP" | "IDOC" | "OData" | "Unknown",
  "confidence": 0.0,
  "evidence": "short reason"
}}

Rules:
- Return ONLY valid JSON
- Do NOT add extra keys
- If unsure, return senderAdapter="Unknown"

iFlow XML:
{iflow_xml}
""".strip()


@mcp.prompt(
    name="generate-runtime-payload",
    description="Given CPI iFlow XML, generate a strict JSON runtime test payload {contentType,payload}.",
)
def generate_runtime_payload_prompt(iflow_xml: str) -> str:
    return f"""
You are an SAP CPI payload generator.

Task:
Generate a runtime test request payload for the iFlow.

Return format (STRICT JSON):
{{
  "contentType": "application/json",
  "payload": {{
    "...": "..."
  }}
}}

Rules:
- MUST be valid JSON
- payload MUST be an object (not a string)
- If schema is unknown, return minimal safe payload

iFlow XML:
{iflow_xml}
""".strip()


@mcp.prompt(
    name="validate-runtime-payload",
    description="Validate a generated runtime payload JSON and fix it to valid strict JSON if needed.",
)
def validate_runtime_payload_prompt(payload_text: str) -> str:
    return f"""
You are a strict JSON validator.

Input may be invalid JSON. Fix it and return ONLY strict valid JSON with format:

{{
  "contentType": "application/json",
  "payload": {{ }}
}}

Input:
{payload_text}
""".strip()


# -------------------------------------------------------------------
# ✅ Optional E2E tool: run-iflow-e2e
# -------------------------------------------------------------------
def _odata_list(data: Any) -> list:
    """
    Normalize CPI OData response into a python list of dicts.

    Supports:
      - {"d":{"results":[...]}}
      - {"value":[...]}
      - already-list
      - otherwise []
    """
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        d = data.get("d")
        if isinstance(d, dict):
            res = d.get("results")
            if isinstance(res, list):
                return res

        val = data.get("value")
        if isinstance(val, list):
            return val

    return []



@mcp.tool(
    name="test-iflow-by-package-and-name",
    description="Find iFlow inside a package and test it by sending sample payload to deployed runtime endpoint."
)
async def test_iflow_by_package_and_name(
    integration_package_id: str,
    integration_flow_id: str,
    payload: Union[dict, list, str],
    content_type: str = "application/json",
    method: str = "POST",
    timeout_seconds: float = 30.0,
    auth_mode: str = "auto",
    basic_user: Optional[str] = None,
    basic_pass: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        api_base_url = os.getenv("API_BASE_URL", "").rstrip("/")
        if not api_base_url:
            return {"ok": False, "step": "config", "error": "API_BASE_URL env var is missing"}

        # 1) Validate iFlow exists in the package (design-time)
        iflows_res = await get_an_integration_flow_of_an_integration_package_tool(
            integration_package_id
        )

        # normalize list
        iflows = []
        if isinstance(iflows_res, dict):
            iflows = (
                iflows_res.get("d", {}).get("results")
                or iflows_res.get("results")
                or iflows_res.get("iflows")
                or []
            )

        found = None
        for x in iflows:
            if not isinstance(x, dict):
                continue
            # CPI often uses "Id" key
            if (x.get("Id") or x.get("id")) == integration_flow_id:
                found = x
                break

        if not found:
            return {
                "ok": False,
                "step": "validate_iflow_in_package",
                "error": f"iFlow '{integration_flow_id}' not found in package '{integration_package_id}'",
                "available_ids": [i.get("Id") for i in iflows if isinstance(i, dict) and i.get("Id")][:50],
            }

        # 2) Fetch deployed endpoints (runtime API)
        token = await TokenManager().get_token()
        ep_res = await fetch_runtime_endpoints(
            api_base_url=api_base_url,
            access_token=token,
            iflow_id=integration_flow_id,
            timeout_seconds=timeout_seconds,
        )

        if not ep_res.get("ok"):
            return {
                "ok": False,
                "step": "fetch_endpoints",
                "integration_flow_id": integration_flow_id,
                "details": ep_res,
            }

        endpoints = ep_res.get("endpoints", [])
        chosen = pick_best_http_endpoint(endpoints)
        if not chosen:
            return {
                "ok": False,
                "step": "choose_endpoint",
                "error": "No deployed endpoints found (is iFlow deployed?)",
                "integration_flow_id": integration_flow_id,
                "endpoints": endpoints,
            }

        endpoint_url = chosen.get("Url") or chosen.get("url")
        if not endpoint_url:
            return {"ok": False, "step": "endpoint_url_missing", "chosen": chosen}

        # 3) Call runtime
        # We reuse your existing Tool 4 logic by calling it directly:
        runtime_result = await test_iflow_runtime_by_id(
            integration_flow_id=integration_flow_id,
            payload=payload,
            content_type=content_type,
            method=method,
            timeout_seconds=timeout_seconds,
            auth_mode=auth_mode,
            basic_user=basic_user,
            basic_pass=basic_pass,
        )

        return {
            "ok": bool(runtime_result.get("ok", False)),
            "step": "done",
            "package_id": integration_package_id,
            "iflow_id": integration_flow_id,
            "iflow_meta": found,
            "endpoint_used": endpoint_url,
            "runtime_result": runtime_result,
        }

    except Exception as e:
        return {"ok": False, "step": "exception", "error": str(e)}
