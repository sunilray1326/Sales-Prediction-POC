# 📋 Complete Request/Response Body Logging Guide

## Overview

The Sales Advisor API and Engine now log **complete request and response bodies as JSON** with **no truncation**. This makes debugging extremely easy - you can see exactly what was sent and what was returned.

---

## 🔍 What Gets Logged

### **1. API Level - Incoming Request (📥)**

When the API receives a request:

```
================================================================================
📥 INCOMING API REQUEST
================================================================================
REQUEST BODY (Complete):
{
  "opportunity_description": "We are pursuing a $50,000 deal for GTX Plus Pro with a healthcare company in the Northeast region. The sales rep is John Smith."
}
================================================================================
```

**Logged Information:**
- ✅ Complete request body as JSON
- ✅ No truncation
- ✅ All fields included

### **2. Engine Level - Incoming Request (🔵)**

When the engine receives a request:

```
================================================================================
🔵 ENGINE - INCOMING REQUEST
================================================================================
ENGINE REQUEST (Complete):
{
  "user_prompt": "We are pursuing a $50,000 deal for GTX Plus Pro with a healthcare company in the Northeast region. The sales rep is John Smith.",
  "prompt_length": 134,
  "prompt_type": "str"
}
================================================================================
```

### **3. Engine Level - Outgoing Response (🟢)**

When the engine completes successfully:

```
================================================================================
🟢 ENGINE - OUTGOING RESPONSE (Success)
================================================================================
ENGINE RESPONSE (Complete):
{
  "success": true,
  "error_message": null,
  "extracted_attributes": {
    "product": "GTX Plus Pro",
    "sector": "Healthcare",
    "region": "Northeast",
    "sales_price": 50000,
    "expected_revenue": null,
    "current_rep": "John Smith"
  },
  "relevant_stats": {
    "overall": {
      "win_rate": 0.6315,
      "total_deals": 1000,
      "won_deals": 631,
      "lost_deals": 369
    },
    "products": {
      "GTX Plus Pro": {
        "win_rate": 0.52,
        "lift": 1.15,
        "total_deals": 150
      }
    },
    "sectors": { ... },
    "regions": { ... },
    "current_rep": { ... },
    "top_reps": [ ... ],
    "simulations": [ ... ]
  },
  "recommendation": "Based on the analysis of similar opportunities...\n\n[COMPLETE RECOMMENDATION TEXT - NO TRUNCATION]\n\n...",
  "won_matches": [
    {
      "deal_id": "D12345",
      "Product": "GTX Plus Pro",
      "Sector": "Healthcare",
      "Region": "Northeast",
      "Sales_Price": 48000,
      "@search.score": 0.95
    },
    ... all 10 won deals ...
  ],
  "lost_matches": [
    ... all 10 lost deals ...
  ]
}
================================================================================
```

**Logged Information:**
- ✅ Complete response as JSON
- ✅ All fields included (no truncation)
- ✅ Full recommendation text
- ✅ All similar deals (all 10 won, all 10 lost)
- ✅ Complete statistics

---

### **3. Error Response (🔴 Red)**

When analysis fails (e.g., attribute extraction fails):

```
🔴 OUTGOING RESPONSE - Analysis failed (attribute extraction)
📤 ERROR RESPONSE DETAILS:
  ├─ Success: False
  ├─ Error Message: Failed to extract attributes from the opportunity description...
  ├─ Extracted Attributes: {}
  ├─ Relevant Stats: None
  ├─ Recommendation: None
  ├─ Won Matches: None
  └─ Lost Matches: None
```

---

### **4. Exception Response (🔴 Red)**

When an exception occurs:

```
🔴 OUTGOING RESPONSE - Analysis failed (exception)
📤 EXCEPTION RESPONSE DETAILS:
  ├─ Success: False
  ├─ Error Message: Error during analysis: Connection timeout
  ├─ Error Type: TimeoutError
  ├─ Extracted Attributes: None
  ├─ Relevant Stats: None
  ├─ Recommendation: None
  ├─ Won Matches: None
  └─ Lost Matches: None
```

**Logged Information:**
- ✅ Error message
- ✅ Exception type
- ✅ Full stack trace (via exc_info=True)
- ✅ All response fields

---

## 🎯 How to Use

### **Enable Detailed Logging**

Set logging level to INFO or DEBUG:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### **In Production (Azure App Service)**

Azure App Service automatically captures all logs. View them in:
- **Azure Portal** → App Service → Monitoring → Log stream
- **Application Insights** → Logs
- **Kudu Console** → Log files

---

## 📊 Log Levels

| Level | What Gets Logged |
|-------|------------------|
| **INFO** | Request/response details, statistics, recommendations (full text) |
| **DEBUG** | Additional internal processing details |
| **WARNING** | Non-critical issues (e.g., missing metrics) |
| **ERROR** | Errors and exceptions with stack traces |

---

## 🔍 Debugging Scenarios

### **Scenario 1: Attribute Extraction Issues**

**Look for:**
```
📥 REQUEST DETAILS:
  └─ Full Prompt Content: [your prompt]

📤 RESPONSE DETAILS:
  ├─ Extracted Attributes:
  │  ├─ product: None  ← Check if this should have been extracted
```

### **Scenario 2: Wrong Statistics Returned**

**Look for:**
```
📤 RESPONSE DETAILS:
  ├─ Relevant Statistics:
  │  ├─ Products: 1 entries
  │  │  ├─ GTX Plus Pro: Win Rate=0.52  ← Verify this is correct
```

### **Scenario 3: Recommendation Quality**

**Look for:**
```
📤 RESPONSE DETAILS:
  ├─ Recommendation:
  │  └─ Content:
  │     [Full recommendation text]  ← Review the complete recommendation
```

### **Scenario 4: Similar Deals Not Relevant**

**Look for:**
```
📤 RESPONSE DETAILS:
  ├─ Similar Won Deals: 10 matches
  │  ├─ Match 1:
  │  │  ├─ Similarity Score: 0.95  ← Check if score is reasonable
```

---

## 📝 Example Log Output

See `test_detailed_logging.py` for a complete example that demonstrates all logging scenarios.

Run it with:
```bash
python test_detailed_logging.py
```

---

## ⚙️ Configuration

### **Disable Detailed Logging**

If logs are too verbose, set level to WARNING:

```python
logging.basicConfig(level=logging.WARNING)
```

### **Log to File**

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sales_advisor.log'),
        logging.StreamHandler()
    ]
)
```

---

## 🎨 Log Format

The logs use tree-style formatting for readability:

```
├─ Top level item
│  ├─ Nested item
│  │  └─ Deeply nested item
│  └─ Another nested item
└─ Last top level item
```

This makes it easy to see the structure of complex data.

---

## ✅ Benefits

1. **Complete Visibility** - See exactly what's being sent and received
2. **No Truncation** - Full text of prompts, recommendations, and data
3. **Easy Debugging** - Quickly identify where issues occur
4. **Production Ready** - Works seamlessly with Azure logging
5. **Structured Format** - Tree-style formatting for easy reading

---

## 🚀 Next Steps

1. Run `test_detailed_logging.py` to see the logging in action
2. Review logs after each API call
3. Use logs to debug any issues
4. Configure log level based on your needs (INFO for debugging, WARNING for production)

---

**Happy debugging! 🔍**

