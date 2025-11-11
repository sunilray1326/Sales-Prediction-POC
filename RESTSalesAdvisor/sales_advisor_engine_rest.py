"""
SalesAdvisorEngine - Business logic for Sales Recommendation Advisor
REST API version - Uses direct HTTP calls instead of Azure SDK libraries
"""

import os
import json
import requests
from pathlib import Path
from collections import Counter
from dotenv import load_dotenv

from prompts import (
    get_attribute_extraction_prompt,
    get_uplift_estimation_prompt,
    get_uplift_estimation_user_prompt,
    get_sales_strategy_system_prompt,
    get_sales_strategy_user_prompt
)


class SalesAdvisorEngine:
    """
    Main business logic engine for Sales Recommendation Advisor.
    Uses REST API calls for Azure OpenAI and Azure Cognitive Search.
    """
    
    def __init__(self):
        """Initialize configuration and load statistics from JSON files."""
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self.config = {
            'OPEN_AI_KEY': os.getenv("OPEN_AI_KEY"),
            'OPEN_AI_ENDPOINT': os.getenv("OPEN_AI_ENDPOINT"),
            'SEARCH_ENDPOINT': os.getenv("SEARCH_ENDPOINT"),
            'SEARCH_KEY': os.getenv("SEARCH_KEY"),
            'INDEX_NAME': os.getenv("INDEX_NAME"),
            'EMBEDDING_MODEL': os.getenv("EMBEDDING_MODEL"),
            'CHAT_MODEL': os.getenv("CHAT_MODEL")
        }
        
        # Validate configuration
        missing_keys = [k for k, v in self.config.items() if not v]
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
        
        # API version for Azure OpenAI
        self.openai_api_version = "2024-12-01-preview"
        
        # API version for Azure Cognitive Search
        self.search_api_version = "2023-11-01"
        
        # Build base URLs
        self.openai_base_url = self.config['OPEN_AI_ENDPOINT'].rstrip('/')
        self.search_base_url = self.config['SEARCH_ENDPOINT'].rstrip('/')
        
        # Load statistics
        script_dir = Path(__file__).parent
        with open(script_dir / "quantitative_stats.json", "r", encoding="utf-8") as f:
            self.stats = json.load(f)
        with open(script_dir / "qualitative_stats.json", "r", encoding="utf-8") as f:
            self.qual_stats = json.load(f)
    
    def analyze_opportunity(self, user_prompt):
        """
        Main method: Analyze a sales opportunity and return recommendations.
        
        Args:
            user_prompt (str): User's opportunity description
        
        Returns:
            dict: Structured response with the following keys:
                - success (bool): Whether analysis succeeded
                - error_message (str): Error message if failed
                - extracted_attributes (dict): Extracted attributes from prompt
                - relevant_stats (dict): Relevant statistics
                - recommendation (str): AI-generated recommendation
                - won_matches (list): Similar won opportunities
                - lost_matches (list): Similar lost opportunities
        """
        try:
            # Step 1: Extract attributes
            extracted_attrs = self._extract_attributes(user_prompt)
            
            # Check if extraction failed
            if not extracted_attrs or all(v is None for v in extracted_attrs.values()):
                return {
                    "success": False,
                    "error_message": "Failed to extract attributes from the opportunity description. Please provide more details about the product, sector, region, or sales representative.",
                    "extracted_attributes": extracted_attrs,
                    "relevant_stats": None,
                    "recommendation": None,
                    "won_matches": None,
                    "lost_matches": None
                }
            
            # Step 2: Get relevant statistics
            relevant_stats = self._get_relevant_stats(extracted_attrs)
            
            # Step 3: Find similar won and lost opportunities
            won_docs = self._get_top_matches(user_prompt, "won", top_k=10)
            lost_docs = self._get_top_matches(user_prompt, "lost", top_k=10)
            
            # Step 4: Build context message
            context_msg = (
                f"User Opportunity:\n{user_prompt}\n"
                f"Extracted Attributes: {json.dumps(extracted_attrs)}\n\n"
                f"=== Top 10 Successful Matches ===\n{self._format_docs(won_docs)}\n\n"
                f"=== Top 10 Failed Matches ===\n{self._format_docs(lost_docs)}\n"
            )
            
            # Step 5: Generate recommendation
            messages = [
                {
                    "role": "system",
                    "content": get_sales_strategy_system_prompt()
                },
                {
                    "role": "user",
                    "content": get_sales_strategy_user_prompt(context_msg, relevant_stats)
                }
            ]
            
            recommendation = self._llm_chat(messages, temperature=0.1, seed=12345)
            
            return {
                "success": True,
                "error_message": None,
                "extracted_attributes": extracted_attrs,
                "relevant_stats": relevant_stats,
                "recommendation": recommendation,
                "won_matches": won_docs,
                "lost_matches": lost_docs
            }
            
        except Exception as e:
            return {
                "success": False,
                "error_message": f"Error during analysis: {str(e)}",
                "extracted_attributes": None,
                "relevant_stats": None,
                "recommendation": None,
                "won_matches": None,
                "lost_matches": None
            }
    
    def _embed_text(self, text):
        """Generate embedding vector for text using Azure OpenAI REST API."""
        url = f"{self.openai_base_url}/openai/deployments/{self.config['EMBEDDING_MODEL']}/embeddings?api-version={self.openai_api_version}"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.config['OPEN_AI_KEY']
        }
        
        payload = {
            "input": text
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result['data'][0]['embedding']
    
    def _get_top_matches(self, prompt, stage_filter, top_k=10):
        """Find top K similar opportunities using Azure Cognitive Search REST API."""
        embedding = self._embed_text(prompt)
        
        url = f"{self.search_base_url}/indexes/{self.config['INDEX_NAME']}/docs/search?api-version={self.search_api_version}"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.config['SEARCH_KEY']
        }
        
        payload = {
            "search": None,
            "vectorQueries": [
                {
                    "kind": "vector",
                    "fields": "text_vector",
                    "vector": embedding,
                    "k": top_k,
                    "exhaustive": False
                }
            ],
            "filter": f"deal_stage eq '{stage_filter}'",
            "select": "opportunity_id,content,deal_stage,product,account_sector,sales_rep,account_region,sales_price,revenue_from_deal,sales_cycle_duration,deal_value_ratio,Notes",
            "top": top_k
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result.get('value', [])
    
    def _format_docs(self, docs):
        """Format document list into readable string for LLM context."""
        return "\n".join([
            f"{doc.get('opportunity_id')} | Stage: {doc.get('deal_stage').capitalize()} | "
            f"Rep: {doc.get('sales_rep')} | Product: {doc.get('product')} | "
            f"Sector: {doc.get('account_sector')} | Region: {doc.get('account_region')} | "
            f"Price: {doc.get('sales_price')} | Revenue: {doc.get('revenue_from_deal')} | "
            f"Sales Cycle Duration: {doc.get('sales_cycle_duration')} days | "
            f"Deal Value Ratio: {doc.get('deal_value_ratio')} | "
            f"Notes: {doc.get('Notes')}"
            for doc in docs
        ])
    
    def _extract_attributes(self, prompt):
        """Use LLM to extract key attributes from the user prompt."""
        extraction_prompt = [
            {
                "role": "system",
                "content": get_attribute_extraction_prompt()
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response_text = self._llm_chat(extraction_prompt, temperature=0.0, seed=12345)
        
        try:
            extracted = json.loads(response_text)
            
            # Validation: Remove hallucinated price if not mentioned in prompt
            if extracted.get("sales_price") is not None:
                price_keywords = ["$", "price", "cost", "dollar", "usd"]
                if not any(keyword in prompt.lower() for keyword in price_keywords):
                    extracted["sales_price"] = None
            
            # Validation: Remove hallucinated revenue if not mentioned in prompt
            if extracted.get("expected_revenue") is not None:
                revenue_keywords = ["revenue", "expected", "forecast"]
                if not any(keyword in prompt.lower() for keyword in revenue_keywords):
                    if "$" not in prompt:
                        extracted["expected_revenue"] = None
            
            return extracted
        except json.JSONDecodeError:
            return {}
    
    def _llm_chat(self, messages, temperature=0.8, seed=None):
        """Chat with LLM using Azure OpenAI REST API."""
        url = f"{self.openai_base_url}/openai/deployments/{self.config['CHAT_MODEL']}/chat/completions?api-version={self.openai_api_version}"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.config['OPEN_AI_KEY']
        }
        
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4000
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _case_insensitive_lookup(self, search_value, data_dict):
        """Perform case-insensitive lookup in a dictionary."""
        if not search_value or not data_dict:
            return None

        # Create a mapping of lowercase keys to actual keys
        lowercase_map = {k.lower(): k for k in data_dict.keys()}

        # Look up using lowercase
        return lowercase_map.get(search_value.lower())

    def _get_relevant_stats(self, extracted_attrs):
        """Filter and summarize relevant stats from JSON based on extracted attributes."""
        relevant = {
            "overall_win_rate": self.stats["overall_win_rate"],
            "avg_cycle_days": self.stats["avg_cycle_days"],
            "correlations": self.stats["correlations"]
        }

        # Product-specific (case-insensitive lookup)
        product = extracted_attrs.get("product")
        product_key = self._case_insensitive_lookup(product, self.stats["product"]["win_rate"])
        if product_key:
            prod_stats = self.stats["product"]
            relevant["products"] = {
                product_key: {
                    "win_rate": prod_stats["win_rate"][product_key],
                    "lift": prod_stats["lift"][product_key]
                }
            }
            alts = sorted(
                [(k, prod_stats["lift"][k]) for k in prod_stats["lift"] if k.lower() != product_key.lower()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            for alt_prod, _ in alts:
                relevant["products"][alt_prod] = {
                    "win_rate": prod_stats["win_rate"][alt_prod],
                    "lift": prod_stats["lift"][alt_prod]
                }
            relevant["avg_revenue_by_product"] = {k: self.stats["avg_revenue_by_product"][k] for k in relevant["products"]}

        # Sector-specific (case-insensitive lookup)
        sector = extracted_attrs.get("sector")
        sector_key = self._case_insensitive_lookup(sector, self.stats["account_sector"]["win_rate"])

        if sector_key:
            sec_stats = self.stats["account_sector"]
            relevant["sector"] = {
                sector_key: {
                    "win_rate": sec_stats["win_rate"][sector_key],
                    "lift": sec_stats["lift"][sector_key]
                }
            }
            alts = sorted(
                [(k, sec_stats["lift"][k]) for k in sec_stats["lift"] if k.lower() != sector_key.lower()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            for alt_sec, _ in alts:
                relevant["sector"][alt_sec] = {
                    "win_rate": sec_stats["win_rate"][alt_sec],
                    "lift": sec_stats["lift"][alt_sec]
                }

            # Product-sector combinations (case-insensitive)
            if product_key:
                prod_sec_key = self._case_insensitive_lookup(f"{product_key}_{sector_key}", self.stats["product_sector_win_rates"])
                relevant["product_sector"] = {}
                if prod_sec_key:
                    relevant["product_sector"][prod_sec_key] = self.stats["product_sector_win_rates"][prod_sec_key]

                # Find alternative product-sector combinations
                sec_combos = []
                for k, v in self.stats["product_sector_win_rates"].items():
                    parts = k.split("_", 1)
                    if len(parts) == 2 and parts[1].lower() == sector_key.lower():
                        sec_combos.append((parts[0], v))

                sec_combos.sort(key=lambda x: x[1], reverse=True)
                for alt_prod, wr in sec_combos[:3]:
                    if alt_prod.lower() != product_key.lower():
                        combo_key = f"{alt_prod}_{sector_key}"
                        relevant["product_sector"][combo_key] = wr

        # Region-specific (case-insensitive lookup)
        region = extracted_attrs.get("region")
        region_key = self._case_insensitive_lookup(region, self.stats["account_region"]["win_rate"])
        if region_key:
            reg_stats = self.stats["account_region"]
            relevant["region"] = {
                region_key: {
                    "win_rate": reg_stats["win_rate"][region_key],
                    "lift": reg_stats["lift"][region_key]
                }
            }
            alts = sorted(
                [(k, reg_stats["lift"][k]) for k in reg_stats["lift"] if k.lower() != region_key.lower()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            for alt_reg, _ in alts:
                relevant["region"][alt_reg] = {
                    "win_rate": reg_stats["win_rate"][alt_reg],
                    "lift": reg_stats["lift"][alt_reg]
                }

        # Sales rep-specific (case-insensitive lookup)
        current_rep = extracted_attrs.get("current_rep")
        rep_key = self._case_insensitive_lookup(current_rep, self.stats["sales_rep"]["win_rate"])
        if rep_key:
            rep_stats = self.stats["sales_rep"]
            relevant["sales_rep"] = {
                rep_key: {
                    "win_rate": rep_stats["win_rate"][rep_key],
                    "lift": rep_stats["lift"][rep_key]
                }
            }
            alts = sorted(
                [(k, rep_stats["lift"][k]) for k in rep_stats["lift"] if k.lower() != rep_key.lower()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            for alt_rep, _ in alts:
                relevant["sales_rep"][alt_rep] = {
                    "win_rate": rep_stats["win_rate"][alt_rep],
                    "lift": rep_stats["lift"][alt_rep]
                }

        # Price comparison
        sales_price = extracted_attrs.get("sales_price")
        if sales_price is not None:
            relevant["price_vs_avg"] = sales_price / self.stats["avg_price"] if self.stats["avg_price"] > 0 else None
        else:
            relevant["price_vs_avg"] = None

        # Revenue comparison
        expected_revenue = extracted_attrs.get("expected_revenue")
        if expected_revenue is not None:
            relevant["revenue_vs_avg"] = expected_revenue / self.stats["avg_revenue"] if self.stats["avg_revenue"] > 0 else None
        else:
            relevant["revenue_vs_avg"] = None

        # Qualitative insights
        relevant["qualitative_insights"] = {}

        # Product insights
        if product_key:
            prod_qual = self.qual_stats.get("product", {}).get(product_key, {})
            if prod_qual:
                relevant["qualitative_insights"]["product"] = prod_qual

        # Sector insights
        if sector_key:
            sec_qual = self.qual_stats.get("account_sector", {}).get(sector_key, {})
            if sec_qual:
                relevant["qualitative_insights"]["sector"] = sec_qual

        # Region insights
        if region_key:
            reg_qual = self.qual_stats.get("account_region", {}).get(region_key, {})
            if reg_qual:
                relevant["qualitative_insights"]["region"] = reg_qual

        # Sales rep insights
        if rep_key:
            rep_qual = self.qual_stats.get("sales_rep", {}).get(rep_key, {})
            if rep_qual:
                relevant["qualitative_insights"]["sales_rep"] = rep_qual

        return relevant

