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
    description = "product GTX Pro, sector medical, region United States, sales price 4821, expected revenue 4514"
    result = client.analyze_opportunity(description)

    print(f"\nRecommendation:\n{result['recommendation']}\n")

    # Show what fields are in the response
    print("Response fields:")
    for key in result.keys():
        print(f"  - {key}")