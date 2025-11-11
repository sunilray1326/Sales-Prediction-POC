"""
SalesAdvisorEngine - Business logic for Sales Recommendation Advisor
Handles all Azure OpenAI and Azure Cognitive Search interactions
"""

import os
import json
from pathlib import Path
from collections import Counter
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

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
    Handles all Azure OpenAI and Azure Cognitive Search operations.
    """
    
    def __init__(self):
        """Initialize Azure clients and load statistics from JSON files."""
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
        
        # Initialize Azure OpenAI client
        self.openai_client = AzureOpenAI(
            api_key=self.config['OPEN_AI_KEY'],
            azure_endpoint=self.config['OPEN_AI_ENDPOINT'],
            api_version="2024-12-01-preview"
        )
        
        # Initialize Azure Cognitive Search client
        self.search_client = SearchClient(
            endpoint=self.config['SEARCH_ENDPOINT'],
            index_name=self.config['INDEX_NAME'],
            credential=AzureKeyCredential(self.config['SEARCH_KEY'])
        )
        
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
            
            # Step 3: Find similar opportunities
            won_docs = self._get_top_matches(user_prompt, stage_filter="won", top_k=10)
            lost_docs = self._get_top_matches(user_prompt, stage_filter="lost", top_k=10)
            
            # Step 4: Build context
            context_msg = (
                f"User Opportunity:\n{user_prompt}\n"
                f"Extracted Attributes: {json.dumps(extracted_attrs)}\n\n"
                f"=== Top 10 Successful Matches ===\n{self._format_docs(won_docs)}\n\n"
                f"=== Top 10 Failed Matches ===\n{self._format_docs(lost_docs)}\n"
            )
            
            # Step 5: Generate recommendation
            conversation = [
                {
                    "role": "system",
                    "content": get_sales_strategy_system_prompt()
                },
                {
                    "role": "user",
                    "content": get_sales_strategy_user_prompt(context_msg, relevant_stats)
                }
            ]
            
            recommendation = self._llm_chat(
                conversation,
                temperature=0.1,
                seed=12345
            )
            
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
        """Generate embedding vector for text using Azure OpenAI."""
        response = self.openai_client.embeddings.create(
            model=self.config['EMBEDDING_MODEL'],
            input=text
        )
        return response.data[0].embedding
    
    def _get_top_matches(self, prompt, stage_filter, top_k=10):
        """Find top K similar opportunities using vector search."""
        embedding = self._embed_text(prompt)
        filter_expr = f"deal_stage eq '{stage_filter}'"
        results = self.search_client.search(
            search_text=None,
            vector_queries=[
                {
                    "kind": "vector",
                    "fields": "text_vector",
                    "vector": embedding,
                    "k": top_k,
                    "exhaustive": False
                }
            ],
            filter=filter_expr,
            select=[
                "opportunity_id", "content", "deal_stage", "product", "account_sector",
                "sales_rep", "account_region", "sales_price", "revenue_from_deal",
                "sales_cycle_duration", "deal_value_ratio", "Notes"
            ],
            top=top_k
        )
        return [doc for doc in results]
    
    def _format_docs(self, docs):
        """Format document list into readable string for LLM context."""
        return "\n".join([
            f"{doc.get('opportunity_id')} | Stage: {doc.get('deal_stage').capitalize()} | "
            f"Rep: {doc.get('sales_rep')} | Product: {doc.get('product')} | "
            f"Sector: {doc.get('account_sector')} | Region: {doc.get('account_region')} | "
            f"Price: {doc.get('sales_price')} | Revenue: {doc.get('revenue_from_deal')} | "
            f"Sales Cycle Duration: {doc.get('sales_cycle_duration')} days | "
            f"Deal Value Ratio: {doc.get('deal_value_ratio')} | "
            f"Note: {doc.get('Notes', '')[:400]}..."
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
        response = self.openai_client.chat.completions.create(
            model=self.config['CHAT_MODEL'],
            messages=extraction_prompt,
            temperature=0.0,
            max_tokens=200
        )
        try:
            extracted = json.loads(response.choices[0].message.content)
            
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
        """Chat with LLM."""
        params = {
            "model": self.config['CHAT_MODEL'],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4000
        }
        if seed is not None:
            params["seed"] = seed
        
        response = self.openai_client.chat.completions.create(**params)
        return response.choices[0].message.content
    
    def _case_insensitive_lookup(self, search_value, data_dict):
        """Perform case-insensitive lookup in a dictionary."""
        if not search_value or not data_dict:
            return None

        lowercase_map = {k.lower(): k for k in data_dict.keys()}
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
                prod_sec_key = self._case_insensitive_lookup(
                    f"{product_key}_{sector_key}",
                    self.stats["product_sector_win_rates"]
                )
                relevant["product_sector"] = {}
                if prod_sec_key:
                    relevant["product_sector"][prod_sec_key] = self.stats["product_sector_win_rates"][prod_sec_key]

                # Find alternative product-sector combinations
                sec_combos = []
                for k, v in self.stats["product_sector_win_rates"].items():
                    parts = k.split("_", 1)
                    if len(parts) == 2 and parts[1].lower() == sector_key.lower():
                        sec_combos.append((parts[0], v))

                if sec_combos:
                    alts = sorted(sec_combos, key=lambda x: x[1], reverse=True)[:3]
                    for alt_prod, wr in alts:
                        if alt_prod.lower() != product_key.lower() if product_key else True:
                            combo_key = self._case_insensitive_lookup(
                                f"{alt_prod}_{sector_key}",
                                self.stats["product_sector_win_rates"]
                            )
                            if combo_key:
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

        # Sales Rep stats (case-insensitive lookup)
        rep_stats = self.stats["sales_rep"]
        current_rep = extracted_attrs.get("current_rep")
        current_rep_key = self._case_insensitive_lookup(current_rep, rep_stats["win_rate"])
        if current_rep_key:
            relevant["current_rep"] = {
                "name": current_rep_key,
                "win_rate": rep_stats["win_rate"][current_rep_key],
                "lift": rep_stats["lift"][current_rep_key],
                "sample_size": rep_stats["sample_size"][current_rep_key]
            }
        top_reps = sorted(
            [(k, rep_stats["lift"][k], rep_stats["win_rate"][k], rep_stats["sample_size"][k])
             for k in rep_stats["lift"]],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        relevant["top_reps"] = [
            {"name": name, "win_rate": wr, "lift": lift, "sample_size": ss}
            for name, lift, wr, ss in top_reps
        ]

        # Simulations
        simulations = []
        baseline_wr = relevant["overall_win_rate"]
        if "sector" in relevant and sector_key:
            sec_lift = relevant["sector"][sector_key]["lift"]
            simulations.append({
                "description": f"Baseline adjusted for {sector_key} sector",
                "estimated_win_rate": baseline_wr * sec_lift,
                "uplift_percent": (sec_lift - 1) * 100
            })
        if "products" in relevant:
            for prod, prod_data in relevant["products"].items():
                lift = prod_data["lift"]
                simulations.append({
                    "description": f"Switch to {prod}",
                    "estimated_win_rate": baseline_wr * lift,
                    "uplift_percent": (lift - 1) * 100,
                    "revenue_estimate": self.stats["avg_revenue_by_product"].get(prod, 0)
                })
        if "top_reps" in relevant:
            for rep in relevant["top_reps"]:
                simulations.append({
                    "description": f"Assign to {rep['name']}",
                    "estimated_win_rate": baseline_wr * rep["lift"],
                    "uplift_percent": (rep["lift"] - 1) * 100,
                    "confidence": "High" if rep["sample_size"] > 200 else "Medium"
                })

        # Qualitative Insights (case-insensitive lookup)
        relevant["qualitative_insights"] = {}
        qual_sector_key = self._case_insensitive_lookup(sector, self.qual_stats.get("segmented", {}))
        if qual_sector_key:
            # Segmented data is now pre-normalized with correct frequencies
            seg_data = self.qual_stats["segmented"][qual_sector_key]
            normalized_seg = {}
            for cat_type in ["win_drivers", "loss_risks"]:
                if cat_type in seg_data:
                    # Filter categories with frequency > 0.1 (10%)
                    filtered = {k: v for k, v in seg_data[cat_type].items() if v["frequency"] > 0.1}
                    normalized_seg[cat_type] = filtered
            relevant["qualitative_insights"] = normalized_seg
        else:
            # Fallback to overall stats if sector not found
            for cat_type in ["win_drivers", "loss_risks"]:
                top_cats = Counter({
                    k: v["frequency"]
                    for k, v in self.qual_stats[cat_type].items()
                    if v["frequency"] > 0.1
                }).most_common(3)
                relevant["qualitative_insights"][cat_type] = {
                    cat[0]: self.qual_stats[cat_type][cat[0]] for cat in top_cats
                }

        # Qualitative lift estimate
        if "loss_risks" in relevant["qualitative_insights"] and relevant["qualitative_insights"]["loss_risks"]:
            top_risk = max(
                relevant["qualitative_insights"]["loss_risks"],
                key=lambda k: relevant["qualitative_insights"]["loss_risks"][k]["frequency"]
            )
            top_risk_freq = relevant["qualitative_insights"]["loss_risks"][top_risk]["frequency"]
            sim_prompt = [
                {
                    "role": "system",
                    "content": get_uplift_estimation_prompt()
                },
                {
                    "role": "user",
                    "content": get_uplift_estimation_user_prompt(top_risk, top_risk_freq, sector_key)
                }
            ]
            try:
                uplift_str = self._llm_chat(sim_prompt, temperature=0.0, seed=12345)
                qual_uplift = float(uplift_str.strip("%"))
                relevant["qual_lift_estimate"] = qual_uplift
                simulations.append({
                    "description": f"Address top qual risk '{top_risk}'",
                    "estimated_win_rate": baseline_wr * (1 + qual_uplift / 100),
                    "uplift_percent": qual_uplift,
                    "from_qual": True
                })
            except ValueError:
                relevant["qual_lift_estimate"] = (1 - top_risk_freq) * 10

        # Price/Revenue checks
        price = extracted_attrs.get("sales_price")
        if price:
            corr_price = self.stats["correlations"]["sales_price"]
            relevant["price_insight"] = (
                f"Current price {price}: Correlation with win rate {corr_price:.4f} "
                f"(negative suggests lower price may help)."
            )
        rev = extracted_attrs.get("expected_revenue")
        if rev:
            relevant["revenue_insight"] = (
                f"Expected revenue {rev}: Compare to product avgs for uplift potential."
            )

        # Pre-sort data for deterministic LLM selection
        simulations = sorted(
            simulations,
            key=lambda x: x.get("uplift_percent", 0),
            reverse=True
        )

        # Sort win_drivers by frequency
        if "win_drivers" in relevant["qualitative_insights"]:
            win_drivers_sorted = dict(
                sorted(
                    relevant["qualitative_insights"]["win_drivers"].items(),
                    key=lambda x: x[1]["frequency"],
                    reverse=True
                )
            )
            relevant["qualitative_insights"]["win_drivers"] = win_drivers_sorted

        # Sort loss_risks by frequency
        if "loss_risks" in relevant["qualitative_insights"]:
            loss_risks_sorted = dict(
                sorted(
                    relevant["qualitative_insights"]["loss_risks"].items(),
                    key=lambda x: x[1]["frequency"],
                    reverse=True
                )
            )
            relevant["qualitative_insights"]["loss_risks"] = loss_risks_sorted

        # Pre-calculate win probability improvements for top 3 recommendations
        win_probability_improvements = []
        for i in range(min(3, len(simulations))):
            sim = simulations[i]
            source_type = "Qualitative insight" if sim.get("from_qual", False) else "Quantitative simulation"
            win_probability_improvements.append({
                "rank": i + 1,
                "recommendation": sim["description"],
                "uplift_percent": sim["uplift_percent"],
                "confidence": sim.get("confidence", "Medium"),
                "source_type": source_type,
                "explanation": (
                    f"This recommendation is based on {source_type.lower()} showing "
                    f"{sim['uplift_percent']:.2f}% improvement in win rate."
                )
            })

        relevant["win_probability_improvements"] = win_probability_improvements
        relevant["simulations"] = simulations
        return relevant

