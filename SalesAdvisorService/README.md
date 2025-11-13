# 🚀 Sales Advisor API Service

A production-ready REST API that provides AI-powered sales opportunity analysis and recommendations using Azure OpenAI and Azure Cognitive Search.

---

## 📁 Project Structure

```
SalesAdvisorService/
│
├── 📚 Documents/                          # All documentation (START HERE!)
│   ├── README.md                          # Documentation index
│   ├── QUICK_START.md                     # 5-min setup guide
│   ├── README_API.md                      # Complete API reference
│   ├── AZURE_DEPLOYMENT_GUIDE.md          # Azure deployment guide
│   ├── API_TESTING_GUIDE.md               # Testing examples
│   ├── GRACEFUL_ERROR_HANDLING.md         # Error handling guide
│   ├── IMPLEMENTATION_SUMMARY.md          # Technical overview
│   └── IMPROVEMENTS_SUMMARY.md            # Recent enhancements
│
├── 🐍 Core Application Files
│   ├── api.py                             # FastAPI application (main entry point)
│   ├── models.py                          # Pydantic request/response models
│   ├── sales_advisor_engine.py            # Core business logic engine
│   ├── prompts.py                         # LLM prompt templates
│   └── start_api.py                       # Convenient startup script
│
├── 📊 Data Files
│   ├── quantitative_stats.json            # Statistical data
│   └── qualitative_stats.json             # Qualitative insights
│
├── 🧪 Testing
│   └── test_missing_metrics.py            # Graceful error handling tests
│
└── 📦 Configuration
    └── requirements.txt                   # Python dependencies
```

---

## ⚡ Quick Start

### **1. Local Testing (5 minutes)**

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy .env.template to .env and fill in values)
# Required: OPEN_AI_KEY, OPEN_AI_ENDPOINT, SEARCH_ENDPOINT, SEARCH_KEY, INDEX_NAME, API_KEYS

# Start the server
python start_api.py

# API will be available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### **2. Test the API**

```bash
# Python
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"opportunity_description": "We are pursuing a $50,000 deal for GTX Plus Pro with a healthcare company in the Northeast region."}'
```

### **3. Deploy to Azure (10 minutes)**

See **[Documents/AZURE_DEPLOYMENT_GUIDE.md](Documents/AZURE_DEPLOYMENT_GUIDE.md)** for step-by-step instructions.

---

## 🎯 Key Features

✅ **Simple One-Call API** - Users call ONE endpoint and get complete response  
✅ **API Key Authentication** - Secure access control  
✅ **Rate Limiting** - 10 requests per hour per API key  
✅ **Graceful Error Handling** - Never crashes on missing metrics  
✅ **Auto-Generated Docs** - Interactive Swagger UI at `/docs`  
✅ **Production-Ready** - Comprehensive logging, error handling, CORS  
✅ **Azure-Optimized** - Designed for Azure App Service deployment  

---

## 📚 Documentation

**All documentation is in the [Documents/](Documents/) folder.**

**Start here:** [Documents/README.md](Documents/README.md) - Documentation index

**Quick links:**
- **Getting Started**: [Documents/QUICK_START.md](Documents/QUICK_START.md)
- **API Reference**: [Documents/README_API.md](Documents/README_API.md)
- **Deployment**: [Documents/AZURE_DEPLOYMENT_GUIDE.md](Documents/AZURE_DEPLOYMENT_GUIDE.md)
- **Testing**: [Documents/API_TESTING_GUIDE.md](Documents/API_TESTING_GUIDE.md)

---

## 🔑 API Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/` | GET | No | API information |
| `/health` | GET | No | Health check |
| `/docs` | GET | No | Interactive API documentation |
| `/api/v1/analyze` | POST | Yes | Analyze sales opportunity |

---

## 📊 Example Request/Response

**Request:**
```json
POST /api/v1/analyze
Headers: X-API-Key: your-api-key

{
  "opportunity_description": "We are pursuing a $50,000 deal for GTX Plus Pro with a healthcare company in the Northeast region."
}
```

**Response:**
```json
{
  "success": true,
  "recommendation": "Based on similar deals...",
  "extracted_attributes": {
    "product": "GTX Plus Pro",
    "sector": "Healthcare",
    "region": "Northeast",
    "sales_price": 50000
  },
  "win_probability_improvements": [...],
  "similar_won_deals": [...],
  "similar_lost_deals": [...],
  "statistics": {...}
}
```

---

## 🧪 Testing

```bash
# Test graceful error handling
python test_missing_metrics.py

# Run local server with pre-flight checks
python start_api.py
```

See [Documents/API_TESTING_GUIDE.md](Documents/API_TESTING_GUIDE.md) for comprehensive testing examples.

---

## 🛡️ Graceful Error Handling

The API **never crashes** when users provide invalid product/sector/region values. Instead:
- Uses case-insensitive lookup
- Returns top alternatives when exact match not found
- Provides clear user-friendly messages

See [Documents/GRACEFUL_ERROR_HANDLING.md](Documents/GRACEFUL_ERROR_HANDLING.md) for details.

---

## 💰 Cost Estimate

**Azure App Service deployment:** ~$138-288/month

See [Documents/README_API.md](Documents/README_API.md) for detailed cost breakdown.

---

## 📞 Need Help?

1. Check the [Documents/](Documents/) folder for comprehensive guides
2. Review troubleshooting sections in each guide
3. Check application logs for error messages

---

**Ready to get started? → [Documents/QUICK_START.md](Documents/QUICK_START.md)** 🚀

