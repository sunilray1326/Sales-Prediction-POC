"""
Simple script to start the Sales Advisor API locally

"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        'OPEN_AI_KEY',
        'OPEN_AI_ENDPOINT',
        'SEARCH_ENDPOINT',
        'SEARCH_KEY',
        'INDEX_NAME',
        'EMBEDDING_MODEL',
        'CHAT_MODEL',
        'API_KEYS'
    ]
    
    # Load .env file if it exists
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env file")
    else:
        print("⚠️  No .env file found. Make sure environment variables are set.")
    
    # Check for missing variables
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print("\n❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Create a .env file based on .env.template and fill in your Azure credentials.")
        return False
    
    print("✅ All required environment variables are set")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    # Map of package names to their import names
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'pydantic': 'pydantic',
        'requests': 'requests',
        'python-dotenv': 'dotenv',
        'openai': 'openai',
        'azure-search-documents': 'azure.search.documents'
    }

    missing = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)

    if missing:
        print("\n❌ Missing required packages:")
        for package in missing:
            print(f"   - {package}")
        print("\n💡 Install dependencies with: pip install -r requirements.txt")
        return False

    print("✅ All required packages are installed")
    return True


def check_files():
    """Check if required files exist"""
    required_files = [
        'api.py',
        'models.py',
        'sales_advisor_engine.py',
        'prompts.py',
        'quantitative_stats.json',
        'qualitative_stats.json'
    ]
    
    base_dir = Path(__file__).parent
    missing = [f for f in required_files if not (base_dir / f).exists()]
    
    if missing:
        print("\n❌ Missing required files:")
        for file in missing:
            print(f"   - {file}")
        return False
    
    print("✅ All required files are present")
    return True


def start_server():
    """Start the FastAPI server"""
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 Starting Sales Advisor API Server")
    print("="*60)
    print("\n📍 Server will be available at:")
    print("   - Local:   http://localhost:8000")
    print("   - Network: http://0.0.0.0:8000")
    print("\n📖 API Documentation:")
    print("   - Swagger UI: http://localhost:8000/docs")
    print("   - ReDoc:      http://localhost:8000/redoc")
    print("\n🔑 API Key Authentication:")
    api_keys = os.getenv('API_KEYS', '').split(',')
    print(f"   - {len(api_keys)} API key(s) configured")
    print(f"   - Use X-API-Key header with one of: {', '.join(api_keys[:2])}")
    print("\n⚡ Rate Limiting:")
    print("   - 10 requests per hour per API key")
    print("\n💡 Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    try:
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔍 Pre-flight Checks")
    print("="*60 + "\n")
    
    # Run checks
    checks_passed = True
    checks_passed &= check_files()
    checks_passed &= check_dependencies()
    checks_passed &= check_environment()
    
    if not checks_passed:
        print("\n❌ Pre-flight checks failed. Please fix the issues above and try again.")
        sys.exit(1)
    
    print("\n✅ All pre-flight checks passed!")
    
    # Start server
    start_server()

