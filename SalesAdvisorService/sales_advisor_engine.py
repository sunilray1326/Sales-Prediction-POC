"""
SalesAdvisorEngine - Business logic for Sales Recommendation Advisor
Handles all Azure OpenAI and Azure Cognitive Search interactions
"""

import os
import json
import logging
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

    # Class-level logging configuration
    _logging_configured = False
    LOG_FILE = "logs/sales_advisor.log"

    @classmethod
    def _configure_logging(cls, log_level=logging.INFO):
        """Configure logging once at class level."""
        if not cls._logging_configured:
            # Create logs directory if it doesn't exist
            log_dir = os.path.dirname(cls.LOG_FILE)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Configure logging with file and console output
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                handlers=[
                    logging.FileHandler(cls.LOG_FILE),
                    logging.StreamHandler()
                ]
            )
            cls._logging_configured = True

    def __init__(self, log_level=logging.INFO):
        """
        Initialize Azure clients and load statistics from JSON files.

        Args:
            log_level: Logging level (default: logging.INFO)
        """
        # Configure logging (only happens once)
        self._configure_logging(log_level)

        # Setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        self.logger.info("=" * 80)
        self.logger.info("Initializing SalesAdvisorEngine")
        self.logger.info(f"Log file: {self.LOG_FILE}")
        self.logger.info("=" * 80)

        # Load environment variables
        load_dotenv()
        self.logger.info("Environment variables loaded")

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

        # Log configuration (mask sensitive data)
        self.logger.info("Configuration loaded:")
        self.logger.info(f"  - OpenAI Endpoint: {self.config['OPEN_AI_ENDPOINT']}")
        self.logger.info(f"  - Search Endpoint: {self.config['SEARCH_ENDPOINT']}")
        self.logger.info(f"  - Index Name: {self.config['INDEX_NAME']}")
        self.logger.info(f"  - Embedding Model: {self.config['EMBEDDING_MODEL']}")
        self.logger.info(f"  - Chat Model: {self.config['CHAT_MODEL']}")

        # Validate configuration
        missing_keys = [k for k, v in self.config.items() if not v]
        if missing_keys:
            self.logger.error(f"Missing required environment variables: {', '.join(missing_keys)}")
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")

        self.logger.info("Configuration validated successfully")

        # Initialize Azure OpenAI client
        try:
            self.openai_client = AzureOpenAI(
                api_key=self.config['OPEN_AI_KEY'],
                azure_endpoint=self.config['OPEN_AI_ENDPOINT'],
                api_version="2024-12-01-preview"
            )
            self.logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
            raise

        # Initialize Azure Cognitive Search client
        try:
            self.search_client = SearchClient(
                endpoint=self.config['SEARCH_ENDPOINT'],
                index_name=self.config['INDEX_NAME'],
                credential=AzureKeyCredential(self.config['SEARCH_KEY'])
            )
            self.logger.info("Azure Cognitive Search client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure Cognitive Search client: {str(e)}")
            raise

        # Load statistics
        script_dir = Path(__file__).parent
        try:
            with open(script_dir / "quantitative_stats.json", "r", encoding="utf-8") as f:
                self.stats = json.load(f)
            self.logger.info(f"Loaded quantitative stats: {len(self.stats)} top-level keys")

            with open(script_dir / "qualitative_stats.json", "r", encoding="utf-8") as f:
                self.qual_stats = json.load(f)
            self.logger.info(f"Loaded qualitative stats: {len(self.qual_stats)} top-level keys")
        except Exception as e:
            self.logger.error(f"Failed to load statistics files: {str(e)}")
            raise

        self.logger.info("SalesAdvisorEngine initialization complete")
        self.logger.info("=" * 80)

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
        self.logger.info("=" * 80)
        self.logger.info("Starting opportunity analysis")
        self.logger.info(f"User prompt length: {len(user_prompt)} characters")
        self.logger.debug(f"User prompt: {user_prompt[:200]}...")  # Log first 200 chars

        try:
            # Step 1: Extract attributes
            self.logger.info("Step 1: Extracting attributes from user prompt")
            extracted_attrs = self._extract_attributes(user_prompt)
            self.logger.info(f"Extracted attributes: {json.dumps(extracted_attrs, indent=2)}")

            # Check if extraction failed
            if not extracted_attrs or all(v is None for v in extracted_attrs.values()):
                self.logger.warning("Attribute extraction failed - all values are None")
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
            self.logger.info("Step 2: Retrieving relevant statistics")
            relevant_stats = self._get_relevant_stats(extracted_attrs)
            self.logger.info(f"Retrieved stats with {len(relevant_stats)} top-level keys")

            # Step 3: Find similar opportunities
            self.logger.info("Step 3: Finding similar opportunities via vector search")
            won_docs = self._get_top_matches(user_prompt, stage_filter="won", top_k=10)
            self.logger.info(f"Found {len(won_docs)} similar won opportunities")

            lost_docs = self._get_top_matches(user_prompt, stage_filter="lost", top_k=10)
            self.logger.info(f"Found {len(lost_docs)} similar lost opportunities")

            # Step 4: Build context
            self.logger.info("Step 4: Building context for LLM")
            context_msg = (
                f"User Opportunity:\n{user_prompt}\n"
                f"Extracted Attributes: {json.dumps(extracted_attrs)}\n\n"
                f"=== Top 10 Successful Matches ===\n{self._format_docs(won_docs)}\n\n"
                f"=== Top 10 Failed Matches ===\n{self._format_docs(lost_docs)}\n"
            )
            self.logger.debug(f"Context message length: {len(context_msg)} characters")

            # Step 5: Generate recommendation
            self.logger.info("Step 5: Generating recommendation via LLM")
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
            self.logger.info(f"Recommendation generated successfully (length: {len(recommendation)} characters)")

            self.logger.info("Opportunity analysis completed successfully")
            self.logger.info("=" * 80)

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
            self.logger.error(f"Error during opportunity analysis: {str(e)}", exc_info=True)
            self.logger.info("=" * 80)
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
        self.logger.info("=" * 80)
        self.logger.info("AZURE OPENAI EMBEDDING REQUEST")
        self.logger.info("=" * 80)

        try:
            # Log request
            self.logger.info("REQUEST PARAMETERS:")
            self.logger.info(f"  Model: {self.config['EMBEDDING_MODEL']}")
            self.logger.info(f"  Input Text Length: {len(text)} chars")
            self.logger.info(f"  Input Text Preview (first 200 chars):")
            self.logger.info(f"    {text[:200]}{'...' if len(text) > 200 else ''}")

            response = self.openai_client.embeddings.create(
                model=self.config['EMBEDDING_MODEL'],
                input=text
            )

            # Log response
            embedding_dim = len(response.data[0].embedding)
            self.logger.info("-" * 80)
            self.logger.info("AZURE OPENAI EMBEDDING RESPONSE")
            self.logger.info("-" * 80)
            self.logger.info(f"  Embedding Dimension: {embedding_dim}")
            self.logger.info(f"  Model: {response.model}")

            # Log token usage if available
            if hasattr(response, 'usage') and response.usage:
                self.logger.info(f"  Token Usage: {response.usage.total_tokens}")

            self.logger.info("=" * 80)

            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}", exc_info=True)
            raise
    
    def _get_top_matches(self, prompt, stage_filter, top_k=10):
        """Find top K similar opportunities using vector search."""
        self.logger.info("=" * 80)
        self.logger.info("AZURE COGNITIVE SEARCH REQUEST")
        self.logger.info("=" * 80)

        try:
            # Generate embedding
            embedding = self._embed_text(prompt)

            # Build filter expression
            filter_expr = f"deal_stage eq '{stage_filter}'"

            # Log full request parameters
            self.logger.info("REQUEST PARAMETERS:")
            self.logger.info(f"  Index Name: {self.config['INDEX_NAME']}")
            self.logger.info(f"  Search Type: Vector Search")
            self.logger.info(f"  Vector Field: text_vector")
            self.logger.info(f"  Top K: {top_k}")
            self.logger.info(f"  Filter: {filter_expr}")
            self.logger.info(f"  Embedding Dimension: {len(embedding)}")
            self.logger.info(f"  Exhaustive Search: False")
            self.logger.info(f"  Selected Fields: opportunity_id, content, deal_stage, product, account_sector, sales_rep, account_region, sales_price, revenue_from_deal, sales_cycle_duration, deal_value_ratio, Notes")

            # Execute search
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

            docs = [doc for doc in results]

            # Log response
            self.logger.info("-" * 80)
            self.logger.info("AZURE COGNITIVE SEARCH RESPONSE")
            self.logger.info("-" * 80)
            self.logger.info(f"  Results Returned: {len(docs)}")

            # Log detailed results
            if docs:
                self.logger.info("  Top Results:")
                for i, doc in enumerate(docs[:5], 1):  # Log top 5
                    self.logger.info(f"    Result {i}:")
                    self.logger.info(f"      Opportunity ID: {doc.get('opportunity_id')}")
                    self.logger.info(f"      Product: {doc.get('product')}")
                    self.logger.info(f"      Sector: {doc.get('account_sector')}")
                    self.logger.info(f"      Region: {doc.get('account_region')}")
                    self.logger.info(f"      Stage: {doc.get('deal_stage')}")
                    self.logger.info(f"      Sales Rep: {doc.get('sales_rep')}")
                    self.logger.info(f"      Price: ${doc.get('sales_price', 0):,.2f}")
                    self.logger.info(f"      Revenue: ${doc.get('revenue_from_deal', 0):,.2f}")
                if len(docs) > 5:
                    self.logger.info(f"    ... and {len(docs) - 5} more results")
            else:
                self.logger.info("  No results found")

            self.logger.info("=" * 80)

            return docs

        except Exception as e:
            self.logger.error(f"Error during Azure Search: {str(e)}", exc_info=True)
            raise
    
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
        self.logger.debug("Calling Azure OpenAI for attribute extraction")

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

        try:
            # Log request parameters
            self.logger.debug(f"OpenAI Chat Completion request:")
            self.logger.debug(f"  - Model: {self.config['CHAT_MODEL']}")
            self.logger.debug(f"  - Temperature: 0.0")
            self.logger.debug(f"  - Max tokens: 200")
            self.logger.debug(f"  - Messages: {len(extraction_prompt)} messages")

            response = self.openai_client.chat.completions.create(
                model=self.config['CHAT_MODEL'],
                messages=extraction_prompt,
                temperature=0.0,
                max_tokens=200
            )

            # Log response
            raw_content = response.choices[0].message.content
            self.logger.debug(f"OpenAI response received (length: {len(raw_content)} chars)")
            self.logger.debug(f"Raw response: {raw_content}")

            # Parse JSON
            extracted = json.loads(raw_content)
            self.logger.debug(f"Parsed attributes: {json.dumps(extracted, indent=2)}")

            # Validation: Remove hallucinated price if not mentioned in prompt
            if extracted.get("sales_price") is not None:
                price_keywords = ["$", "price", "cost", "dollar", "usd"]
                if not any(keyword in prompt.lower() for keyword in price_keywords):
                    self.logger.debug("Removing hallucinated sales_price (not mentioned in prompt)")
                    extracted["sales_price"] = None

            # Validation: Remove hallucinated revenue if not mentioned in prompt
            if extracted.get("expected_revenue") is not None:
                revenue_keywords = ["revenue", "expected", "forecast"]
                if not any(keyword in prompt.lower() for keyword in revenue_keywords):
                    if "$" not in prompt:
                        self.logger.debug("Removing hallucinated expected_revenue (not mentioned in prompt)")
                        extracted["expected_revenue"] = None

            self.logger.debug(f"Final validated attributes: {json.dumps(extracted, indent=2)}")
            return extracted

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from OpenAI response: {str(e)}")
            self.logger.error(f"Raw response was: {raw_content}")
            return {}
        except Exception as e:
            self.logger.error(f"Error during attribute extraction: {str(e)}", exc_info=True)
            raise
    
    def _llm_chat(self, messages, temperature=0.8, seed=None):
        """Chat with LLM."""
        self.logger.info("=" * 80)
        self.logger.info("AZURE OPENAI CHAT COMPLETION REQUEST")
        self.logger.info("=" * 80)

        params = {
            "model": self.config['CHAT_MODEL'],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4000
        }
        if seed is not None:
            params["seed"] = seed

        try:
            # Log full request parameters
            self.logger.info("REQUEST PARAMETERS:")
            self.logger.info(f"  Model: {params['model']}")
            self.logger.info(f"  Temperature: {params['temperature']}")
            self.logger.info(f"  Max Tokens: {params['max_tokens']}")
            self.logger.info(f"  Seed: {params.get('seed', 'None')}")
            self.logger.info(f"  Message Count: {len(messages)}")

            # Log full messages
            self.logger.info("REQUEST MESSAGES:")
            for i, msg in enumerate(messages):
                self.logger.info(f"  Message {i+1} - Role: {msg['role']}")
                content = msg.get('content', '')
                self.logger.info(f"  Content ({len(content)} chars):")
                # Log first 500 chars of each message
                if len(content) <= 500:
                    self.logger.info(f"    {content}")
                else:
                    self.logger.info(f"    {content[:500]}...")
                    self.logger.info(f"    [... truncated, total {len(content)} chars]")

            response = self.openai_client.chat.completions.create(**params)

            # Log full response
            self.logger.info("-" * 80)
            self.logger.info("AZURE OPENAI CHAT COMPLETION RESPONSE")
            self.logger.info("-" * 80)

            content = response.choices[0].message.content
            self.logger.info(f"RESPONSE CONTENT ({len(content)} chars):")
            # Log first 1000 chars of response
            if len(content) <= 1000:
                self.logger.info(content)
            else:
                self.logger.info(f"{content[:1000]}...")
                self.logger.info(f"[... truncated, total {len(content)} chars]")

            # Log token usage
            if hasattr(response, 'usage') and response.usage:
                self.logger.info("TOKEN USAGE:")
                self.logger.info(f"  Prompt Tokens: {response.usage.prompt_tokens}")
                self.logger.info(f"  Completion Tokens: {response.usage.completion_tokens}")
                self.logger.info(f"  Total Tokens: {response.usage.total_tokens}")

            # Log response metadata
            self.logger.info("RESPONSE METADATA:")
            self.logger.info(f"  Finish Reason: {response.choices[0].finish_reason}")
            self.logger.info(f"  Model: {response.model}")

            self.logger.info("=" * 80)

            return content

        except Exception as e:
            self.logger.error(f"Error during LLM chat: {str(e)}", exc_info=True)
            raise
    
    def _case_insensitive_lookup(self, search_value, data_dict):
        """Perform case-insensitive lookup in a dictionary."""
        if not search_value or not data_dict:
            return None

        lowercase_map = {k.lower(): k for k in data_dict.keys()}
        return lowercase_map.get(search_value.lower())

    def _get_relevant_stats(self, extracted_attrs):
        """Filter and summarize relevant stats from JSON based on extracted attributes."""
        self.logger.debug("Building relevant statistics from extracted attributes")
        self.logger.debug(f"Input attributes: {json.dumps(extracted_attrs, indent=2)}")

        relevant = {
            "overall_win_rate": self.stats["overall_win_rate"],
            "avg_cycle_days": self.stats["avg_cycle_days"],
            "correlations": self.stats["correlations"]
        }

        self.logger.debug(f"Overall win rate: {relevant['overall_win_rate']:.4f}")

        # Product-specific (case-insensitive lookup)
        product = extracted_attrs.get("product")
        self.logger.debug(f"Looking up product: '{product}'")
        product_key = self._case_insensitive_lookup(product, self.stats["product"]["win_rate"])

        # Get product stats reference (used in both if and else blocks)
        prod_stats = self.stats["product"]

        if product_key:
            self.logger.debug(f"Product found: '{product_key}'")
            relevant["products"] = {
                product_key: {
                    "win_rate": prod_stats["win_rate"][product_key],
                    "lift": prod_stats["lift"][product_key]
                }
            }
            self.logger.debug(f"Product '{product_key}' - Win rate: {prod_stats['win_rate'][product_key]:.4f}, "
                            f"Lift: {prod_stats['lift'][product_key]:.4f}")
        else:
            self.logger.debug(f"Product '{product}' not found in stats, using top alternatives")
            relevant["products"] = {}
            alts = sorted(
                [(k, prod_stats["lift"][k]) for k in prod_stats["lift"]],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            for alt_prod, _ in alts:
                relevant["products"][alt_prod] = {
                    "win_rate": prod_stats["win_rate"][alt_prod],
                    "lift": prod_stats["lift"][alt_prod]
                }

        if relevant.get("products"):
            relevant["avg_revenue_by_product"] = {k: self.stats["avg_revenue_by_product"][k] for k in relevant["products"]}

        # Sector-specific (case-insensitive lookup)
        sector = extracted_attrs.get("sector")
        self.logger.debug(f"Looking up sector: '{sector}'")
        sector_key = self._case_insensitive_lookup(sector, self.stats["account_sector"]["win_rate"])

        # Get sector stats reference (used in both if and else blocks)
        sec_stats = self.stats["account_sector"]

        if sector_key:
            self.logger.debug(f"Sector found: '{sector_key}'")
            relevant["sector"] = {
                sector_key: {
                    "win_rate": sec_stats["win_rate"][sector_key],
                    "lift": sec_stats["lift"][sector_key]
                }
            }
            self.logger.debug(f"Sector '{sector_key}' - Win rate: {sec_stats['win_rate'][sector_key]:.4f}, "
                            f"Lift: {sec_stats['lift'][sector_key]:.4f}")
        else:
            self.logger.debug(f"Sector '{sector}' not found in stats, using top alternatives")
            relevant["sector"] = {}
            alts = sorted(
                [(k, sec_stats["lift"][k]) for k in sec_stats["lift"]],
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
        self.logger.debug("Retrieving qualitative insights")
        relevant["qualitative_insights"] = {}
        qual_sector_key = self._case_insensitive_lookup(sector, self.qual_stats.get("segmented", {}))

        if qual_sector_key:
            self.logger.debug(f"Using segmented qualitative stats for sector: '{qual_sector_key}'")
            # Segmented data is now pre-normalized with correct frequencies
            seg_data = self.qual_stats["segmented"][qual_sector_key]
            normalized_seg = {}
            for cat_type in ["win_drivers", "loss_risks"]:
                if cat_type in seg_data:
                    # Filter categories with frequency > 0.1 (10%)
                    filtered = {k: v for k, v in seg_data[cat_type].items() if v["frequency"] > 0.1}
                    normalized_seg[cat_type] = filtered
                    self.logger.debug(f"  {cat_type}: {len(filtered)} categories above 10% threshold")
            relevant["qualitative_insights"] = normalized_seg
        else:
            self.logger.debug(f"Sector '{sector}' not found in qualitative stats, using overall stats")
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
                self.logger.debug(f"  {cat_type}: {len(top_cats)} top categories")

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

        # Log summary
        self.logger.info("=" * 80)
        self.logger.info("RETRIEVED RELEVANT STATISTICS")
        self.logger.info("=" * 80)

        # Quantitative Stats
        self.logger.info("QUANTITATIVE STATISTICS:")
        self.logger.info(f"  Overall Win Rate: {relevant['overall_win_rate']:.2%}")
        self.logger.info(f"  Average Cycle Days: Won={relevant['avg_cycle_days']['won']:.1f}, Lost={relevant['avg_cycle_days']['lost']:.1f}")

        if 'products' in relevant:
            self.logger.info(f"  Product Stats ({len(relevant['products'])} products):")
            for prod, stats in relevant['products'].items():
                self.logger.info(f"    - {prod}: Win Rate={stats['win_rate']:.2%}, Lift={stats['lift']:.2%}")

        if 'sector' in relevant:
            self.logger.info(f"  Sector Stats:")
            for sec, stats in relevant['sector'].items():
                self.logger.info(f"    - {sec}: Win Rate={stats['win_rate']:.2%}, Lift={stats['lift']:.2%}")

        if 'region' in relevant:
            self.logger.info(f"  Region Stats:")
            for reg, stats in relevant['region'].items():
                self.logger.info(f"    - {reg}: Win Rate={stats['win_rate']:.2%}, Lift={stats['lift']:.2%}")

        if 'current_rep' in relevant:
            rep_name = relevant['current_rep']['name']
            rep_wr = relevant['current_rep']['win_rate']
            rep_lift = relevant['current_rep']['lift']
            self.logger.info(f"  Current Rep: {rep_name} (Win Rate={rep_wr:.2%}, Lift={rep_lift:.2%})")

        if 'product_sector' in relevant:
            self.logger.info(f"  Product-Sector Combinations: {len(relevant['product_sector'])}")
            for combo, wr in relevant['product_sector'].items():
                self.logger.info(f"    - {combo}: {wr:.2%}")

        # Qualitative Stats
        self.logger.info("QUALITATIVE STATISTICS:")
        if 'win_drivers' in relevant['qualitative_insights']:
            self.logger.info(f"  Win Drivers ({len(relevant['qualitative_insights']['win_drivers'])} categories):")
            for driver, data in relevant['qualitative_insights']['win_drivers'].items():
                self.logger.info(f"    - {driver}: {data['frequency']:.1f}%")

        if 'loss_risks' in relevant['qualitative_insights']:
            self.logger.info(f"  Loss Risks ({len(relevant['qualitative_insights']['loss_risks'])} categories):")
            for risk, data in relevant['qualitative_insights']['loss_risks'].items():
                self.logger.info(f"    - {risk}: {data['frequency']:.1f}%")

        # Simulations
        self.logger.info(f"  Simulations: {len(simulations)}")
        for sim in simulations[:3]:  # Log top 3
            self.logger.info(f"    - {sim['description']}: +{sim['uplift_percent']:.2f}% uplift")

        self.logger.info("=" * 80)

        return relevant

