"""
Test script to verify complete request/response body logging
"""

import requests
import json
import time

# API configuration
API_URL = "http://localhost:8000/api/v1/analyze"
API_KEY = "test-key-12345"  # Use your actual API key from .env

def test_api_logging():
    """Test the API and check logs for complete request/response bodies"""
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE REQUEST/RESPONSE BODY LOGGING")
    print("=" * 80 + "\n")
    
    # Test case 1: Successful request
    print("TEST 1: Sending successful request...")
    print("-" * 80)
    
    request_body = {
        "opportunity_description": "We are pursuing a $50,000 deal for GTX Plus Pro with a healthcare company in the Northeast region. The sales rep is John Smith."
    }
    
    print("Request Body:")
    print(json.dumps(request_body, indent=2))
    print()
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(API_URL, json=request_body, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        print()
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("-" * 80)
    print("\n✅ Check the log file: logs/sales_advisor.log")
    print("\nYou should see:")
    print("  1. 📥 INCOMING API REQUEST - Complete request body as JSON")
    print("  2. 🔵 ENGINE - INCOMING REQUEST - Complete engine request as JSON")
    print("  3. 🟢 ENGINE - OUTGOING RESPONSE - Complete engine response as JSON")
    print("  4. 📤 OUTGOING API RESPONSE - Complete API response body as JSON")
    print("\n" + "=" * 80)
    
    # Test case 2: Error request (minimal prompt)
    print("\nTEST 2: Sending error request (minimal prompt)...")
    print("-" * 80)
    
    error_request_body = {
        "opportunity_description": "We have a deal."
    }
    
    print("Request Body:")
    print(json.dumps(error_request_body, indent=2))
    print()
    
    try:
        response = requests.post(API_URL, json=error_request_body, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        print()
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("-" * 80)
    print("\n✅ Check the log file: logs/sales_advisor.log")
    print("\nYou should see:")
    print("  1. 📥 INCOMING API REQUEST - Complete request body as JSON")
    print("  2. 🔵 ENGINE - INCOMING REQUEST - Complete engine request as JSON")
    print("  3. 🔴 ENGINE - OUTGOING RESPONSE (Error) - Complete error response as JSON")
    print("  4. 📤 OUTGOING API ERROR RESPONSE - Complete error response as JSON")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n⚠️  Make sure the API is running first!")
    print("   Run: python start_api.py")
    print("\n   Press Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    try:
        time.sleep(5)
        test_api_logging()
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")

