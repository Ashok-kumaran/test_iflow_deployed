# User Payload Guide

This guide explains what kind of payloads users can provide to the [`test_iflow_with_user_payload`](/_tool/_test_iflow_with_user_payload_tool.py) tool.

## Overview

The [`test_iflow_with_user_payload`](/_tool/_test_iflow_with_user_payload_tool.py) tool accepts **any JSON payload** that the user wants to test. The tool doesn't validate or transform the payload - it sends it as-is to the integration flow endpoint.

## Payload Types by Adapter

### 1. SOAP Adapter (XML Payloads)

**Example 1: Simple SOAP Request**
```json
{
  "message": "<soap:Envelope xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/'><soap:Body><SalesOrder><OrderNumber>12345</OrderNumber><Customer>Test Customer</Customer></SalesOrder></soap:Body></soap:Envelope>"
}
```

**Example 2: Complex SOAP Request**
```json
{
  "message": "<?xml version='1.0'?><soap:Envelope xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/' xmlns:ns='http://example.com/service'><soap:Body><ns:CreateOrder><OrderHeader><OrderNumber>ORD-001</OrderNumber><OrderDate>2024-01-01</OrderDate></OrderHeader><OrderItems><Item><ProductCode>PROD-001</ProductCode><Quantity>10</Quantity><Price>99.99</Price></Item></OrderItems></ns:CreateOrder></soap:Body></soap:Envelope>"
}
```

**Example 3: SOAP with Headers**
```json
{
  "message": "<soap:Envelope xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/'><soap:Header><Security><UsernameToken><Username>testuser</Username><Password>testpass</Password></UsernameToken></Security></soap:Header><soap:Body><TestRequest><Data>Test</Data></TestRequest></soap:Body></soap:Envelope>"
}
```

### 2. REST Adapter (JSON Payloads)

**Example 1: Simple JSON Request**
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

**Example 2: Complex JSON with Nested Objects**
```json
{
  "transactionId": "TXN-123456789",
  "timestamp": "2024-01-01T12:00:00Z",
  "sourceSystem": "ERP",
  "targetSystem": "CRM",
  "payload": {
    "customer": {
      "personalInfo": {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com"
      },
      "address": {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zipCode": "10001"
      }
    },
    "orders": [
      {
        "orderNumber": "ORD-001",
        "status": "PENDING",
        "lineItems": [
          {
            "sku": "SKU-001",
            "quantity": 2,
            "unitPrice": 49.99
          }
        ]
      }
    ]
  }
}
```

**Example 3: Minimal JSON**
```json
{
  "id": "123",
  "name": "Test"
}
```

### 3. IDoc Adapter (XML Payloads)

**Example 1: ORDERS05 IDoc**
```json
{
  "message": "<?xml version='1.0'?><IDOC><E1EDK03><MSGFN>004</MSGFN><DOCNUM>000000123456</DOCNUM><TEST>ORDERS05 Test</TEST></E1EDK03><E1EDP01><POSEX>000010</POSEX><MENGE>10.000</MENGE><VRKME>ST</VRKME></E1EDP01></IDOC>"
}
```

**Example 2: MATMAS IDoc**
```json
{
  "message": "<?xml version='1.0'?><IDOC><E1MARAM><MSGFN>004</MSGFN><MATNR>000000000000001234</MATNR><MTART>FERT</MTART><MBRSH>M</MBRSH><MEINS>ST</MEINS></E1MARAM></IDOC>"
}
```

**Example 3: Custom IDoc Structure**
```json
{
  "message": "<?xml version='1.0'?><IDOC><E1HEADER><DOCNUM>123456</DOCNUM><DOCTYPE>ORDERS</DOCTYPE></E1HEADER><E1ITEMS><ITEM><POSEX>0010</POSEX><MATNR>PROD-001</MATNR><MENGE>10</MENGE></ITEM></E1ITEMS></IDOC>"
}
```

### 4. File Adapter (File Content)

**Example 1: CSV File**
```json
{
  "message": "OrderID,CustomerID,ProductID,Quantity,Price\nORD-001,CUST-001,PROD-001,10,99.99\nORD-002,CUST-002,PROD-002,5,149.99"
}
```

**Example 2: Plain Text File**
```json
{
  "message": "Order Processing Report\n========================\nDate: 2024-01-01\nTotal Orders: 2\nTotal Amount: $1249.85\n\nOrder 1: ORD-001 - $999.90\nOrder 2: ORD-002 - $249.95"
}
```

**Example 3: JSON File**
```json
{
  "message": "{\"orders\": [{\"orderId\": \"ORD-001\", \"amount\": 999.90}, {\"orderId\": \"ORD-002\", \"amount\": 249.95}]}"
}
```

### 5. JMS Adapter (Message Queue Structure)

**Example 1: Simple JMS Message**
```json
{
  "message": "Test JMS message for queue processing",
  "properties": {
    "messageId": "MSG-12345",
    "timestamp": "2024-01-01T12:00:00Z",
    "correlationId": "CORR-001",
    "priority": 5
  },
  "body": {
    "data": "Sample payload for JMS processing"
  }
}
```

**Example 2: Complex JMS Message**
```json
{
  "message": "Order processing message",
  "properties": {
    "messageId": "MSG-98765",
    "timestamp": "2024-01-01T12:00:00Z",
    "correlationId": "CORR-002",
    "priority": 9,
    "JMSDeliveryMode": "PERSISTENT",
    "JMSType": "OrderMessage"
  },
  "body": {
    "order": {
      "orderId": "ORD-001",
      "customer": "CUST-123",
      "items": [
        {"sku": "SKU-001", "qty": 2}
      ]
    }
  }
}
```

### 6. RFC Adapter (RFC Structure)

**Example 1: Simple RFC Call**
```json
{
  "message": "Test RFC call",
  "function": "BAPI_SALESORDER_CREATE",
  "parameters": {
    "IMPORTING": {
      "ORDER_HEADER": {
        "DOC_TYPE": "OR",
        "SALES_ORG": "1000",
        "DISTR_CHAN": "10",
        "DIVISION": "00"
      }
    },
    "EXPORTING": {
      "SALESDOCUMENT": "1234567890"
    }
  }
}
```

**Example 2: Complex RFC Call**
```json
{
  "message": "Material master creation",
  "function": "BAPI_MATERIAL_SAVEDATA",
  "parameters": {
    "IMPORTING": {
      "HEADDATA": {
        "MATERIAL": "000000000000001234",
        "IND_SECTOR": "M",
        "MATERIAL_TYPE": "FERT",
        "BASE_UOM": "ST"
      }
    },
    "EXPORTING": {
      "RETURN": {
        "TYPE": "S",
        "CODE": "000",
        "MESSAGE": "Material created successfully"
      }
    }
  }
}
```

### 7. Generic/Unknown Adapter (JSON Payloads)

**Example 1: Simple Generic Payload**
```json
{
  "message": "Test message for integration flow",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "12345",
    "name": "Test Data",
    "value": "Sample Value"
  }
}
```

**Example 2: Complex Generic Payload**
```json
{
  "message": "Complex test data",
  "metadata": {
    "source": "Test System",
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0"
  },
  "payload": {
    "records": [
      {
        "id": "REC-001",
        "type": "ORDER",
        "data": {
          "orderNumber": "ORD-001",
          "customer": "CUST-123",
          "amount": 999.90
        }
      },
      {
        "id": "REC-002",
        "type": "INVOICE",
        "data": {
          "invoiceNumber": "INV-001",
          "customer": "CUST-123",
          "amount": 999.90
        }
      }
    ]
  }
}
```

## Payload Guidelines

### 1. JSON Structure
- Payload must be valid JSON
- Can be a simple object or complex nested structure
- Can include XML strings as values (for SOAP/IDoc adapters)

### 2. Data Types
- **Strings:** For text data, XML payloads, file content
- **Numbers:** For quantities, prices, IDs
- **Booleans:** For flags, status indicators
- **Arrays:** For lists of items, records
- **Objects:** For nested structures

### 3. Size Considerations
- Small payloads (< 1KB): Ideal for testing
- Medium payloads (1KB - 10KB): Acceptable
- Large payloads (> 10KB): May cause performance issues

### 4. Content Guidelines
- **For SOAP:** Include SOAP envelope with proper namespaces
- **For IDoc:** Include IDoc structure with proper segments
- **For REST:** Include all required fields per API specification
- **For File:** Include file content as string
- **For JMS:** Include message body and optional properties
- **For RFC:** Include function name and parameters

## Examples by Use Case

### Use Case 1: Testing Order Processing
```json
{
  "orderId": "ORD-2024-001",
  "orderDate": "2024-01-01",
  "customer": {
    "id": "CUST-123",
    "name": "John Doe",
    "email": "john.doe@example.com"
  },
  "items": [
    {
      "productId": "PROD-001",
      "productName": "Widget",
      "quantity": 5,
      "unitPrice": 99.99,
      "totalPrice": 499.95
    }
  ],
  "shippingAddress": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zipCode": "10001"
  },
  "billingAddress": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zipCode": "10001"
  },
  "paymentMethod": "CREDIT_CARD",
  "totalAmount": 499.95,
  "taxAmount": 40.00,
  "shippingAmount": 10.00,
  "grandTotal": 549.95
}
```

### Use Case 2: Testing Customer Update
```json
{
  "customerId": "CUST-123",
  "action": "UPDATE",
  "changes": {
    "email": "new.email@example.com",
    "phone": "+1-555-123-4567",
    "address": {
      "street": "456 Oak Ave",
      "city": "Los Angeles",
      "state": "CA",
      "zipCode": "90210"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "source": "WEB_PORTAL"
}
```

### Use Case 3: Testing Inventory Sync
```json
{
  "syncId": "SYNC-001",
  "timestamp": "2024-01-01T12:00:00Z",
  "warehouse": "WH-001",
  "items": [
    {
      "sku": "SKU-001",
      "location": "A1-B2",
      "quantity": 100,
      "reserved": 20,
      "available": 80,
      "lastUpdated": "2024-01-01T11:00:00Z"
    },
    {
      "sku": "SKU-002",
      "location": "A1-B3",
      "quantity": 50,
      "reserved": 10,
      "available": 40,
      "lastUpdated": "2024-01-01T11:30:00Z"
    }
  ]
}
```

### Use Case 4: Testing Error Scenarios
```json
{
  "errorCode": "ERR-001",
  "errorMessage": "Invalid customer ID",
  "timestamp": "2024-01-01T12:00:00Z",
  "context": {
    "operation": "CREATE_ORDER",
    "customerId": "INVALID-123"
  }
}
```

### Use Case 5: Testing Edge Cases
```json
{
  "message": "Edge case test",
  "data": {
    "emptyString": "",
    "nullValue": null,
    "zeroValue": 0,
    "negativeValue": -1,
    "veryLargeNumber": 999999999999,
    "specialCharacters": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
    "unicode": "🎉🎊🎈",
    "longString": "This is a very long string that exceeds normal limits..."
  }
}
```

## Testing Different Scenarios

### Success Scenario
```json
{
  "scenario": "SUCCESS",
  "data": {
    "orderId": "ORD-001",
    "status": "PENDING",
    "message": "Order created successfully"
  }
}
```

### Error Scenario
```json
{
  "scenario": "ERROR",
  "error": {
    "code": "ERR-001",
    "message": "Invalid input data",
    "details": "Customer ID is required"
  }
}
```

### Validation Scenario
```json
{
  "scenario": "VALIDATION",
  "data": {
    "orderId": "ORD-001",
    "validationErrors": [
      {
        "field": "customer.email",
        "message": "Invalid email format"
      },
      {
        "field": "items[0].quantity",
        "message": "Quantity must be greater than 0"
      }
    ]
  }
}
```

## Best Practices

1. **Start Simple:** Begin with minimal payloads and add complexity as needed
2. **Use Real Data:** When possible, use anonymized production data
3. **Test Edge Cases:** Include boundary values and special characters
4. **Document Payloads:** Keep track of what each payload tests
5. **Version Control:** Store test payloads in version control
6. **Validate First:** Ensure payload is valid JSON before sending
7. **Check Size:** Keep payloads reasonable for testing

## Common Mistakes to Avoid

1. **Invalid JSON:** Missing commas, quotes, or brackets
2. **Wrong Data Types:** Using strings where numbers are expected
3. **Missing Required Fields:** Not including all mandatory fields
4. **Incorrect Format:** Wrong XML structure for SOAP/IDoc
5. **Too Large:** Payloads that exceed system limits
6. **Special Characters:** Not escaping quotes in XML strings

## Summary

Users can provide **any JSON payload** to the [`test_iflow_with_user_payload`](/_tool/_test_iflow_with_user_payload_tool.py) tool. The payload can be:

- **Simple JSON objects** for basic testing
- **Complex nested structures** for realistic scenarios
- **XML strings** for SOAP/IDoc adapters
- **File content** for file adapters
- **Message structures** for JMS adapters
- **RFC structures** for RFC adapters
- **Any custom format** that the integration flow expects

The tool sends the payload as-is to the integration flow endpoint, allowing users to test any scenario they need.
