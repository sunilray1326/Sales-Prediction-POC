import requests
import json

# Make API call
response = requests.post(
    'http://localhost:8000/api/v1/analyze',
    json={'opportunity_description': 'product GTX Pro, sector medical, region United States, sales price 4821, expected revenue 4514'},
    headers={'X-API-Key': 'your-secret-api-key-1'}
)

# Get the recommendation
result = response.json()
recommendation = result['recommendation']

# Save to file
with open('raw_recommendation.txt', 'w', encoding='utf-8') as f:
    f.write("=== RAW RECOMMENDATION FROM API ===\n\n")
    f.write(recommendation)
    f.write("\n\n=== END ===\n")

print(f"Recommendation length: {len(recommendation)} characters")
print(f"First 500 characters:\n{recommendation[:500]}")
print("\nSaved to raw_recommendation.txt")

