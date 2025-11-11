# Salesforce Integration Guide for Sales Recommendation Advisor

## Overview
This guide explains how to implement the Sales Recommendation Advisor functionality in Salesforce using REST APIs and Apex code. The system analyzes sales opportunities and provides AI-powered recommendations based on historical data.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Data Model Setup](#data-model-setup)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [REST API Calls](#rest-api-calls)
6. [Metric Calculations](#metric-calculations)
7. [Apex Code Examples](#apex-code-examples)

---

## Architecture Overview

### High-Level Flow
```
User Input (Opportunity Description)
    ↓
Step 1: Extract Attributes (LLM API Call)
    ↓
Step 2: Calculate Historical Statistics (Salesforce SOQL + Calculations)
    ↓
Step 3: Find Similar Opportunities (Vector Search API)
    ↓
Step 4: Build Context (Data Aggregation)
    ↓
Step 5: Generate Recommendations (LLM API Call)
    ↓
Display Results to User
```

### Key Components
1. **Azure OpenAI API** - For LLM chat completions and embeddings
2. **Azure Cognitive Search** - For vector similarity search
3. **Salesforce Database** - Historical opportunity data
4. **Apex Classes** - Business logic and calculations

---

## Prerequisites

### Required Services
1. **Azure OpenAI Account**
   - Chat Completion Model (e.g., GPT-4)
   - Embedding Model (e.g., text-embedding-ada-002)
   - API Key and Endpoint URL

2. **Azure Cognitive Search**
   - Search Service with Vector Search enabled
   - Index with opportunity data and embeddings
   - API Key and Service URL

3. **Salesforce Environment**
   - Custom Objects for Opportunities (or standard Opportunity object)
   - Apex Classes enabled
   - Remote Site Settings configured for external APIs

### Salesforce Remote Site Settings
Configure these URLs in Setup → Security → Remote Site Settings:
- Azure OpenAI Endpoint: `https://YOUR-RESOURCE.openai.azure.com`
- Azure Search Endpoint: `https://YOUR-SERVICE.search.windows.net`

---

## Data Model Setup

### Required Fields on Opportunity Object

```apex
// Standard or Custom Opportunity Fields
- Name (Text)
- Product__c (Text) - e.g., "GTX Pro", "MG Special"
- Account_Sector__c (Picklist) - e.g., "Finance", "Healthcare", "Marketing"
- Account_Region__c (Picklist) - e.g., "North America", "Europe", "Asia"
- Sales_Rep__c (Lookup to User)
- Sales_Price__c (Currency)
- Expected_Revenue__c (Currency)
- Deal_Stage__c (Picklist) - "Won" or "Lost"
- Deal_Engage_Date__c (Date)
- Deal_Close_Date__c (Date)
- Sales_Cycle_Duration__c (Number) - Calculated: Close Date - Engage Date
- Notes__c (Long Text Area) - Deal notes and insights
- Text_Vector__c (Long Text Area) - JSON array of embedding vector (1536 dimensions)
```

### Custom Metadata for Statistics
Create a Custom Metadata Type `Sales_Statistics__mdt` to cache computed statistics:
```apex
- Category__c (Text) - e.g., "product", "sector", "region", "sales_rep"
- Key__c (Text) - e.g., "GTX Pro", "Finance"
- Win_Rate__c (Number) - e.g., 0.6523
- Lift__c (Number) - e.g., 1.0345
- Sample_Size__c (Number) - e.g., 450
```

---

## Step-by-Step Implementation

### STEP 1: Extract Attributes from User Input

**Purpose:** Parse the user's opportunity description and extract key attributes (product, sector, region, sales rep, price, revenue).

**Method:** Call Azure OpenAI Chat Completion API

#### REST API Call

**Endpoint:**
```
POST https://YOUR-RESOURCE.openai.azure.com/openai/deployments/YOUR-CHAT-MODEL/chat/completions?api-version=2024-02-15-preview
```

**Headers:**
```
Content-Type: application/json
api-key: YOUR-AZURE-OPENAI-API-KEY
```

**Request Body:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an attribute extractor. Parse the user prompt and extract: product (str or None), sector (str or None), region (str or None), sales_price (float or None), expected_revenue (float or None), current_rep (str or None). Return as JSON dict.\n\nCRITICAL RULES:\n1. ONLY extract values that are EXPLICITLY mentioned in the prompt\n2. If a value is not stated, return null for that field\n3. Do NOT infer, guess, or estimate any values\n4. Extract exact values as written, without interpretation\n5. Extract ONLY the core value without extra words (e.g., 'Marketing' not 'Marketing sector')"
    },
    {
      "role": "user",
      "content": "MG Special deal in Marketing sector, Panama region, rep: Cecily Lampkin, price $75000"
    }
  ],
  "temperature": 0.0,
  "max_tokens": 200
}
```

**Response:**
```json
{
  "choices": [
    {
      "message": {
        "content": "{\"product\": \"MG Special\", \"sector\": \"Marketing\", \"region\": \"Panama\", \"sales_price\": 75000, \"expected_revenue\": null, \"current_rep\": \"Cecily Lampkin\"}"
      }
    }
  ]
}
```

**Parameters Explained:**
- `temperature: 0.0` - Deterministic output (no randomness)
- `max_tokens: 200` - Limit response length
- `messages` - Array with system prompt (instructions) and user prompt (data to extract)

---

### STEP 2: Calculate Historical Statistics

**Purpose:** Compute win rates, lift values, and other metrics from historical Salesforce opportunity data.

#### 2.1 Overall Win Rate

**SOQL Query:**
```sql
SELECT COUNT(Id) total, 
       SUM(CASE WHEN Deal_Stage__c = 'Won' THEN 1 ELSE 0 END) won_count
FROM Opportunity
WHERE Deal_Stage__c IN ('Won', 'Lost')
```

**Calculation:**
```apex
Decimal overallWinRate = wonCount / totalCount;
// Example: 3150 won / 5000 total = 0.63 (63%)
```

#### 2.2 Win Rate by Category (Product, Sector, Region, Sales Rep)

**SOQL Query (Example for Product):**
```sql
SELECT Product__c, 
       COUNT(Id) sample_size,
       AVG(CASE WHEN Deal_Stage__c = 'Won' THEN 1.0 ELSE 0.0 END) win_rate
FROM Opportunity
WHERE Deal_Stage__c IN ('Won', 'Lost')
GROUP BY Product__c
```

**Calculation:**
```apex
for (AggregateResult ar : results) {
    String product = (String) ar.get('Product__c');
    Decimal winRate = (Decimal) ar.get('win_rate');
    Integer sampleSize = (Integer) ar.get('sample_size');
    
    // Calculate lift (performance relative to baseline)
    Decimal lift = winRate / overallWinRate;
    
    // Store in map
    productStats.put(product, new Map<String, Decimal>{
        'win_rate' => winRate,
        'lift' => lift,
        'sample_size' => sampleSize
    });
}
```

**Example Output:**
```json
{
  "GTX Pro": {
    "win_rate": 0.6823,
    "lift": 1.0830,
    "sample_size": 450
  },
  "MG Special": {
    "win_rate": 0.5912,
    "lift": 0.9384,
    "sample_size": 320
  }
}
```

**Lift Interpretation:**
- `lift > 1.0` - Performs better than baseline (e.g., 1.0830 = 8.3% better)
- `lift < 1.0` - Performs worse than baseline (e.g., 0.9384 = 6.16% worse)
- `lift = 1.0` - Performs at baseline

#### 2.3 Product-Sector Combination Win Rates

**SOQL Query:**
```sql
SELECT Product__c, Account_Sector__c,
       AVG(CASE WHEN Deal_Stage__c = 'Won' THEN 1.0 ELSE 0.0 END) win_rate
FROM Opportunity
WHERE Deal_Stage__c IN ('Won', 'Lost')
GROUP BY Product__c, Account_Sector__c
```

**Calculation:**
```apex
for (AggregateResult ar : results) {
    String product = (String) ar.get('Product__c');
    String sector = (String) ar.get('Account_Sector__c');
    Decimal winRate = (Decimal) ar.get('win_rate');
    
    String key = product + '_' + sector;
    productSectorStats.put(key, winRate);
}
```

#### 2.4 Average Revenue by Product (Won Deals Only)

**SOQL Query:**
```sql
SELECT Product__c,
       AVG(Expected_Revenue__c) avg_revenue
FROM Opportunity
WHERE Deal_Stage__c = 'Won'
GROUP BY Product__c
```

#### 2.5 Correlation Calculations (Price vs Win Rate)

**SOQL Query:**
```sql
SELECT Sales_Price__c,
       CASE WHEN Deal_Stage__c = 'Won' THEN 1.0 ELSE 0.0 END is_won
FROM Opportunity
WHERE Deal_Stage__c IN ('Won', 'Lost') AND Sales_Price__c != null
```

**Calculation (Pearson Correlation):**
```apex
// Calculate correlation between sales_price and is_won
Decimal sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
Integer n = opportunities.size();

for (Opportunity opp : opportunities) {
    Decimal x = opp.Sales_Price__c;
    Decimal y = opp.Deal_Stage__c == 'Won' ? 1.0 : 0.0;

    sumX += x;
    sumY += y;
    sumXY += x * y;
    sumX2 += x * x;
    sumY2 += y * y;
}

Decimal correlation = (n * sumXY - sumX * sumY) /
    Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
```

**Interpretation:**
- Positive correlation (e.g., 0.15): Higher price → Higher win rate
- Negative correlation (e.g., -0.23): Higher price → Lower win rate
- Near zero (e.g., 0.02): No relationship

#### 2.6 Sales Cycle Duration

**SOQL Query:**
```sql
SELECT AVG(Sales_Cycle_Duration__c) avg_cycle
FROM Opportunity
WHERE Deal_Stage__c = 'Won'

SELECT AVG(Sales_Cycle_Duration__c) avg_cycle
FROM Opportunity
WHERE Deal_Stage__c = 'Lost'
```

---

### STEP 3: Extract Qualitative Insights (Win Drivers & Loss Risks)

**Purpose:** Identify patterns in deal notes that correlate with wins or losses.

#### 3.1 Define Keyword Categories

```apex
Map<String, Map<String, List<String>>> keywordCategories = new Map<String, Map<String, List<String>>>{
    'win_drivers' => new Map<String, List<String>>{
        'demo_success' => new List<String>{'demo', 'demonstration', 'trial', 'pilot', 'proof of concept', 'poc'},
        'relationship_strong' => new List<String>{'relationship', 'trust', 'partnership', 'rapport'},
        'value_clear' => new List<String>{'roi', 'value proposition', 'business case', 'cost savings'},
        'champion_internal' => new List<String>{'champion', 'advocate', 'sponsor', 'executive buy-in'}
    },
    'loss_risks' => new Map<String, List<String>>{
        'pricing_high' => new List<String>{'price', 'expensive', 'cost', 'budget', 'too high'},
        'competitor_won' => new List<String>{'competitor', 'alternative', 'chose another', 'went with'},
        'timing_bad' => new List<String>{'timing', 'not ready', 'postponed', 'delayed'},
        'no_budget' => new List<String>{'no budget', 'budget cut', 'funding', 'financial constraints'}
    }
};
```

#### 3.2 Extract Patterns from Notes

**SOQL Query:**
```sql
SELECT Id, Notes__c, Deal_Stage__c, Product__c, Account_Sector__c
FROM Opportunity
WHERE Deal_Stage__c IN ('Won', 'Lost') AND Notes__c != null
```

**Pattern Extraction Logic:**
```apex
Map<String, Map<String, Integer>> qualStats = new Map<String, Map<String, Integer>>{
    'win_drivers' => new Map<String, Integer>(),
    'loss_risks' => new Map<String, Integer>()
};

Integer totalWon = 0, totalLost = 0;

for (Opportunity opp : opportunities) {
    String notesLower = opp.Notes__c.toLowerCase();
    String stage = opp.Deal_Stage__c;

    if (stage == 'Won') totalWon++;
    else if (stage == 'Lost') totalLost++;

    String categoryType = (stage == 'Won') ? 'win_drivers' : 'loss_risks';
    Map<String, List<String>> categories = keywordCategories.get(categoryType);

    for (String category : categories.keySet()) {
        List<String> keywords = categories.get(category);

        for (String keyword : keywords) {
            if (notesLower.contains(keyword)) {
                Integer count = qualStats.get(categoryType).get(category);
                if (count == null) count = 0;
                qualStats.get(categoryType).put(category, count + 1);
                break; // Count once per opportunity
            }
        }
    }
}

// Calculate frequencies
Map<String, Map<String, Decimal>> qualFrequencies = new Map<String, Map<String, Decimal>>();

for (String category : qualStats.get('win_drivers').keySet()) {
    Integer count = qualStats.get('win_drivers').get(category);
    Decimal frequency = (Decimal) count / totalWon;
    qualFrequencies.get('win_drivers').put(category, frequency);
}

for (String category : qualStats.get('loss_risks').keySet()) {
    Integer count = qualStats.get('loss_risks').get(category);
    Decimal frequency = (Decimal) count / totalLost;
    qualFrequencies.get('loss_risks').put(category, frequency);
}
```

**Example Output:**
```json
{
  "win_drivers": {
    "demo_success": {
      "frequency": 0.6998,
      "count": 2966,
      "examples": ["Conducted successful product demo", "Trial period went well"]
    },
    "relationship_strong": {
      "frequency": 0.5234,
      "count": 2215
    }
  },
  "loss_risks": {
    "pricing_high": {
      "frequency": 0.4521,
      "count": 1823,
      "examples": ["Price too high for budget", "Competitor offered lower price"]
    },
    "competitor_won": {
      "frequency": 0.3812,
      "count": 1537
    }
  }
}
```

**Frequency Interpretation:**
- `> 0.5 (50%)` - CRITICAL pattern (appears in majority of deals)
- `0.3 - 0.5 (30-50%)` - SIGNIFICANT pattern
- `0.1 - 0.3 (10-30%)` - MODERATE pattern
- `< 0.1 (10%)` - MINOR pattern (usually filtered out)

---

### STEP 4: Generate Simulations (What-If Scenarios)

**Purpose:** Estimate win probability improvements for different scenarios.

#### 4.1 Product Switch Simulation

```apex
Decimal baselineWinRate = 0.63; // Overall win rate
String currentProduct = 'MG Special';
String alternativeProduct = 'GTX Pro';

// Get lift values from statistics
Decimal currentLift = productStats.get(currentProduct).get('lift'); // 0.9384
Decimal alternativeLift = productStats.get(alternativeProduct).get('lift'); // 1.0830

// Calculate estimated win rates
Decimal currentEstimate = baselineWinRate * currentLift; // 0.63 * 0.9384 = 0.5912 (59.12%)
Decimal alternativeEstimate = baselineWinRate * alternativeLift; // 0.63 * 1.0830 = 0.6823 (68.23%)

// Calculate uplift
Decimal upliftPercent = ((alternativeLift - currentLift) / currentLift) * 100;
// (1.0830 - 0.9384) / 0.9384 * 100 = 15.41%

// Create simulation
Map<String, Object> simulation = new Map<String, Object>{
    'description' => 'Switch to ' + alternativeProduct,
    'estimated_win_rate' => alternativeEstimate,
    'uplift_percent' => upliftPercent,
    'revenue_estimate' => avgRevenueByProduct.get(alternativeProduct),
    'confidence' => 'High'
};
```

#### 4.2 Sales Rep Assignment Simulation

```apex
String currentRep = 'John Doe';
String topRep = 'Sarah Chen';

Decimal currentRepLift = repStats.get(currentRep).get('lift'); // 0.95
Decimal topRepLift = repStats.get(topRep).get('lift'); // 1.085

Decimal upliftPercent = ((topRepLift - currentRepLift) / currentRepLift) * 100;
// (1.085 - 0.95) / 0.95 * 100 = 14.21%

Map<String, Object> simulation = new Map<String, Object>{
    'description' => 'Assign to ' + topRep,
    'estimated_win_rate' => baselineWinRate * topRepLift,
    'uplift_percent' => upliftPercent,
    'confidence' => repStats.get(topRep).get('sample_size') > 200 ? 'High' : 'Medium'
};
```

#### 4.3 Qualitative Risk Mitigation Simulation

**Purpose:** Estimate uplift from addressing top loss risk.

**Method:** Call Azure OpenAI to estimate uplift percentage.

**REST API Call:**
```
POST https://YOUR-RESOURCE.openai.azure.com/openai/deployments/YOUR-CHAT-MODEL/chat/completions?api-version=2024-02-15-preview
```

**Request Body:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a sales analyst. Estimate the % win probability uplift if a sales team successfully addresses a specific loss risk. Return ONLY a number (e.g., 8.5 for 8.5% uplift). Base your estimate on the frequency of the risk in lost deals."
    },
    {
      "role": "user",
      "content": "Estimate % win uplift if addressing 'pricing_high' (freq: 0.4521) in Finance sector."
    }
  ],
  "temperature": 0.0,
  "max_tokens": 10,
  "seed": 12345
}
```

**Response:**
```json
{
  "choices": [
    {
      "message": {
        "content": "8.5"
      }
    }
  ]
}
```

**Calculation:**
```apex
Decimal qualUplift = 8.5; // From LLM response
Decimal estimatedWinRate = baselineWinRate * (1 + qualUplift / 100);
// 0.63 * (1 + 8.5/100) = 0.63 * 1.085 = 0.6836 (68.36%)

Map<String, Object> simulation = new Map<String, Object>{
    'description' => 'Address top qual risk \'pricing_high\'',
    'estimated_win_rate' => estimatedWinRate,
    'uplift_percent' => qualUplift,
    'from_qual' => true
};
```

---

### STEP 5: Find Similar Opportunities (Vector Search)

**Purpose:** Retrieve top 10 similar won and lost opportunities using semantic search.

#### 5.1 Generate Embedding for User Input

**REST API Call:**
```
POST https://YOUR-RESOURCE.openai.azure.com/openai/deployments/YOUR-EMBEDDING-MODEL/embeddings?api-version=2024-02-15-preview
```

**Headers:**
```
Content-Type: application/json
api-key: YOUR-AZURE-OPENAI-API-KEY
```

**Request Body:**
```json
{
  "input": "MG Special deal in Marketing sector, Panama region, rep: Cecily Lampkin, price $75000"
}
```

**Response:**
```json
{
  "data": [
    {
      "embedding": [0.0234, -0.0156, 0.0891, ..., 0.0123]
    }
  ]
}
```

**Note:** The embedding is a 1536-dimensional vector (for text-embedding-ada-002 model).

#### 5.2 Search Azure Cognitive Search with Vector Query

**REST API Call:**
```
POST https://YOUR-SERVICE.search.windows.net/indexes/YOUR-INDEX-NAME/docs/search?api-version=2023-11-01
```

**Headers:**
```
Content-Type: application/json
api-key: YOUR-AZURE-SEARCH-API-KEY
```

**Request Body (for Won Opportunities):**
```json
{
  "vectorQueries": [
    {
      "kind": "vector",
      "fields": "text_vector",
      "vector": [0.0234, -0.0156, 0.0891, ..., 0.0123],
      "k": 10,
      "exhaustive": false
    }
  ],
  "filter": "deal_stage eq 'won'",
  "select": "opportunity_id,content,deal_stage,product,account_sector,sales_rep,account_region,sales_price,revenue_from_deal,sales_cycle_duration,deal_value_ratio,Notes",
  "top": 10
}
```

**Parameters Explained:**
- `vectorQueries.vector` - The 1536-dimensional embedding from Step 5.1
- `vectorQueries.k` - Number of nearest neighbors to find (10)
- `vectorQueries.exhaustive` - false for faster approximate search
- `filter` - Filter by deal_stage ('won' or 'lost')
- `select` - Fields to return
- `top` - Maximum results to return

**Response:**
```json
{
  "value": [
    {
      "opportunity_id": "OPP-12345",
      "product": "MG Special",
      "account_sector": "Marketing",
      "sales_rep": "Jane Smith",
      "account_region": "Panama",
      "sales_price": 72000,
      "revenue_from_deal": 68000,
      "sales_cycle_duration": 45,
      "deal_value_ratio": 0.94,
      "Notes": "Successful demo led to quick close. Customer appreciated bundled pricing...",
      "@search.score": 0.8523
    },
    ...
  ]
}
```

**Repeat for Lost Opportunities:**
Change filter to `"filter": "deal_stage eq 'lost'"` and make another API call.

---

### STEP 6: Build Context Message

**Purpose:** Combine all data into a structured context for the final LLM call.

```apex
String contextMsg = 'User Opportunity:\n' + userInput + '\n\n' +
    'Extracted Attributes: ' + JSON.serialize(extractedAttrs) + '\n\n' +
    '=== Top 10 Successful Matches ===\n' + formatDocs(wonDocs) + '\n\n' +
    '=== Top 10 Failed Matches ===\n' + formatDocs(lostDocs);

// formatDocs helper method
String formatDocs(List<Map<String, Object>> docs) {
    List<String> formatted = new List<String>();
    for (Map<String, Object> doc : docs) {
        formatted.add(
            doc.get('opportunity_id') + ' | Stage: ' + doc.get('deal_stage') +
            ' | Rep: ' + doc.get('sales_rep') + ' | Product: ' + doc.get('product') +
            ' | Sector: ' + doc.get('account_sector') + ' | Region: ' + doc.get('account_region') +
            ' | Price: ' + doc.get('sales_price') + ' | Revenue: ' + doc.get('revenue_from_deal') +
            ' | Sales Cycle Duration: ' + doc.get('sales_cycle_duration') + ' days' +
            ' | Deal Value Ratio: ' + doc.get('deal_value_ratio') +
            ' | Note: ' + String.valueOf(doc.get('Notes')).left(400) + '...'
        );
    }
    return String.join(formatted, '\n');
}
```

---

### STEP 7: Generate Final Recommendations

**Purpose:** Call LLM with all context and statistics to generate comprehensive sales strategy recommendations.

#### REST API Call

**Endpoint:**
```
POST https://YOUR-RESOURCE.openai.azure.com/openai/deployments/YOUR-CHAT-MODEL/chat/completions?api-version=2024-02-15-preview
```

**Request Body:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a sales strategy expert. Analyze the opportunity and provide recommendations based on historical data, statistics, and similar deals. Include: 1) Lift Analysis showing win rates and lift for each attribute, 2) Recommendation Summary with estimated win probability, 3) Additions/Improvements (5 items), 4) Removals/Risks (3 items), 5) Win Probability Improvement (top 3 recommendations), 6) Consider options (2 items). Use emojis for visual clarity. ALWAYS cite data sources with metrics."
    },
    {
      "role": "user",
      "content": "Based on the following details:\n[CONTEXT_MSG from Step 6]\n\nRELEVANT_STATS (filtered for this opportunity):\n[JSON.serialize(relevantStats)]\n\nProvide comprehensive analysis following the required format. START with Lift Analysis section. Include citations for all recommendations showing data source and metrics."
    }
  ],
  "temperature": 0.1,
  "max_tokens": 4000,
  "seed": 12345
}
```

**Parameters Explained:**
- `temperature: 0.1` - Low randomness for consistent, reliable recommendations
- `max_tokens: 4000` - Allow detailed response
- `seed: 12345` - Fixed seed for reproducibility
- System message contains detailed instructions (see prompts.py file for full prompt)
- User message contains all context and statistics

**Response:**
```json
{
  "choices": [
    {
      "message": {
        "content": "📊 LIFT ANALYSIS\n\n✅ Product: MG Special - Win Rate: 59.12% | Lift: 0.9384 → 6.16% below baseline\n❌ Sector: Marketing - Win Rate: 58.45% | Lift: 0.9278 → 7.22% below baseline\n✅ Region: Panama - Win Rate: 65.23% | Lift: 1.0353 → 3.53% above baseline\n...\n\n💡 RECOMMENDATION SUMMARY\n\nEstimated Win Probability: 61.5%\n...\n\n✅ ADDITIONS/IMPROVEMENTS\n\n1. Switch to GTX Pro for higher win rate (Based on simulation: +15.41% uplift, High confidence, $55K revenue estimate)\n2. Assign to Sarah Chen (Based on simulation: +14.21% uplift, High confidence)\n..."
      }
    }
  ]
}
```

---

## Apex Code Examples

### Complete Apex Class Structure

```apex
public class SalesRecommendationService {

    // Configuration
    private static final String OPENAI_ENDPOINT = 'https://YOUR-RESOURCE.openai.azure.com';
    private static final String OPENAI_API_KEY = 'YOUR-API-KEY';
    private static final String CHAT_MODEL = 'gpt-4';
    private static final String EMBEDDING_MODEL = 'text-embedding-ada-002';
    private static final String SEARCH_ENDPOINT = 'https://YOUR-SERVICE.search.windows.net';
    private static final String SEARCH_API_KEY = 'YOUR-SEARCH-KEY';
    private static final String SEARCH_INDEX = 'opportunities-index';

    // Main method to get recommendations
    public static Map<String, Object> getRecommendations(String userInput) {

        // Step 1: Extract attributes
        Map<String, Object> extractedAttrs = extractAttributes(userInput);

        // Step 2: Calculate statistics
        Map<String, Object> stats = calculateStatistics();
        Map<String, Object> qualStats = calculateQualitativeStats();

        // Step 3: Get relevant stats for this opportunity
        Map<String, Object> relevantStats = getRelevantStats(extractedAttrs, stats, qualStats);

        // Step 4: Find similar opportunities
        List<Map<String, Object>> wonDocs = findSimilarOpportunities(userInput, 'won', 10);
        List<Map<String, Object>> lostDocs = findSimilarOpportunities(userInput, 'lost', 10);

        // Step 5: Build context
        String contextMsg = buildContext(userInput, extractedAttrs, wonDocs, lostDocs);

        // Step 6: Generate recommendations
        String recommendation = generateRecommendations(contextMsg, relevantStats);

        return new Map<String, Object>{
            'recommendation' => recommendation,
            'extracted_attrs' => extractedAttrs,
            'relevant_stats' => relevantStats,
            'won_matches' => wonDocs,
            'lost_matches' => lostDocs
        };
    }

    // Step 1: Extract attributes using LLM
    private static Map<String, Object> extractAttributes(String userInput) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(OPENAI_ENDPOINT + '/openai/deployments/' + CHAT_MODEL + '/chat/completions?api-version=2024-02-15-preview');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setHeader('api-key', OPENAI_API_KEY);

        Map<String, Object> requestBody = new Map<String, Object>{
            'messages' => new List<Map<String, String>>{
                new Map<String, String>{
                    'role' => 'system',
                    'content' => 'You are an attribute extractor. Parse the user prompt and extract: product (str or None), sector (str or None), region (str or None), sales_price (float or None), expected_revenue (float or None), current_rep (str or None). Return as JSON dict. ONLY extract explicitly mentioned values.'
                },
                new Map<String, String>{
                    'role' => 'user',
                    'content' => userInput
                }
            },
            'temperature' => 0.0,
            'max_tokens' => 200
        };

        req.setBody(JSON.serialize(requestBody));

        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() == 200) {
            Map<String, Object> response = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            List<Object> choices = (List<Object>) response.get('choices');
            Map<String, Object> choice = (Map<String, Object>) choices[0];
            Map<String, Object> message = (Map<String, Object>) choice.get('message');
            String content = (String) message.get('content');

            return (Map<String, Object>) JSON.deserializeUntyped(content);
        }

        return new Map<String, Object>();
    }

    // Step 2: Calculate statistics from Salesforce data
    private static Map<String, Object> calculateStatistics() {
        Map<String, Object> stats = new Map<String, Object>();

        // Overall win rate
        AggregateResult[] overallResults = [
            SELECT COUNT(Id) total,
                   SUM(CASE WHEN Deal_Stage__c = 'Won' THEN 1 ELSE 0 END) won_count
            FROM Opportunity
            WHERE Deal_Stage__c IN ('Won', 'Lost')
        ];

        Decimal totalCount = (Decimal) overallResults[0].get('total');
        Decimal wonCount = (Decimal) overallResults[0].get('won_count');
        Decimal overallWinRate = wonCount / totalCount;
        stats.put('overall_win_rate', overallWinRate);

        // Win rate by product
        Map<String, Map<String, Decimal>> productStats = new Map<String, Map<String, Decimal>>();
        AggregateResult[] productResults = [
            SELECT Product__c,
                   COUNT(Id) sample_size,
                   AVG(CASE WHEN Deal_Stage__c = 'Won' THEN 1.0 ELSE 0.0 END) win_rate
            FROM Opportunity
            WHERE Deal_Stage__c IN ('Won', 'Lost')
            GROUP BY Product__c
        ];

        Map<String, Object> productWinRates = new Map<String, Object>();
        Map<String, Object> productLifts = new Map<String, Object>();
        Map<String, Object> productSampleSizes = new Map<String, Object>();

        for (AggregateResult ar : productResults) {
            String product = (String) ar.get('Product__c');
            Decimal winRate = (Decimal) ar.get('win_rate');
            Integer sampleSize = (Integer) ar.get('sample_size');
            Decimal lift = winRate / overallWinRate;

            productWinRates.put(product, winRate);
            productLifts.put(product, lift);
            productSampleSizes.put(product, sampleSize);
        }

        stats.put('product', new Map<String, Object>{
            'win_rate' => productWinRates,
            'lift' => productLifts,
            'sample_size' => productSampleSizes
        });

        // Repeat similar logic for sector, region, sales_rep
        // ... (similar code for other categories)

        // Average revenue by product (won deals only)
        Map<String, Decimal> avgRevenueByProduct = new Map<String, Decimal>();
        AggregateResult[] revenueResults = [
            SELECT Product__c, AVG(Expected_Revenue__c) avg_revenue
            FROM Opportunity
            WHERE Deal_Stage__c = 'Won'
            GROUP BY Product__c
        ];

        for (AggregateResult ar : revenueResults) {
            String product = (String) ar.get('Product__c');
            Decimal avgRevenue = (Decimal) ar.get('avg_revenue');
            avgRevenueByProduct.put(product, avgRevenue);
        }
        stats.put('avg_revenue_by_product', avgRevenueByProduct);

        // Correlations (simplified - full implementation requires more complex calculation)
        stats.put('correlations', new Map<String, Decimal>{
            'sales_price' => -0.0234,
            'account_size' => 0.1523,
            'account_revenue' => 0.0891
        });

        // Sales cycle duration
        AggregateResult[] cycleResults = [
            SELECT AVG(Sales_Cycle_Duration__c) avg_cycle
            FROM Opportunity
            WHERE Deal_Stage__c = 'Won'
        ];
        Decimal avgCycleWon = (Decimal) cycleResults[0].get('avg_cycle');

        cycleResults = [
            SELECT AVG(Sales_Cycle_Duration__c) avg_cycle
            FROM Opportunity
            WHERE Deal_Stage__c = 'Lost'
        ];
        Decimal avgCycleLost = (Decimal) cycleResults[0].get('avg_cycle');

        stats.put('avg_cycle_days', new Map<String, Decimal>{
            'won' => avgCycleWon,
            'lost' => avgCycleLost
        });

        return stats;
    }

    // Generate embedding for text
    private static List<Decimal> generateEmbedding(String text) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(OPENAI_ENDPOINT + '/openai/deployments/' + EMBEDDING_MODEL + '/embeddings?api-version=2024-02-15-preview');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setHeader('api-key', OPENAI_API_KEY);

        Map<String, Object> requestBody = new Map<String, Object>{
            'input' => text
        };

        req.setBody(JSON.serialize(requestBody));

        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() == 200) {
            Map<String, Object> response = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            List<Object> data = (List<Object>) response.get('data');
            Map<String, Object> embeddingData = (Map<String, Object>) data[0];
            List<Object> embedding = (List<Object>) embeddingData.get('embedding');

            List<Decimal> result = new List<Decimal>();
            for (Object val : embedding) {
                result.add((Decimal) val);
            }
            return result;
        }

        return new List<Decimal>();
    }

    // Find similar opportunities using vector search
    private static List<Map<String, Object>> findSimilarOpportunities(String userInput, String stage, Integer topK) {
        // Generate embedding
        List<Decimal> embedding = generateEmbedding(userInput);

        // Call Azure Cognitive Search
        HttpRequest req = new HttpRequest();
        req.setEndpoint(SEARCH_ENDPOINT + '/indexes/' + SEARCH_INDEX + '/docs/search?api-version=2023-11-01');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setHeader('api-key', SEARCH_API_KEY);

        Map<String, Object> requestBody = new Map<String, Object>{
            'vectorQueries' => new List<Map<String, Object>>{
                new Map<String, Object>{
                    'kind' => 'vector',
                    'fields' => 'text_vector',
                    'vector' => embedding,
                    'k' => topK,
                    'exhaustive' => false
                }
            },
            'filter' => 'deal_stage eq \'' + stage + '\'',
            'select' => 'opportunity_id,content,deal_stage,product,account_sector,sales_rep,account_region,sales_price,revenue_from_deal,sales_cycle_duration,deal_value_ratio,Notes',
            'top' => topK
        };

        req.setBody(JSON.serialize(requestBody));

        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() == 200) {
            Map<String, Object> response = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            List<Object> values = (List<Object>) response.get('value');

            List<Map<String, Object>> results = new List<Map<String, Object>>();
            for (Object val : values) {
                results.add((Map<String, Object>) val);
            }
            return results;
        }

        return new List<Map<String, Object>>();
    }

    // Generate final recommendations
    private static String generateRecommendations(String contextMsg, Map<String, Object> relevantStats) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(OPENAI_ENDPOINT + '/openai/deployments/' + CHAT_MODEL + '/chat/completions?api-version=2024-02-15-preview');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setHeader('api-key', OPENAI_API_KEY);
        req.setTimeout(120000); // 2 minutes timeout

        String systemPrompt = 'You are a sales strategy expert. Analyze the opportunity and provide recommendations...'; // Full prompt from prompts.py
        String userPrompt = 'Based on the following details:\n' + contextMsg + '\n\nRELEVANT_STATS:\n' + JSON.serialize(relevantStats);

        Map<String, Object> requestBody = new Map<String, Object>{
            'messages' => new List<Map<String, String>>{
                new Map<String, String>{'role' => 'system', 'content' => systemPrompt},
                new Map<String, String>{'role' => 'user', 'content' => userPrompt}
            },
            'temperature' => 0.1,
            'max_tokens' => 4000,
            'seed' => 12345
        };

        req.setBody(JSON.serialize(requestBody));

        Http http = new Http();
        HttpResponse res = http.send(req);

        if (res.getStatusCode() == 200) {
            Map<String, Object> response = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            List<Object> choices = (List<Object>) response.get('choices');
            Map<String, Object> choice = (Map<String, Object>) choices[0];
            Map<String, Object> message = (Map<String, Object>) choice.get('message');
            return (String) message.get('content');
        }

        return 'Error generating recommendations';
    }
}
```

---

## Summary of Key Metrics and Calculations

### 1. Win Rate
```
Win Rate = (Number of Won Deals) / (Total Deals)
Example: 3150 won / 5000 total = 0.63 (63%)
```

### 2. Lift
```
Lift = (Category Win Rate) / (Overall Win Rate)
Example: Product "GTX Pro" win rate 68.23% / Overall 63% = 1.0830
Interpretation: 8.3% better than baseline
```

### 3. Uplift Percentage
```
Uplift % = ((New Lift - Current Lift) / Current Lift) × 100
Example: ((1.0830 - 0.9384) / 0.9384) × 100 = 15.41%
```

### 4. Estimated Win Rate
```
Estimated Win Rate = Baseline Win Rate × Lift
Example: 0.63 × 1.0830 = 0.6823 (68.23%)
```

### 5. Frequency (Qualitative)
```
Frequency = (Count of Pattern) / (Total Deals in Category)
Example: 2966 demo_success mentions / 4237 won deals = 0.6998 (69.98%)
```

### 6. Correlation (Pearson)
```
r = (n×ΣXY - ΣX×ΣY) / sqrt((n×ΣX² - (ΣX)²) × (n×ΣY² - (ΣY)²))
Where X = sales_price, Y = is_won (1 or 0)
```

---

## Important Notes

1. **API Rate Limits**: Azure OpenAI and Search have rate limits. Implement retry logic and caching.

2. **Timeout Settings**: LLM calls can take 10-30 seconds. Set appropriate timeouts (120 seconds recommended).

3. **Data Privacy**: Ensure compliance with data privacy regulations when sending opportunity data to external APIs.

4. **Error Handling**: Always implement try-catch blocks and fallback logic for API failures.

5. **Caching**: Cache statistics in Custom Metadata or Custom Settings to avoid recalculating on every request.

6. **Batch Processing**: For initial setup, use batch Apex to generate embeddings for all historical opportunities.

7. **Governor Limits**: Be mindful of Salesforce governor limits (heap size, CPU time, callout limits).

---

## Next Steps

1. Set up Azure OpenAI and Azure Cognitive Search services
2. Configure Remote Site Settings in Salesforce
3. Create custom fields on Opportunity object
4. Implement Apex classes for statistics calculation
5. Build batch job to generate embeddings for historical data
6. Create Lightning Web Component or Visualforce page for UI
7. Test with sample opportunities
8. Deploy to production

---

## Support and Resources

- **Azure OpenAI Documentation**: https://learn.microsoft.com/en-us/azure/ai-services/openai/
- **Azure Cognitive Search**: https://learn.microsoft.com/en-us/azure/search/
- **Salesforce Apex REST Callouts**: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_restful_http.htm

---

**Document Version**: 1.0
**Last Updated**: 2025-11-11
**Author**: Sales Prediction POC Team


