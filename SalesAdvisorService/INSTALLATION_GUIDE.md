# 🔧 Installation Guide - Python 3.13 Compatible

## ✅ Updated for Python 3.13 Compatibility

The requirements have been updated to use versions with pre-built wheels that work with Python 3.13 on Windows.

---

## 📦 Installation Steps

### **Option 1: Clean Install (Recommended)**

```bash
# Navigate to the project directory
cd "c:\Sunil Ray\Github\Sales Prediction POC\SalesAdvisorService"

# Upgrade pip first
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

### **Option 2: If You Still Get Errors**

```bash
# Uninstall problematic packages first
pip uninstall pydantic pydantic-core -y

# Upgrade pip, setuptools, and wheel
python -m pip install --upgrade pip setuptools wheel

# Install with pre-built wheels only (no compilation)
pip install --only-binary :all: -r requirements.txt
```

### **Option 3: Install Packages Individually**

If you still have issues, install packages one by one:

```bash
# Core dependencies
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install pydantic==2.9.2
pip install requests==2.31.0
pip install python-dotenv==1.1.1

# Azure SDK
pip install openai==1.54.0
pip install azure-search-documents==11.6.0
pip install azure-core==1.31.0

# Additional
pip install python-multipart==0.0.6
```

---

## 🔍 What Changed?

### **Updated Packages:**

| Package | Old Version | New Version | Reason |
|---------|-------------|-------------|--------|
| **pydantic** | 2.5.0 | 2.9.2 | Better Python 3.13 support, pre-built wheels |
| **openai** | 2.3.0 | 1.54.0 | Stable version with pre-built wheels |
| **azure-core** | 1.35.1 | 1.31.0 | Compatible with azure-search-documents |

### **Why These Changes?**

1. **Python 3.13 is very new** - Not all packages have pre-built wheels yet
2. **pydantic-core 2.14.1 requires Rust** - Compilation fails on Windows without proper setup
3. **Newer pydantic (2.9.2)** - Has pre-built wheels for Python 3.13 on Windows
4. **Stable OpenAI SDK** - Version 1.54.0 is stable and well-tested

---

## ✅ Verify Installation

After installation, verify everything works:

```bash
# Check installed versions
pip list | findstr "fastapi pydantic openai azure"

# Test imports
python -c "import fastapi; import pydantic; import openai; print('✅ All imports successful!')"

# Run the API
python start_api.py
```

---

## 🚨 Troubleshooting

### **Error: "No matching distribution found"**

**Solution:**
```bash
# Use --only-binary to force pre-built wheels
pip install --only-binary :all: pydantic==2.9.2
```

### **Error: "Microsoft Visual C++ required"**

**Solution:** You don't need this anymore! The updated versions use pre-built wheels.

### **Error: "Rust compiler not found"**

**Solution:** You don't need Rust anymore! The updated pydantic version has pre-built wheels.

### **Error: "Could not build wheels"**

**Solution:**
```bash
# Clear pip cache
pip cache purge

# Reinstall with no cache
pip install --no-cache-dir -r requirements.txt
```

---

## 🎯 Alternative: Use Python 3.11 or 3.12

If you continue to have issues, consider using Python 3.11 or 3.12 instead of 3.13:

```bash
# Check your Python version
python --version

# If you have Python 3.11 or 3.12 available, use that instead
# Python 3.13 is very new and some packages may not be fully compatible yet
```

**Recommended Python versions:**
- ✅ **Python 3.11** - Excellent compatibility
- ✅ **Python 3.12** - Good compatibility
- ⚠️ **Python 3.13** - Very new, some packages still catching up

---

## 📝 Notes

- All packages in the updated requirements.txt have **pre-built wheels** for Windows
- No compilation required (no need for Visual Studio Build Tools or Rust)
- Tested with Python 3.13 on Windows
- Compatible with Azure App Service deployment

---

## ✅ Expected Output

When installation succeeds, you should see:

```
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 pydantic-2.9.2 ...
```

No errors about:
- ❌ "Building wheel for pydantic-core"
- ❌ "Rust compiler not found"
- ❌ "Microsoft Visual C++ required"

---

## 🚀 Next Steps

After successful installation:

1. **Set up environment variables** - Copy `.env.template` to `.env` and fill in your Azure credentials
2. **Test the API** - Run `python start_api.py`
3. **Check the docs** - Visit http://localhost:8000/docs

See **Documents/QUICK_START.md** for detailed setup instructions.

