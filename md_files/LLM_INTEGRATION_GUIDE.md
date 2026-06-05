# LLM Integration Guide for Sample Payload Generation

## Overview

This guide explains how to integrate LLM-based payload generation with the MCP server for testing SAP Cloud Platform Integration (CPI) flows. The new approach leverages the LLM's capabilities to dynamically generate appropriate sample payloads based on integration flow analysis.

## Problem Statement

The original [`_test_iflow_with_sample_payload_tool.py`](/_tool/_test_iflow_with_sample_payload_tool.py) uses hardcoded sample payloads that don't adapt to different adapter types (SOAP, REST, IDoc, SFTP, JMS, RFC, etc.). This causes issues when testing integration flows that require specific payload formats.

## Solution: LLM-Powered Dynamic Payload Generation

### New Tool: [`generate_sample_payload_with_llm`](/_tool/_generate_sample_payload_with_llm.py)

The new tool performs the following steps:

1. **Retrieves Integration Flow Metadata**
   - Gets endpoint URL with entry points
   - Downloads integration flow configuration
   - Downloads integration flow zip file

2. **Analyzes Integration Flow Structure**
   - Extracts and examines zip file contents
   - Identifies adapter type (SOAP, REST, IDoc, SFTP, JMS, RFC, etc.)
   - Detects schemas (WSDL, OpenAPI, XSD, JSON)
   - Extracts configuration hints

3. **Generates LLM Prompt**
   - Creates comprehensive prompt with:
     - Integration flow ID
     - Detected adapter type
     - Configuration parameters
     - File structure analysis
     - Schema information

4. **Calls LLM for Payload Generation**
   - Sends prompt to LLM
   - Receives appropriate sample payload
   - Validates payload format

5. **Tests Integration Flow**
   - Gets CSRF token
   - Sends LLM-generated payload
   - Returns response

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM-Based Client                          │
│              (Copilot, Cline, Roo, etc.)                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  generate_sample_payload_with_llm                     │  │
│  │  (New Tool)                                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. Get endpoint URL & configuration                 │  │
│  │  2. Download integration flow zip                    │  │
│  │  3. Analyze flow structure                           │  │
│  │  4. Generate LLM prompt                              │  │
│  │  5. Call LLM API (or use smart defaults)             │  │
│  │  6. Test with generated payload                      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Integration with LLM-Based Clients

### For Copilot/Cline/Roo Users

When using the MCP server with LLM-based clients, the client can:

1. **Call the new tool directly:**
   ```
   generate_sample_payload_with_llm(integration_flow_id="my-flow", version="active")
   ```

2. **Use the tool in a workflow:**
   ```
   Step 1: Get integration flow details
   Step 2: Analyze the flow structure
   Step 3: Generate appropriate sample payload
   Step 4: Test the integration flow
   ```

3. **Leverage LLM reasoning:**
   - The LLM can analyze the integration flow configuration
   - It can understand adapter-specific requirements
   - It can generate payloads that match the expected format

### Example Usage

#### Scenario 1: Testing a SOAP-based Integration Flow

**User Request:**
```
Test the integration flow "SalesOrderToSAP" with a sample payload
```

**LLM Analysis:**
1. Calls `generate_sample_payload_with_llm("SalesOrderToSAP")`
2. Receives analysis showing:
   - Adapter Type: SOAP
   - Has WSDL: true
   - WSDL content available
3. Generates appropriate SOAP XML payload:
   ```xml
   <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
     <soap:Body>
       <SalesOrder>
         <OrderNumber>12345</OrderNumber>
         <Customer>Test Customer</Customer>
         <Items>
           <Item>
             <Product>PROD-001</Product>
             <Quantity>10</Quantity>
           </Item>
         </Items>
       </SalesOrder>
     </soap:Body>
   </soap:Envelope>
   ```

#### Scenario 2: Testing a REST-based Integration Flow

**User Request:**
```
Test the integration flow "OrderAPI" with a sample payload
```

**LLM Analysis:**
1. Calls `generate_sample_payload_with_llm("OrderAPI")`
2. Receives analysis showing:
   - Adapter Type: REST
   - Has OpenAPI: true
   - OpenAPI specification available
3. Generates appropriate JSON payload:
   ```json
   {
     "orderId": "ORD-2024-001",
     "customer": {
       "id": "CUST-123",
       "name": "John Doe"
     },
     "items": [
       {
         "productId": "PROD-001",
         "quantity": 5,
         "price": 99.99
       }
     ],
     "totalAmount": 499.95
   }
   ```

#### Scenario 3: Testing an IDoc-based Integration Flow

**User Request:**
```
Test the integration flow "IDocORDERS05" with a sample payload
```

**LLM Analysis:**
1. Calls `generate_sample_payload_with_llm("IDocORDERS05")`
2. Receives analysis showing:
   - Adapter Type: IDoc
   - Has XML Schema: true
   - IDoc structure detected
3. Generates appropriate IDoc XML payload:
   ```xml
   <?xml version="1.0"?>
   <IDOC>
     <E1EDK03>
       <MSGFN>004</MSGFN>
       <DOCNUM>000000123456</DOCNUM>
       <TEST>ORDERS05 Test</TEST>
     </E1EDK03>
     <E1EDP01>
       <POSEX>000010</POSEX>
       <MENGE>10.000</MENGE>
       <VRKME>ST</VRKME>
     </E1EDP01>
   </IDOC>
   ```

## Implementation Details

### Smart Default Generation

When LLM API is not available, the tool uses smart defaults based on adapter type:

```python
if adapter_type == 'SOAP':
    # Generate XML payload for SOAP
    return {"message": "<soap:Envelope>...</soap:Envelope>"}

elif adapter_type == 'REST':
    # Generate JSON payload for REST
    return {"id": "12345", "message": "Test..."}

elif adapter_type == 'IDoc':
    # Generate IDoc XML payload
    return {"message": "<?xml version='1.0'?><IDOC>...</IDOC>"}

# ... and so on for other adapter types
```

### Integration Flow Analysis

The tool analyzes the integration flow zip file to detect:

1. **Adapter Type Indicators:**
   - SOAP: `.wsdl` files, "soap" in filenames
   - REST: OpenAPI/Swagger files, `.json`/`.yaml` files
   - IDoc: "idoc" in filenames, `.xsd` files
   - File: "sftp", "ftp", "file" in filenames
   - JMS: "jms", "queue", "topic" in filenames
   - RFC: "rfc", "bapi" in filenames

2. **Schema Detection:**
   - WSDL files for SOAP
   - OpenAPI/Swagger files for REST
   - XSD files for XML schemas
   - JSON schema files

3. **Configuration Hints:**
   - `.properties` files
   - `.cfg` files
   - Configuration files

### LLM Prompt Structure

The tool generates a comprehensive prompt for the LLM:

```
You are an expert in SAP Cloud Platform Integration (CPI)...

**Integration Flow Details:**
- Integration Flow ID: {id}
- Adapter Type: {type}
- Has WSDL: {true/false}
- Has OpenAPI: {true/false}
- ...

**Configuration Parameters:**
{config_data}

**File Structure Analysis:**
{file_list}

**Instructions:**
1. Analyze the adapter type and configuration
2. Generate a sample payload that matches requirements
3. For SOAP/XML adapters, generate valid XML
4. For REST/JSON adapters, generate valid JSON
5. ...
6. Return ONLY the JSON payload (no additional text)
```

## Benefits

1. **Dynamic Generation:** Payloads are generated based on actual integration flow structure
2. **Adapter-Specific:** Different adapter types get appropriate payload formats
3. **Schema-Aware:** Can use WSDL, OpenAPI, XSD schemas when available
4. **LLM-Powered:** Leverages LLM's understanding of integration patterns
5. **Fallback Mechanism:** Smart defaults when LLM is unavailable
6. **Testable:** Generates payloads that can be immediately tested

## Future Enhancements

### 1. Full LLM Integration

To use actual LLM API (OpenAI, Anthropic, etc.):

```python
import openai

async def generate_payload_with_llm(...):
    # ... analysis code ...
    
    # Call actual LLM API
    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert in SAP CPI..."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    # Parse LLM response
    payload = parse_llm_response(response.choices[0].message.content)
    return payload
```

### 2. Schema Validation

Add schema validation to ensure generated payloads match expected formats:

```python
def validate_payload_against_schema(payload, schema):
    # Validate XML against XSD
    # Validate JSON against JSON Schema
    # Return validation errors if any
```

### 3. Multiple Payload Examples

Generate multiple sample payloads for comprehensive testing:

```python
async def generate_multiple_payloads(...):
    # Generate success case
    # Generate error case
    # Generate edge cases
    # Return all payloads
```

### 4. Payload Templates

Create reusable templates for common integration patterns:

```python
TEMPLATES = {
    "sales_order": {...},
    "customer_update": {...},
    "inventory_sync": {...}
}
```

## Testing the New Tool

### Test 1: SOAP Integration Flow

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

### Test 2: REST Integration Flow

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

### Test 3: IDoc Integration Flow

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

## Comparison: Old vs New Approach

| Aspect | Old Approach | New Approach |
|--------|-------------|--------------|
| **Payload Generation** | Hardcoded JSON | Dynamic based on adapter type |
| **Adapter Support** | Generic only | SOAP, REST, IDoc, SFTP, JMS, RFC, etc. |
| **Schema Awareness** | None | WSDL, OpenAPI, XSD, JSON Schema |
| **LLM Integration** | None | LLM-powered generation |
| **Flexibility** | Low | High |
| **Test Coverage** | Limited | Comprehensive |
| **Maintenance** | Manual updates | Automatic adaptation |

## Conclusion

The new [`generate_sample_payload_with_llm`](/_tool/_generate_sample_payload_with_llm.py) tool provides a flexible, LLM-powered approach to generating sample payloads for testing integration flows. It:

1. **Analyzes** the integration flow structure
2. **Detects** adapter types and schemas
3. **Generates** appropriate payloads using LLM or smart defaults
4. **Tests** the integration flow with the generated payload

This approach ensures that payloads are always appropriate for the specific integration flow, regardless of the adapter type or complexity.

## Next Steps

1. **Integrate with LLM API:** Add actual LLM API calls for dynamic generation
2. **Add Schema Validation:** Validate generated payloads against schemas
3. **Create Templates:** Build reusable payload templates for common patterns
4. **Enhance Analysis:** Improve integration flow analysis capabilities
5. **Add Logging:** Add detailed logging for debugging and monitoring
6. **Create Tests:** Write comprehensive tests for different adapter types

## References

- [SAP Cloud Platform Integration Documentation](https://help.sap.com/viewer/product/CLOUD_INTEGRATION/Cloud/en-US)
- [MCP Server Documentation](https://modelcontextprotocol.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference)
