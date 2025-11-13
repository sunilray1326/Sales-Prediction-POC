"""
Sales Advisor API Client

Supports testing both local and Azure-deployed APIs.

Usage:
    # Test local API
    python sales_advisor_client.py --run local

    # Test Azure API
    python sales_advisor_client.py --run azure

    # Default (local)
    python sales_advisor_client.py
"""

import requests
import argparse
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

    def analyze_opportunity(self, description: str, save_json: bool = False, output_dir: str = ".") -> Dict[str, Any]:
        """Analyze a sales opportunity

        Args:
            description: Opportunity description text
            save_json: If True, saves request and response as JSON files
            output_dir: Directory to save JSON files (default: current directory)

        Returns:
            API response as dictionary
        """
        payload = {"opportunity_description": description}

        # Save request JSON if requested
        if save_json:
            request_file = os.path.join(output_dir, "request.json")
            with open(request_file, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            print(f"💾 Request saved to: {request_file}")

        response = self.session.post(
            f"{self.base_url}/api/v1/analyze",
            json=payload
        )
        response.raise_for_status()
        result = response.json()

        # Save response JSON if requested
        if save_json:
            response_file = os.path.join(output_dir, "response.json")
            with open(response_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"💾 Response saved to: {response_file}")

        return result

    def get_recommendation(self, description: str) -> str:
        """Get just the recommendation text"""
        result = self.analyze_opportunity(description)
        return result.get("recommendation", "")

    def get_top_improvements(self, description: str, top_n: int = 3) -> list:
        """Get top N win probability improvements"""
        result = self.analyze_opportunity(description)
        improvements = result.get("win_probability_improvements", [])
        return improvements[:top_n]

def get_config(environment: str) -> Dict[str, str]:
    """Get configuration based on environment"""
    if environment.lower() == "azure":
        # Azure configuration from environment variables
        base_url = os.getenv("AZURE_API_URL")
        api_key = os.getenv("AZURE_API_KEY")

        if not base_url:
            raise ValueError(
                "AZURE_API_URL not found in environment variables. "
                "Please set it in your .env file or environment.\n"
                "Example: AZURE_API_URL=https://your-app-name.azurewebsites.net"
            )
        if not api_key:
            raise ValueError(
                "AZURE_API_KEY not found in environment variables. "
                "Please set it in your .env file or environment.\n"
                "Example: AZURE_API_KEY=your-azure-api-key"
            )

        return {
            "base_url": base_url,
            "api_key": api_key,
            "environment": "Azure"
        }
    else:
        # Local configuration
        base_url = os.getenv("LOCAL_API_URL", "http://localhost:8000")
        api_key = os.getenv("LOCAL_API_KEY", "your-secret-api-key-1")

        return {
            "base_url": base_url,
            "api_key": api_key,
            "environment": "Local"
        }


# Usage example
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Test Sales Advisor API (Local or Azure)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sales_advisor_client.py --run local    # Test local API
  python sales_advisor_client.py --run azure    # Test Azure API
  python sales_advisor_client.py                # Test local API (default)
        """
    )
    parser.add_argument(
        "--run",
        type=str,
        choices=["local", "azure"],
        default="local",
        help="Environment to test: 'local' or 'azure' (default: local)"
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save request and response as JSON files (request.json and response.json)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save JSON files (default: current directory)"
    )

    args = parser.parse_args()

    # Get configuration
    try:
        config = get_config(args.run)
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        exit(1)

    print("=" * 80)
    print(f"🚀 Testing Sales Advisor API - {config['environment']} Environment")
    print("=" * 80)
    print(f"Base URL: {config['base_url']}")
    print(f"API Key: {config['api_key'][:10]}..." if len(config['api_key']) > 10 else f"API Key: {config['api_key']}")
    print("=" * 80)
    print()

    # Initialize client
    client = SalesAdvisorClient(
        base_url=config['base_url'],
        api_key=config['api_key']
    )

    try:
        # Check health
        print("📊 Checking API health...")
        health = client.health_check()
        print(f"✅ API Status: {health['status']}")
        print()

        # Analyze opportunity
        print("🔍 Analyzing opportunity...")
        description = "product GTX Pro, sector medical, region United States, sales price 4821, expected revenue 4514"
        result = client.analyze_opportunity(description, save_json=args.save_json, output_dir=args.output_dir)

        print(f"✅ Analysis complete!")
        print()
        print("📝 Recommendation:")
        print("-" * 80)
        print(result['recommendation'])
        print("-" * 80)
        print()

        # Show what fields are in the response
        print("📦 Response fields:")
        for key in result.keys():
            if key == "similar_won_deals":
                print(f"  - {key}: {len(result[key])} deals")
            elif key == "similar_lost_deals":
                print(f"  - {key}: {len(result[key])} deals")
            elif key == "recommendation":
                print(f"  - {key}: {len(result[key])} characters")
            else:
                print(f"  - {key}")

        print()
        print("=" * 80)
        print(f"✅ {config['environment']} API test completed successfully!")
        print("=" * 80)

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to {config['base_url']}")
        print(f"   Make sure the {config['environment']} API is running.")
        exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
        exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)