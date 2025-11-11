# Quick Start: REST API Version

## 🚀 Switch to REST API Version in 3 Steps

### Step 1: Install Dependencies

```bash
pip uninstall openai azure-search-documents azure-core
pip install requests==2.31.0
```

Or use the REST requirements file:
```bash
pip install -r requirements_rest.txt
```

### Step 2: Update app.py

Change **one line** in `app.py`:

```python
# FROM:
from sales_advisor_engine import SalesAdvisorEngine

# TO:
from sales_advisor_engine_rest import SalesAdvisorEngine
```

### Step 3: Run the App

```bash
streamlit run app.py
```

That's it! ✅

---

## 📊 What Changed?

### Code Changes
- ✅ **0 changes** to `app.py` logic (just 1 import line)
- ✅ **0 changes** to `.env` file
- ✅ **0 changes** to prompts or statistics
- ✅ **Same API interface** - `analyze_opportunity()` works identically

### Dependencies Reduced
- ❌ Removed: `openai` (2.3.0)
- ❌ Removed: `azure-search-documents` (11.6.0)
- ❌ Removed: `azure-core` (1.35.1)
- ✅ Added: `requests` (2.31.0)

**Result**: 5 packages → 3 packages (40% reduction)

---

## 🔍 How It Works

### SDK Version (Before)
```python
# Uses Azure SDK libraries
self.openai_client = AzureOpenAI(...)
response = self.openai_client.embeddings.create(...)
```

### REST Version (After)
```python
# Uses direct HTTP calls
url = f"{endpoint}/openai/deployments/{model}/embeddings?api-version={version}"
response = requests.post(url, headers=headers, json=payload)
```

---

## ✅ Benefits

| Benefit | Description |
|---------|-------------|
| **Fewer Dependencies** | Only 3 packages instead of 5 |
| **Smaller Footprint** | Lighter Docker images, faster deployments |
| **More Control** | See exactly what's sent to Azure APIs |
| **Better Debugging** | Easier to log and troubleshoot HTTP calls |
| **Version Flexibility** | Not tied to SDK version updates |

---

## 📝 API Endpoints Used

### Azure OpenAI

**Embeddings**:
```
POST https://{resource}.openai.azure.com/openai/deployments/{model}/embeddings?api-version=2024-12-01-preview
```

**Chat Completions**:
```
POST https://{resource}.openai.azure.com/openai/deployments/{model}/chat/completions?api-version=2024-12-01-preview
```

### Azure Cognitive Search

**Vector Search**:
```
POST https://{service}.search.windows.net/indexes/{index}/docs/search?api-version=2023-11-01
```

---

## 🧪 Testing

Run the test script to verify both versions work identically:

```bash
python test_rest_vs_sdk.py
```

This will:
- ✅ Test both SDK and REST versions with the same input
- ✅ Compare extracted attributes
- ✅ Compare search results
- ✅ Verify embeddings are identical

---

## 🔄 Switching Back to SDK Version

If you want to switch back:

```bash
# Reinstall SDK packages
pip install -r requirements.txt

# Update app.py
# Change: from sales_advisor_engine_rest import SalesAdvisorEngine
# To:     from sales_advisor_engine import SalesAdvisorEngine
```

---

## 📦 File Structure

```
SalesAdvisor/
├── sales_advisor_engine.py          # SDK version (original)
├── sales_advisor_engine_rest.py     # REST API version (new)
├── app.py                            # Streamlit UI (works with both)
├── requirements.txt                  # SDK dependencies
├── requirements_rest.txt             # REST dependencies (minimal)
├── test_rest_vs_sdk.py              # Test both versions
├── REST_API_VERSION_GUIDE.md        # Detailed comparison
└── QUICK_START_REST.md              # This file
```

---

## ❓ Which Version Should I Use?

### Use SDK Version if:
- ✅ You want easier development with type hints
- ✅ You prefer less verbose code
- ✅ You want automatic SDK updates

### Use REST Version if:
- ✅ You want minimal dependencies
- ✅ You need full control over HTTP requests
- ✅ You're deploying to serverless/containers
- ✅ You want smaller Docker images
- ✅ You need to customize retry logic

---

## 💡 Pro Tips

### 1. Environment Variables
Both versions use the **same** `.env` file - no changes needed!

### 2. Error Handling
REST version includes `response.raise_for_status()` for automatic error handling.

### 3. Debugging
Add logging to see HTTP requests:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 4. Timeouts
Add timeouts to REST calls:
```python
response = requests.post(url, headers=headers, json=payload, timeout=30)
```

### 5. Retries
Add retry logic:
```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
```

---

## 📚 Additional Resources

- **Detailed Comparison**: See `REST_API_VERSION_GUIDE.md`
- **Azure OpenAI REST API Docs**: https://learn.microsoft.com/en-us/azure/ai-services/openai/reference
- **Azure Search REST API Docs**: https://learn.microsoft.com/en-us/rest/api/searchservice/

---

## ✨ Summary

The REST API version provides:
- ✅ **Same functionality** as SDK version
- ✅ **Same API interface** - drop-in replacement
- ✅ **Fewer dependencies** - 40% reduction
- ✅ **More control** - direct HTTP calls
- ✅ **Better for production** - lighter, more debuggable

**Try it now!** Just change one import line and you're done! 🚀

