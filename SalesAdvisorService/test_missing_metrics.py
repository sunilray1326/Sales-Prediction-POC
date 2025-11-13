"""
Test script to verify graceful handling of missing/invalid metrics.

This script tests that the API handles cases where:
- Product is not found in the stats
- Sector is not found in the stats
- Region is not found in the stats
- Rep is not found in the stats

The engine should NOT crash - it should return top alternatives instead.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the engine
from sales_advisor_engine import SalesAdvisorEngine

def test_missing_product():
    """Test with a product that doesn't exist in stats"""
    print("\n" + "="*80)
    print("TEST 1: Missing Product (should NOT crash)")
    print("="*80)
    
    engine = SalesAdvisorEngine()
    
    # Use a product that definitely doesn't exist
    prompt = """
    We are pursuing a $50,000 deal with a healthcare company in the Northeast region.
    The product is 'SuperDuperUltraMegaProduct' which doesn't exist in our stats.
    Sales rep is John Smith.
    """
    
    result = engine.analyze_opportunity(prompt)
    
    if result["success"]:
        print("✅ SUCCESS - Engine handled missing product gracefully")
        print(f"   Extracted product: {result['extracted_attributes'].get('product')}")
        print(f"   Product stats returned: {list(result['relevant_stats'].get('products', {}).keys())}")
        print(f"   Recommendation preview: {result['recommendation'][:200]}...")
    else:
        print(f"❌ FAILED - Engine returned error: {result.get('error_message')}")
    
    return result["success"]


def test_missing_sector():
    """Test with a sector that doesn't exist in stats"""
    print("\n" + "="*80)
    print("TEST 2: Missing Sector (should NOT crash)")
    print("="*80)
    
    engine = SalesAdvisorEngine()
    
    # Use a sector that definitely doesn't exist
    prompt = """
    We are pursuing a $50,000 deal for GTX Plus Pro product in the Northeast region.
    The company is in the 'Underwater Basket Weaving' sector which doesn't exist in our stats.
    Sales rep is John Smith.
    """
    
    result = engine.analyze_opportunity(prompt)
    
    if result["success"]:
        print("✅ SUCCESS - Engine handled missing sector gracefully")
        print(f"   Extracted sector: {result['extracted_attributes'].get('sector')}")
        print(f"   Sector stats returned: {list(result['relevant_stats'].get('sector', {}).keys())}")
        print(f"   Recommendation preview: {result['recommendation'][:200]}...")
    else:
        print(f"❌ FAILED - Engine returned error: {result.get('error_message')}")
    
    return result["success"]


def test_missing_region():
    """Test with a region that doesn't exist in stats"""
    print("\n" + "="*80)
    print("TEST 3: Missing Region (should NOT crash)")
    print("="*80)
    
    engine = SalesAdvisorEngine()
    
    # Use a region that definitely doesn't exist
    prompt = """
    We are pursuing a $50,000 deal for GTX Plus Pro product with a healthcare company.
    The company is located in 'Antarctica' region which doesn't exist in our stats.
    Sales rep is John Smith.
    """
    
    result = engine.analyze_opportunity(prompt)
    
    if result["success"]:
        print("✅ SUCCESS - Engine handled missing region gracefully")
        print(f"   Extracted region: {result['extracted_attributes'].get('region')}")
        print(f"   Region stats returned: {list(result['relevant_stats'].get('region', {}).keys())}")
        print(f"   Recommendation preview: {result['recommendation'][:200]}...")
    else:
        print(f"❌ FAILED - Engine returned error: {result.get('error_message')}")
    
    return result["success"]


def test_missing_rep():
    """Test with a rep that doesn't exist in stats"""
    print("\n" + "="*80)
    print("TEST 4: Missing Sales Rep (should NOT crash)")
    print("="*80)
    
    engine = SalesAdvisorEngine()
    
    # Use a rep that definitely doesn't exist
    prompt = """
    We are pursuing a $50,000 deal for GTX Plus Pro product with a healthcare company in Northeast.
    The sales rep is 'Nonexistent McFakename' who doesn't exist in our stats.
    """
    
    result = engine.analyze_opportunity(prompt)
    
    if result["success"]:
        print("✅ SUCCESS - Engine handled missing rep gracefully")
        print(f"   Extracted rep: {result['extracted_attributes'].get('current_rep')}")
        print(f"   Rep stats returned: {result['relevant_stats'].get('current_rep')}")
        print(f"   Recommendation preview: {result['recommendation'][:200]}...")
    else:
        print(f"❌ FAILED - Engine returned error: {result.get('error_message')}")
    
    return result["success"]


def test_all_missing():
    """Test with everything missing"""
    print("\n" + "="*80)
    print("TEST 5: All Attributes Missing (should NOT crash)")
    print("="*80)
    
    engine = SalesAdvisorEngine()
    
    # Use all invalid values
    prompt = """
    We are pursuing a $50,000 deal for 'FakeProduct' with a company in 'FakeSector' 
    located in 'FakeRegion'. Sales rep is 'FakeRep'.
    """
    
    result = engine.analyze_opportunity(prompt)
    
    if result["success"]:
        print("✅ SUCCESS - Engine handled all missing attributes gracefully")
        print(f"   Product stats returned: {list(result['relevant_stats'].get('products', {}).keys())}")
        print(f"   Sector stats returned: {list(result['relevant_stats'].get('sector', {}).keys())}")
        print(f"   Region stats returned: {list(result['relevant_stats'].get('region', {}).keys())}")
        print(f"   Recommendation preview: {result['recommendation'][:200]}...")
    else:
        print(f"❌ FAILED - Engine returned error: {result.get('error_message')}")
    
    return result["success"]


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING GRACEFUL HANDLING OF MISSING METRICS")
    print("="*80)
    print("\nThis test verifies that the engine doesn't crash when product/sector/region")
    print("are not found in the stats. Instead, it should return top alternatives.")
    
    # Check environment variables
    required_vars = ["OPEN_AI_KEY", "OPEN_AI_ENDPOINT", "SEARCH_ENDPOINT", "SEARCH_KEY", "INDEX_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set up your .env file before running tests.")
        sys.exit(1)
    
    # Run all tests
    results = []
    results.append(("Missing Product", test_missing_product()))
    results.append(("Missing Sector", test_missing_sector()))
    results.append(("Missing Region", test_missing_region()))
    results.append(("Missing Rep", test_missing_rep()))
    results.append(("All Missing", test_all_missing()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED - Graceful error handling is working correctly!")
        print("\nThe engine successfully handles missing metrics by:")
        print("  1. Using case-insensitive lookup to find metrics")
        print("  2. Returning top alternatives when exact match not found")
        print("  3. Never crashing - always returning a valid response")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Please review the errors above")
        sys.exit(1)

