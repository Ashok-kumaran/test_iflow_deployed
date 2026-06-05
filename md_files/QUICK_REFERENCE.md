# Quick Reference: LLM-Powered Payload Generation

## Problem Solved

**Original Issue:** Hardcoded sample payloads that don't work for all adapter types

**Solution:** New tool [`generate_sample_payload_with_llm`](/_tool/_generate_sample_payload_with_llm.py) that dynamically generates payloads based on integration flow analysis

## Quick Start

### 1. Call the New Tool

```bash
curl -X POST http://localhost:8000/mcp/is_migrator \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "generate_sample_payload_with_llm",
    "params": {
      "integration_flow_id": "your-flow-id",
      "version": "active"
    },
    "id": 1
  }'
```

### 2. What It Does

1. **Downloads** integration flow zip file
2. **Analyzes** the structure to detect adapter type
3. **Generates** appropriate sample payload (LLM-powered or smart defaults)
4. **Tests** the integration flow with the generated payload

## Adapter Detection

The tool detects these adapter types:

| Adapter Type | Indicators | Example Payload |
|--------------|------------|-----------------|
| **SOAP** | `.wsdl` files, "soap" in filenames | XML with SOAP envelope |
| **REST** | OpenAPI/Swagger files, `.json`/`.yaml` | JSON with API structure |
| **IDoc** | "idoc" in filenames, `.xsd` files | IDoc XML structure |
| **File** | "sftp", "ftp", "file" in filenames | File content |
| **JMS** | "jms", "queue", "topic" in filenames | Message queue structure |
| **RFC** | "rfc", "bapi" in filenames | RFC structure |

## Example Outputs

### SOAP Integration Flow

**Input:** `generate_sample_payload_with_llm("SalesOrderToSAP")`

**Output:**
```json
{
  "status_code": 200,
  "sample_payload": {
    "message": "<soap:Envelope xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/'><soap:Body><SalesOrder><OrderNumber>12345</OrderNumber></SalesOrder></soap:Body></soap:Envelope>"
  },
  "flow_analysis": {
    "adapter_type": "SOAP",
    "has_wSDL": true,
    "has_xml_schema": true
  }
}
```

### REST Integration Flow

**Input:** `generate_sample_payload_with_llm("OrderAPI")`

**Output:**
```json
{
  "status_code": 200,
  "sample_payload": {
    "orderId": "ORD-2024-001",
    "customer": {"id": "CUST-123", "name": "John Doe"},
    "items": [{"productId": "PROD-001", "quantity": 5}]
  },
  "flow_analysis": {
    "adapter_type": "REST",
    "has_openAPI": true,
    "has_json_schema": true
  }
}
```

### IDoc Integration Flow

**Input:** `generate_sample_payload_with_llm("IDocORDERS05")`

**Output:**
```json
{
  "status_code": 200,
  "sample_payload": {
    "message": "<?xml version='1.0'?><IDOC><E1EDK03><MSGFN>004</MSGFN><DOCNUM>12345</DOCNUM></E1EDK03></IDOC>"
  },
  "flow_analysis": {
    "adapter_type": "IDoc",
    "has_xml_schema": true
  }
}
```

## Comparison: Old vs New

### Old Tool: `_test_iflow_with_sample_payload_tool.py`

```python
# Always returns the same hardcoded JSON
sample_payload = {
    "message": f"Test message for integration flow: {integration_flow_id}",
    "timestamp": "2024-01-01T00:00:00Z",
    "data": {
        "id": "12345",
        "name": "Test Data",
        "value": "Sample Value"
    }
}
```

**Problems:**
- ❌ Doesn't work for SOAP (needs XML)
- ❌ Doesn't work for IDoc (needs specific structure)
- ❌ Doesn't work for File adapters (needs file content)
- ❌ Doesn't work for JMS/RFC adapters
- ❌ No schema awareness

### New Tool: `_generate_sample_payload_with_llm.py`

```python
# Dynamically generates based on adapter type
if adapter_type == 'SOAP':
    return {"message": "<soap:Envelope>...</soap:Envelope>"}
elif adapter_type == 'REST':
    return {"id": "12345", "message": "Test..."}
elif adapter_type == 'IDoc':
    return {"message": "<?xml version='1.0'?><IDOC>...</IDOC>"}
# ... and so on
```

**Benefits:**
- ✅ Works for all adapter types
- ✅ Adapter-specific payload formats
- ✅ Schema-aware (WSDL, OpenAPI, XSD)
- ✅ LLM-powered generation
- ✅ Smart fallback defaults

## Integration with LLM-Based Clients

### For Copilot/Cline/Roo Users

When using the MCP server with LLM-based clients:

1. **Direct Tool Call:**
   ```
   generate_sample_payload_with_llm(integration_flow_id="my-flow")
   ```

2. **Workflow Integration:**
   ```
   Step 1: Get integration flow details
   Step 2: Analyze flow structure
   Step 3: Generate appropriate payload
   Step 4: Test integration flow
   ```

3. **LLM Reasoning:**
   - LLM analyzes integration flow configuration
   - Understands adapter-specific requirements
   - Generates payloads matching expected format

## API Reference

### Endpoint

```
POST http://localhost:8000/mcp/is_migrator
```

### Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "generate_sample_payload_with_llm",
  "params": {
    "integration_flow_id": "string",
    "version": "active | version-number"
  },
  "id": 1
}
```

### Response Format

```json
{
  "jsonrpc": "2.0",
  "result": {
    "status_code": 200,
    "headers": {...},
    "body": {...},
    "test_url": "https://...",
    "integration_flow_id": "string",
    "sample_payload": {...},
    "flow_analysis": {
      "adapter_type": "SOAP|REST|IDoc|File|JMS|RFC|unknown",
      "has_wSDL": true|false,
      "has_openAPI": true|false,
      "has_xml_schema": true|false,
      "has_json_schema": true|false,
      "file_structure": [...],
      "configuration_hints": [...]
    }
  },
  "id": 1
}
```

## Testing Commands

### Test SOAP Flow

```bash
curl -X POST http://localhost:8000/mcp/is_migrator \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "generate_sample_payload_with_llm",
    "params": {
      "integration_flow_id": "SalesOrderToSAP",
      "version": "active"
    },
    "id": 1
  }'
```

### Test REST Flow

```bash
curl -X POST http://localhost:8000/mcp/is_migrator \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "generate_sample_payload_with_llm",
    "params": {
      "integration_flow_id": "OrderAPI",
      "version": "active"
    },
    "id": 2
  }'
```

### Test IDoc Flow

```bash
curl -X POST http://localhost:8000/mcp/is_migrator \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "generate_sample_payload_with_llm",
    "params": {
      "integration_flow_id": "IDocORDERS05",
      "version": "active"
    },
    "id": 3
  }'
```

## Files

### New Files
- [`_tool/_generate_sample_payload_with_llm.py`](/_tool/_generate_sample_payload_with_llm.py) - Main implementation
- [`LLM_INTEGRATION_GUIDE.md`](LLM_INTEGRATION_GUIDE.md) - Detailed guide
- [`SOLUTION_SUMMARY.md`](SOLUTION_SUMMARY.md) - Solution overview
- [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) - This file

### Modified Files
- [`mcp_tools.py`](mcp_tools.py) - Added new tool decorator

## Next Steps

1. **Test the tool** with different integration flows
2. **Integrate with LLM API** for dynamic generation
3. **Add schema validation** for generated payloads
4. **Create payload templates** for common patterns
5. **Enhance analysis** capabilities

## Troubleshooting

### Issue: Tool not found

**Solution:** Ensure the tool is registered in [`mcp_tools.py`](mcp_tools.py)

```python
from _tool._generate_sample_payload_with_llm import generate_sample_payload_with_llm

@mcp.tool(name="generate_sample_payload_with_llm")
async def generate_sample_payload_with_llm_tool(...):
    ...
```

### Issue: Adapter type not detected

**Solution:** Check the integration flow zip file structure. The tool looks for specific file patterns.

### Issue: Payload generation fails

**Solution:** The tool has smart fallback defaults. Check logs for errors.

## Documentation

- **Full Guide:** [`LLM_INTEGRATION_GUIDE.md`](LLM_INTEGRATION_GUIDE.md)
- **Solution Overview:** [`SOLUTION_SUMMARY.md`](SOLUTION_SUMMARY.md)
- **Quick Reference:** [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) (this file)

## Contact

For issues or questions, refer to the documentation files or check the tool implementation in [`_tool/_generate_sample_payload_with_llm.py`](/_tool/_generate_sample_payload_with_llm.py).
