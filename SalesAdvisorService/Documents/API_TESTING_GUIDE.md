# 🧪 API Testing Guide

Complete guide to test the Sales Advisor REST API using various tools.

---

## 📋 Table of Contents

1. [Quick Test with cURL](#quick-test-with-curl)
2. [Testing with Postman](#testing-with-postman)
3. [Testing with Python](#testing-with-python)
4. [Testing with JavaScript](#testing-with-javascript)
5. [Interactive API Documentation](#interactive-api-documentation)

---

## 🚀 Quick Test with cURL

### 1. Test Health Endpoint (No Authentication)

```bash
# Local testing
curl http://localhost:8000/health

# Azure deployment
curl https://sales-advisor-api.azurewebsites.net/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "azure_services": {
    "openai": "connected",
    "cognitive_search": "connected"
  }
}
```

---

### 2. Test Analysis Endpoint (Requires API Key)

```bash
# Local testing
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-1" \
  -d '{
    "opportunity_description": "We are pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product. The sales rep is John Smith."
  }'

# Azure deployment
curl -X POST https://sales-advisor-api.azurewebsites.net/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-1" \
  -d '{
    "opportunity_description": "We are pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product. The sales rep is John Smith."
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "recommendation": "Based on analysis of similar deals...",
  "extracted_attributes": {
    "product": "GTX Plus Pro",
    "sector": "Healthcare",
    "region": "Northeast",
    "current_rep": "John Smith",
    "sales_price": 50000.0,
    "expected_revenue": null
  },
  "win_probability_improvements": [
    {
      "rank": 1,
      "recommendation": "Switch to GTX Plus Pro",
      "uplift_percent": 15.5,
      "confidence": "High",
      "source_type": "Quantitative simulation",
      "explanation": "This recommendation is based on quantitative simulation showing 15.50% improvement in win rate."
    }
  ],
  "similar_won_deals": [...],
  "similar_lost_deals": [...],
  "statistics": {...}
}
```

---

### 3. Test Authentication Error

```bash
# Missing API key
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"opportunity_description": "Test deal"}'
```

**Expected Response (401):**
```json
{
  "detail": "Missing API key. Include X-API-Key header in your request."
}
```

---

### 4. Test Rate Limiting

```bash
# Run this command 11 times quickly to trigger rate limit
for i in {1..11}; do
  curl -X POST http://localhost:8000/api/v1/analyze \
    -H "Content-Type: application/json" \
    -H "X-API-Key: your-secret-api-key-1" \
    -d '{"opportunity_description": "Test deal number '$i'"}'
  echo "\n--- Request $i completed ---\n"
done
```

**Expected Response (429 on 11th request):**
```json
{
  "detail": "Rate limit exceeded. You can analyze 10 opportunities per hour. Please wait 3540 seconds before trying again."
}
```

---

## 📮 Testing with Postman

### Step 1: Import Collection

1. Open Postman
2. Click **Import** → **Raw Text**
3. Paste the collection JSON (see below)
4. Click **Import**

### Step 2: Set Environment Variables

Create a new environment with these variables:

| Variable | Value |
|----------|-------|
| `base_url` | `http://localhost:8000` or `https://sales-advisor-api.azurewebsites.net` |
| `api_key` | `your-secret-api-key-1` |

### Step 3: Test Endpoints

#### Request 1: Health Check

- **Method**: GET
- **URL**: `{{base_url}}/health`
- **Headers**: None required

#### Request 2: Analyze Opportunity

- **Method**: POST
- **URL**: `{{base_url}}/api/v1/analyze`
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-API-Key`: `{{api_key}}`
- **Body** (raw JSON):
```json
{
  "opportunity_description": "We are pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product. The sales rep is John Smith."
}
```

### Postman Collection JSON

```json
{
  "info": {
    "name": "Sales Advisor API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/health",
          "host": ["{{base_url}}"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "Analyze Opportunity",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "X-API-Key",
            "value": "{{api_key}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"opportunity_description\": \"We are pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product. The sales rep is John Smith.\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/v1/analyze",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "analyze"]
        }
      }
    }
  ]
}
```

---

## 🐍 Testing with Python

### Simple Test Script

```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"  # or your Azure URL
API_KEY = "your-secret-api-key-1"

# Test 1: Health Check
print("Testing health endpoint...")
response = requests.get(f"{BASE_URL}/health")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}\n")

# Test 2: Analyze Opportunity
print("Testing analyze endpoint...")
headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

payload = {
    "opportunity_description": "We are pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product. The sales rep is John Smith."
}

response = requests.post(
    f"{BASE_URL}/api/v1/analyze",
    headers=headers,
    json=payload
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Success: {result['success']}")
    print(f"Recommendation: {result['recommendation'][:200]}...")
    print(f"Extracted Attributes: {json.dumps(result['extracted_attributes'], indent=2)}")
    print(f"Win Probability Improvements: {len(result['win_probability_improvements'])} recommendations")
else:
    print(f"Error: {response.json()}")
```

### Advanced Python Client

```python
import requests
from typing import Dict, Any, Optional

class SalesAdvisorClient:
    """Python client for Sales Advisor API"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-API-Key": api_key
        })

    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def analyze_opportunity(self, description: str) -> Dict[str, Any]:
        """Analyze a sales opportunity"""
        payload = {"opportunity_description": description}
        response = self.session.post(
            f"{self.base_url}/api/v1/analyze",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_recommendation(self, description: str) -> str:
        """Get just the recommendation text"""
        result = self.analyze_opportunity(description)
        return result.get("recommendation", "")

    def get_top_improvements(self, description: str, top_n: int = 3) -> list:
        """Get top N win probability improvements"""
        result = self.analyze_opportunity(description)
        improvements = result.get("win_probability_improvements", [])
        return improvements[:top_n]

# Usage example
if __name__ == "__main__":
    client = SalesAdvisorClient(
        base_url="http://localhost:8000",
        api_key="your-secret-api-key-1"
    )

    # Check health
    health = client.health_check()
    print(f"API Status: {health['status']}")

    # Analyze opportunity
    description = "We are pursuing a $50,000 deal with a healthcare company..."
    result = client.analyze_opportunity(description)

    print(f"\nRecommendation:\n{result['recommendation']}\n")

    # Get top improvements
    improvements = client.get_top_improvements(description)
    print("Top Recommendations:")
    for imp in improvements:
        print(f"  {imp['rank']}. {imp['recommendation']} (+{imp['uplift_percent']:.1f}%)")
```

---

## 🌐 Testing with JavaScript

### Node.js Example

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';
const API_KEY = 'your-secret-api-key-1';

// Test health endpoint
async function testHealth() {
  try {
    const response = await axios.get(`${BASE_URL}/health`);
    console.log('Health Status:', response.data);
  } catch (error) {
    console.error('Health check failed:', error.message);
  }
}

// Test analyze endpoint
async function analyzeOpportunity(description) {
  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/analyze`,
      { opportunity_description: description },
      {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        }
      }
    );

    console.log('Analysis successful!');
    console.log('Recommendation:', response.data.recommendation.substring(0, 200) + '...');
    console.log('Extracted Attributes:', response.data.extracted_attributes);
    console.log('Top Improvements:', response.data.win_probability_improvements.length);

    return response.data;
  } catch (error) {
    if (error.response) {
      console.error('Error:', error.response.status, error.response.data);
    } else {
      console.error('Error:', error.message);
    }
  }
}

// Run tests
(async () => {
  await testHealth();

  const description = "We are pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product.";
  await analyzeOpportunity(description);
})();
```

### Browser JavaScript (Fetch API)

```javascript
const BASE_URL = 'https://sales-advisor-api.azurewebsites.net';
const API_KEY = 'your-secret-api-key-1';

async function analyzeOpportunity(description) {
  try {
    const response = await fetch(`${BASE_URL}/api/v1/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
      },
      body: JSON.stringify({
        opportunity_description: description
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    const result = await response.json();
    console.log('Success:', result.success);
    console.log('Recommendation:', result.recommendation);

    return result;
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Usage
analyzeOpportunity("We are pursuing a $50,000 deal with a healthcare company...");
```

---

## 📖 Interactive API Documentation

FastAPI automatically generates interactive API documentation!

### Swagger UI (Recommended)

**URL**: `http://localhost:8000/docs` or `https://your-app.azurewebsites.net/docs`

Features:
- ✅ Try out API endpoints directly in browser
- ✅ See request/response schemas
- ✅ Test authentication
- ✅ View all available endpoints

**How to use:**
1. Open `/docs` in your browser
2. Click on an endpoint (e.g., `POST /api/v1/analyze`)
3. Click **"Try it out"**
4. Enter your API key in the **X-API-Key** field
5. Enter request body
6. Click **"Execute"**
7. See the response!

### ReDoc (Alternative)

**URL**: `http://localhost:8000/redoc` or `https://your-app.azurewebsites.net/redoc`

Features:
- ✅ Clean, readable documentation
- ✅ Better for sharing with non-technical users
- ✅ Printable format

---

## 🧪 Test Scenarios

### Scenario 1: Valid Request

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-1" \
  -d '{
    "opportunity_description": "Pursuing $75,000 GTX Basic deal with manufacturing company in West region. Rep: Sarah Johnson."
  }'
```

**Expected**: 200 OK with full analysis

---

### Scenario 2: Missing API Key

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"opportunity_description": "Test"}'
```

**Expected**: 401 Unauthorized

---

### Scenario 3: Invalid API Key

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: wrong-key" \
  -d '{"opportunity_description": "Test"}'
```

**Expected**: 401 Unauthorized

---

### Scenario 4: Too Short Description

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-1" \
  -d '{"opportunity_description": "Short"}'
```

**Expected**: 422 Validation Error (minimum 10 characters)

---

### Scenario 5: Rate Limit Exceeded

Run 11 requests within an hour with the same API key.

**Expected**: First 10 succeed (200 OK), 11th fails (429 Too Many Requests)

---

## 📊 Response Structure Reference

### Successful Response

```json
{
  "success": true,
  "recommendation": "string (AI-generated recommendation)",
  "extracted_attributes": {
    "product": "string or null",
    "sector": "string or null",
    "region": "string or null",
    "current_rep": "string or null",
    "sales_price": "number or null",
    "expected_revenue": "number or null"
  },
  "win_probability_improvements": [
    {
      "rank": 1,
      "recommendation": "string",
      "uplift_percent": 15.5,
      "confidence": "High|Medium|Low",
      "source_type": "Quantitative simulation|Qualitative insight",
      "explanation": "string"
    }
  ],
  "similar_won_deals": [...],
  "similar_lost_deals": [...],
  "statistics": {
    "overall_win_rate": 0.63,
    "avg_cycle_days_won": 45.2,
    "avg_cycle_days_lost": 52.8,
    "product_stats": {...},
    "sector_stats": {...},
    "region_stats": {...},
    "current_rep_stats": {...},
    "top_reps": [...]
  }
}
```

### Error Response

```json
{
  "detail": "Error message here"
}
```

---

## ✅ Testing Checklist

- [ ] Health endpoint returns 200 OK
- [ ] Analysis endpoint works with valid API key
- [ ] Missing API key returns 401
- [ ] Invalid API key returns 401
- [ ] Rate limiting works (11th request fails)
- [ ] Validation works (short description fails)
- [ ] Response contains all expected fields
- [ ] Similar deals are returned
- [ ] Win probability improvements are calculated
- [ ] Statistics are included
- [ ] Interactive docs accessible at /docs

**Happy Testing! 🎉**


