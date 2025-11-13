# 🛡️ Graceful Error Handling - Missing Metrics

## Overview

The Sales Advisor API is designed to **NEVER crash** when users provide product, sector, region, or rep values that don't exist in our statistics. Instead, it handles missing data gracefully by providing top alternatives.

---

## ✅ How It Works

### 1. **Case-Insensitive Lookup**

The engine uses `_case_insensitive_lookup()` to find metrics, so these are all equivalent:
- "Healthcare" = "healthcare" = "HEALTHCARE" = "HeAlThCaRe"

```python
def _case_insensitive_lookup(self, search_value, data_dict):
    """Perform case-insensitive lookup in a dictionary."""
    if not search_value or not data_dict:
        return None
    
    lowercase_map = {k.lower(): k for k in data_dict.keys()}
    return lowercase_map.get(search_value.lower())
```

### 2. **Fallback to Top Alternatives**

When a metric is not found, the engine automatically returns the top 3 alternatives based on lift/win rate:

**Example - Missing Product:**
```python
product_key = self._case_insensitive_lookup(product, prod_stats["win_rate"])

if product_key:
    # Product found - return its stats
    relevant["products"] = {
        product_key: {
            "win_rate": prod_stats["win_rate"][product_key],
            "lift": prod_stats["lift"][product_key]
        }
    }
else:
    # Product NOT found - return top 3 alternatives
    self.logger.debug(f"Product '{product}' not found in stats, using top alternatives")
    relevant["products"] = {}
    alts = sorted(
        [(k, prod_stats["lift"][k]) for k in prod_stats["lift"]],
        key=lambda x: x[1],
        reverse=True
    )[:3]
    for alt_prod, _ in alts:
        relevant["products"][alt_prod] = {
            "win_rate": prod_stats["win_rate"][alt_prod],
            "lift": prod_stats["lift"][alt_prod]
        }
```

### 3. **API Layer Protection**

The API layer (`api.py`) has additional safeguards:

```python
def transform_engine_result(result: dict) -> OpportunityResponse:
    """
    Transform SalesAdvisorEngine result to API response model.
    
    Handles missing metrics gracefully - if product/sector/region not found,
    the engine returns top alternatives instead of crashing.
    """
    try:
        # Use .get() with defaults to prevent KeyError
        extracted_attrs_data = result.get("extracted_attributes", {})
        relevant_stats = result.get("relevant_stats", {})
        
        # ... safe extraction with try/except blocks
        
    except Exception as e:
        logging.error(f"Error transforming engine result: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to transform engine result: {str(e)}")
```

---

## 📊 Behavior Examples

### Example 1: Invalid Product

**User Input:**
```json
{
  "opportunity_description": "We are pursuing a $50,000 deal for 'SuperDuperProduct' (doesn't exist) with a healthcare company."
}
```

**What Happens:**
1. ✅ Engine extracts: `product = "SuperDuperProduct"`
2. ✅ Lookup fails (product not in stats)
3. ✅ Engine logs: `"Product 'SuperDuperProduct' not found in stats, using top alternatives"`
4. ✅ Returns top 3 products by lift instead
5. ✅ LLM recommendation mentions: "The product 'SuperDuperProduct' is not in our historical data. Based on similar deals, consider these alternatives..."

**Response:**
```json
{
  "success": true,
  "extracted_attributes": {
    "product": "SuperDuperProduct"
  },
  "statistics": {
    "product_stats": {
      "GTX Plus Pro": {"win_rate": 0.75, "lift": 1.2},
      "GTX Basic": {"win_rate": 0.65, "lift": 1.1},
      "GTX Standard": {"win_rate": 0.60, "lift": 1.0}
    }
  },
  "recommendation": "The product 'SuperDuperProduct' is not found in our historical data. However, based on similar deals in the healthcare sector, I recommend considering GTX Plus Pro which has a 75% win rate..."
}
```

### Example 2: Invalid Sector

**User Input:**
```json
{
  "opportunity_description": "We are pursuing a deal with a company in the 'Underwater Basket Weaving' sector."
}
```

**What Happens:**
1. ✅ Engine extracts: `sector = "Underwater Basket Weaving"`
2. ✅ Lookup fails (sector not in stats)
3. ✅ Engine logs: `"Sector 'Underwater Basket Weaving' not found in stats, using top alternatives"`
4. ✅ Returns top 3 sectors by lift instead
5. ✅ LLM recommendation mentions the sector is not found

**Response:**
```json
{
  "success": true,
  "extracted_attributes": {
    "sector": "Underwater Basket Weaving"
  },
  "statistics": {
    "sector_stats": {
      "Healthcare": {"win_rate": 0.70, "lift": 1.15},
      "Technology": {"win_rate": 0.68, "lift": 1.12},
      "Finance": {"win_rate": 0.65, "lift": 1.08}
    }
  },
  "recommendation": "The sector 'Underwater Basket Weaving' is not in our historical data. Based on overall trends, here are insights from our top-performing sectors..."
}
```

### Example 3: All Attributes Invalid

**User Input:**
```json
{
  "opportunity_description": "Deal for 'FakeProduct' with 'FakeSector' in 'FakeRegion' by 'FakeRep'."
}
```

**What Happens:**
1. ✅ Engine extracts all attributes
2. ✅ All lookups fail
3. ✅ Engine returns top alternatives for each category
4. ✅ LLM provides general recommendations based on overall stats

**Response:**
```json
{
  "success": true,
  "extracted_attributes": {
    "product": "FakeProduct",
    "sector": "FakeSector",
    "region": "FakeRegion",
    "current_rep": "FakeRep"
  },
  "statistics": {
    "product_stats": { /* top 3 products */ },
    "sector_stats": { /* top 3 sectors */ },
    "region_stats": { /* top 3 regions */ },
    "current_rep_stats": null
  },
  "recommendation": "While the specific product, sector, and region mentioned are not in our historical data, I can provide insights based on our overall performance trends..."
}
```

---

## 🧪 Testing

Run the test script to verify graceful error handling:

```bash
cd SalesAdvisorService
python test_missing_metrics.py
```

**Tests:**
1. ✅ Missing Product - Returns top alternatives
2. ✅ Missing Sector - Returns top alternatives
3. ✅ Missing Region - Returns top alternatives
4. ✅ Missing Rep - Returns null (no crash)
5. ✅ All Missing - Returns top alternatives for all

---

## 🔍 Logging

When metrics are not found, the engine logs debug messages:

```
DEBUG - Looking up product: 'SuperDuperProduct'
DEBUG - Product 'SuperDuperProduct' not found in stats, using top alternatives
DEBUG - Looking up sector: 'Underwater Basket Weaving'
DEBUG - Sector 'Underwater Basket Weaving' not found in stats, using top alternatives
```

These logs help you understand what's happening without crashing the API.

---

## 📝 User-Friendly Messages

The LLM is instructed to mention when metrics are not found:

**Prompt includes:**
```
If any of the extracted attributes (product, sector, region, rep) are not found in the 
statistics, mention this in your recommendation and provide insights based on the 
available alternatives.
```

**Example LLM Response:**
> "I notice that the product 'SuperDuperProduct' is not in our historical sales data. 
> However, based on similar deals in the healthcare sector, I can provide the following 
> recommendations..."

---

## ✅ Summary

**The API NEVER crashes due to missing metrics. Instead:**

1. ✅ **Case-insensitive lookup** - Handles variations in capitalization
2. ✅ **Automatic fallback** - Returns top alternatives when not found
3. ✅ **Clear logging** - Debug messages explain what happened
4. ✅ **User-friendly messages** - LLM explains missing data
5. ✅ **Safe API layer** - Additional `.get()` safeguards prevent KeyError
6. ✅ **Comprehensive testing** - Test script verifies all scenarios

**This matches the SDK version behavior - graceful degradation instead of crashes!** 🎉

