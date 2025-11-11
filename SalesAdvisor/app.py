"""
Streamlit UI for Sales Recommendation Advisor (Based on GrokSalesRecommendation.py)
Simple, clean interface without custom stylesheets
"""

import streamlit as st
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from pathlib import Path
import json
from collections import Counter

# Import centralized prompts
from prompts import (
    get_attribute_extraction_prompt,
    get_uplift_estimation_prompt,
    get_uplift_estimation_user_prompt,
    get_sales_strategy_system_prompt,
    get_sales_strategy_user_prompt
)

# Page configuration
st.set_page_config(
    page_title="Sales Recommendation Advisor",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark yellow buttons and smaller metric values
st.markdown("""
    <style>
    /* Dark yellow background for secondary buttons */
    button[kind="secondary"] {
        background-color: #DAA520 !important;
        color: white !important;
    }
    /* Dark yellow background for primary buttons */
    button[kind="primary"] {
        background-color: #DAA520 !important;
        color: white !important;
    }
    /* Reduce Statistics metric font size to match header size */
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    /* Make follow-up questions larger, bold, and italic with yellow/gold color */
    .followup-question {
        font-size: 1.5em !important;
        font-weight: bold !important;
        font-style: italic !important;
        color: #FFD700 !important;
    }
    /* Make chat input narrower (70% width) and taller (3-4 lines visible) */
    .stChatInput {
        width: 70% !important;
        max-width: 70% !important;
    }
    .stChatInput > div {
        min-height: 100px !important;
    }
    .stChatInput textarea {
        min-height: 100px !important;
        height: auto !important;
        max-height: 200px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'recommendation' not in st.session_state:
    st.session_state.recommendation = None
if 'extracted_attrs' not in st.session_state:
    st.session_state.extracted_attrs = None
if 'relevant_stats' not in st.session_state:
    st.session_state.relevant_stats = None
if 'won_docs' not in st.session_state:
    st.session_state.won_docs = None
if 'lost_docs' not in st.session_state:
    st.session_state.lost_docs = None
if 'current_opportunity' not in st.session_state:
    st.session_state.current_opportunity = ""
if 'follow_up_responses' not in st.session_state:
    st.session_state.follow_up_responses = []
if 'show_analysis' not in st.session_state:
    st.session_state.show_analysis = False
if 'follow_up_input_key' not in st.session_state:
    st.session_state.follow_up_input_key = 0

# Load environment variables
@st.cache_resource
def load_config():
    load_dotenv()
    return {
        'OPEN_AI_KEY': os.getenv("OPEN_AI_KEY"),
        'OPEN_AI_ENDPOINT': os.getenv("OPEN_AI_ENDPOINT"),
        'SEARCH_ENDPOINT': os.getenv("SEARCH_ENDPOINT"),
        'SEARCH_KEY': os.getenv("SEARCH_KEY"),
        'INDEX_NAME': os.getenv("INDEX_NAME"),
        'EMBEDDING_MODEL': os.getenv("EMBEDDING_MODEL"),
        'CHAT_MODEL': os.getenv("CHAT_MODEL")
    }

# Initialize Azure clients
@st.cache_resource
def init_clients():
    config = load_config()
    openai_client = AzureOpenAI(
        api_key=config['OPEN_AI_KEY'],
        azure_endpoint=config['OPEN_AI_ENDPOINT'],
        api_version="2024-12-01-preview"
    )
    search_client = SearchClient(
        endpoint=config['SEARCH_ENDPOINT'],
        index_name=config['INDEX_NAME'],
        credential=AzureKeyCredential(config['SEARCH_KEY'])
    )
    return openai_client, search_client

# Load statistics
@st.cache_data
def load_statistics():
    script_dir = Path(__file__).parent
    with open(script_dir / "quantitative_stats.json", "r", encoding="utf-8") as f:
        stats = json.load(f)
    with open(script_dir / "qualitative_stats.json", "r", encoding="utf-8") as f:
        qual_stats = json.load(f)
    return stats, qual_stats

def embed_text(text, openai_client, embedding_model):
    response = openai_client.embeddings.create(model=embedding_model, input=text)
    return response.data[0].embedding

def get_top_matches(prompt, stage_filter, search_client, openai_client, embedding_model, top_k=10):
    embedding = embed_text(prompt, openai_client, embedding_model)
    filter_expr = f"deal_stage eq '{stage_filter}'"
    results = search_client.search(
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
            "opportunity_id", "content", "deal_stage", "product", "account_sector", "sales_rep", "account_region", 
            "sales_price", "revenue_from_deal", "sales_cycle_duration", "deal_value_ratio", "Notes"
        ],
        top=top_k
    )
    return [doc for doc in results]

def format_docs(docs):
    return "\n".join([
        f"{doc.get('opportunity_id')} | Stage: {doc.get('deal_stage').capitalize()} | Rep: {doc.get('sales_rep')} | "
        f"Product: {doc.get('product')} | Sector: {doc.get('account_sector')} | Region: {doc.get('account_region')} | "
        f"Price: {doc.get('sales_price')} | Revenue: {doc.get('revenue_from_deal')} | Sales Cycle Duration: {doc.get('sales_cycle_duration')} days | "
        f"Deal Value Ratio: {doc.get('deal_value_ratio')} | Note: {doc.get('Notes', '')[:400]}..."  
        for doc in docs
    ])

def extract_attributes(prompt, openai_client, chat_model):
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
    response = openai_client.chat.completions.create(
        model=chat_model,
        messages=extraction_prompt,
        temperature=0.0,  # Changed from 0.1 for deterministic extraction
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
            # Only check for revenue if $ is not already counted as price
            if not any(keyword in prompt.lower() for keyword in revenue_keywords):
                if "$" not in prompt:
                    extracted["expected_revenue"] = None

        return extracted
    except json.JSONDecodeError:
        return {}

def llm_chat(messages, openai_client, chat_model, temperature=0.8, seed=None):
    """
    Chat with LLM.
    For consistent recommendations, use temperature=0.1 and seed=12345.
    For deterministic numeric outputs, use temperature=0.0 and seed=12345.
    """
    params = {
        "model": chat_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 4000
    }
    if seed is not None:
        params["seed"] = seed

    response = openai_client.chat.completions.create(**params)
    return response.choices[0].message.content

def case_insensitive_lookup(search_value, data_dict):
    """
    Perform case-insensitive lookup in a dictionary.
    Returns the actual key from the dictionary if found, None otherwise.

    Args:
        search_value: The value to search for (case-insensitive)
        data_dict: Dictionary with keys to search in

    Returns:
        The actual key from the dictionary (with correct case) or None
    """
    if not search_value or not data_dict:
        return None

    # Create a mapping of lowercase keys to actual keys
    lowercase_map = {k.lower(): k for k in data_dict.keys()}

    # Look up using lowercase
    return lowercase_map.get(search_value.lower())

def get_relevant_stats(extracted_attrs, stats, qual_stats, openai_client, chat_model):
    """Filter and summarize relevant stats from JSON based on extracted attributes."""
    relevant = {
        "overall_win_rate": stats["overall_win_rate"],
        "avg_cycle_days": stats["avg_cycle_days"],
        "correlations": stats["correlations"]
    }
    
    # Product-specific (case-insensitive lookup)
    product = extracted_attrs.get("product")
    product_key = case_insensitive_lookup(product, stats["product"]["win_rate"])
    if product_key:
        prod_stats = stats["product"]
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
        relevant["avg_revenue_by_product"] = {k: stats["avg_revenue_by_product"][k] for k in relevant["products"]}
    
    # Sector-specific (case-insensitive lookup)
    sector = extracted_attrs.get("sector")
    sector_key = case_insensitive_lookup(sector, stats["account_sector"]["win_rate"])

    # Debug logging for sector lookup
    if sector and not sector_key:
        import sys
        print(f"⚠️ WARNING: Sector '{sector}' not found in stats.", file=sys.stderr)
        print(f"   Available sectors: {list(stats['account_sector']['win_rate'].keys())}", file=sys.stderr)

    if sector_key:
        sec_stats = stats["account_sector"]
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
            # Try to find product_sector combination with case-insensitive matching
            prod_sec_key = case_insensitive_lookup(f"{product_key}_{sector_key}", stats["product_sector_win_rates"])
            relevant["product_sector"] = {}
            if prod_sec_key:
                relevant["product_sector"][prod_sec_key] = stats["product_sector_win_rates"][prod_sec_key]

            # Find alternative product-sector combinations
            sec_combos = []
            for k, v in stats["product_sector_win_rates"].items():
                parts = k.split("_", 1)  # Split only on first underscore
                if len(parts) == 2 and parts[1].lower() == sector_key.lower():
                    sec_combos.append((parts[0], v))

            if sec_combos:
                alts = sorted(sec_combos, key=lambda x: x[1], reverse=True)[:3]
                for alt_prod, wr in alts:
                    if alt_prod.lower() != product_key.lower() if product_key else True:
                        combo_key = case_insensitive_lookup(f"{alt_prod}_{sector_key}", stats["product_sector_win_rates"])
                        if combo_key:
                            relevant["product_sector"][combo_key] = wr
    
    # Region-specific (case-insensitive lookup)
    region = extracted_attrs.get("region")
    region_key = case_insensitive_lookup(region, stats["account_region"]["win_rate"])
    if region_key:
        reg_stats = stats["account_region"]
        relevant["region"] = {
            region_key: {
                "win_rate": reg_stats["win_rate"][region_key],
                "lift": reg_stats["lift"][region_key]
            }
        }

    # Sales Rep stats (case-insensitive lookup)
    rep_stats = stats["sales_rep"]
    current_rep = extracted_attrs.get("current_rep")
    current_rep_key = case_insensitive_lookup(current_rep, rep_stats["win_rate"])
    if current_rep_key:
        relevant["current_rep"] = {
            "name": current_rep_key,
            "win_rate": rep_stats["win_rate"][current_rep_key],
            "lift": rep_stats["lift"][current_rep_key],
            "sample_size": rep_stats["sample_size"][current_rep_key]
        }
    top_reps = sorted(
        [(k, rep_stats["lift"][k], rep_stats["win_rate"][k], rep_stats["sample_size"][k]) for k in rep_stats["lift"]],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    relevant["top_reps"] = [{"name": name, "win_rate": wr, "lift": lift, "sample_size": ss} for name, lift, wr, ss in top_reps]
    
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
                "revenue_estimate": stats["avg_revenue_by_product"].get(prod, 0)
            })
    if "top_reps" in relevant:
        for rep in relevant["top_reps"]:
            simulations.append({
                "description": f"Assign to {rep['name']}",
                "estimated_win_rate": baseline_wr * rep["lift"],
                "uplift_percent": (rep["lift"] - 1) * 100,
                "confidence": "High" if rep["sample_size"] > 200 else "Medium"
            })
    relevant["simulations"] = simulations

    # Qualitative Insights (case-insensitive lookup)
    relevant["qualitative_insights"] = {}
    qual_sector_key = case_insensitive_lookup(sector, qual_stats.get("segmented", {}))
    if qual_sector_key:
        seg_data = qual_stats["segmented"][qual_sector_key]
        normalized_seg = {}
        for cat_type in ["win_drivers", "loss_risks"]:
            if cat_type in seg_data:
                denom_key = "total_" + cat_type.split("_")[0].lower()
                denom = qual_stats["overall"].get(denom_key, 1)
                normalized_cat = {}
                for category, count in seg_data[cat_type].items():
                    freq = count / denom if denom > 0 else 0
                    normalized_cat[category] = {
                        "frequency": freq,
                        "count": count,
                        "examples": []
                    }
                filtered = {k: v for k, v in normalized_cat.items() if v["frequency"] > 0.1}
                normalized_seg[cat_type] = filtered
        relevant["qualitative_insights"] = normalized_seg
    else:
        for cat_type in ["win_drivers", "loss_risks"]:
            top_cats = Counter({k: v["frequency"] for k, v in qual_stats[cat_type].items() if v["frequency"] > 0.1}).most_common(3)
            relevant["qualitative_insights"][cat_type] = {cat[0]: qual_stats[cat_type][cat[0]] for cat in top_cats}

    # Qualitative lift estimate
    if "loss_risks" in relevant["qualitative_insights"] and relevant["qualitative_insights"]["loss_risks"]:
        top_risk = max(relevant["qualitative_insights"]["loss_risks"], key=lambda k: relevant["qualitative_insights"]["loss_risks"][k]["frequency"])
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
            # Use temperature=0.0 for deterministic numeric uplift estimation
            uplift_str = llm_chat(sim_prompt, openai_client, chat_model, temperature=0.0, seed=12345)
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
        corr_price = stats["correlations"]["sales_price"]
        relevant["price_insight"] = f"Current price {price}: Correlation with win rate {corr_price:.4f} (negative suggests lower price may help)."
    rev = extracted_attrs.get("expected_revenue")
    if rev:
        relevant["revenue_insight"] = f"Expected revenue {rev}: Compare to product avgs for uplift potential."

    # ═══════════════════════════════════════════════════════════════════
    # PRE-SORT DATA IN PYTHON FOR DETERMINISTIC LLM SELECTION
    # ═══════════════════════════════════════════════════════════════════

    # Sort simulations by uplift_percent (highest first)
    # This ensures LLM always sees simulations in the same order
    simulations = sorted(
        simulations,
        key=lambda x: x.get("uplift_percent", 0),
        reverse=True  # Descending order: highest uplift first
    )

    # Sort win_drivers by frequency (highest first)
    if "win_drivers" in relevant["qualitative_insights"]:
        win_drivers_sorted = dict(
            sorted(
                relevant["qualitative_insights"]["win_drivers"].items(),
                key=lambda x: x[1]["frequency"],
                reverse=True  # Descending order: most frequent first
            )
        )
        relevant["qualitative_insights"]["win_drivers"] = win_drivers_sorted

    # Sort loss_risks by frequency (highest first)
    if "loss_risks" in relevant["qualitative_insights"]:
        loss_risks_sorted = dict(
            sorted(
                relevant["qualitative_insights"]["loss_risks"].items(),
                key=lambda x: x[1]["frequency"],
                reverse=True  # Descending order: most frequent first
            )
        )
        relevant["qualitative_insights"]["loss_risks"] = loss_risks_sorted

    # ═══════════════════════════════════════════════════════════════════
    # PRE-CALCULATE WIN PROBABILITY IMPROVEMENTS FOR TOP 3 RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════════

    # Prepare top 3 win probability improvement recommendations
    # These combine quantitative (simulations) and qualitative (win_drivers) insights
    win_probability_improvements = []

    # Add top 3 simulations (already sorted by uplift_percent)
    for i in range(min(3, len(simulations))):
        sim = simulations[i]

        # Determine if this is quantitative or qualitative based
        source_type = "Qualitative insight" if sim.get("from_qual", False) else "Quantitative simulation"

        win_probability_improvements.append({
            "rank": i + 1,
            "recommendation": sim["description"],
            "uplift_percent": sim["uplift_percent"],
            "confidence": sim.get("confidence", "Medium"),
            "source_type": source_type,
            "explanation": f"This recommendation is based on {source_type.lower()} showing {sim['uplift_percent']:.2f}% improvement in win rate."
        })

    relevant["win_probability_improvements"] = win_probability_improvements
    relevant["simulations"] = simulations
    return relevant

# Main UI
def main():
    # Initialize clients and load data
    try:
        openai_client, search_client = init_clients()
        stats, qual_stats = load_statistics()
        config = load_config()
    except Exception as e:
        st.error(f"❌ Error initializing application: {str(e)}")
        st.info("Please ensure your .env file is properly configured with all required credentials.")
        return

    # Sidebar
    with st.sidebar:
        st.header("ℹ️ About")
        st.info(
            "This tool analyzes your sales opportunity by comparing it to similar won and lost deals, "
            "providing data-driven recommendations to improve your chances of success."
        )

        st.markdown("---")

        # Buttons with dark yellow background
        if st.button("🔍 Analyze New Opportunity", type="secondary", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.recommendation = None
            st.session_state.extracted_attrs = None
            st.session_state.relevant_stats = None
            st.session_state.won_docs = None
            st.session_state.lost_docs = None
            st.session_state.current_opportunity = ""
            st.session_state.follow_up_responses = []
            st.session_state.show_analysis = False
            st.rerun()

        if st.button("🔄 Clear History", type="secondary", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.recommendation = None
            st.session_state.extracted_attrs = None
            st.session_state.relevant_stats = None
            st.session_state.won_docs = None
            st.session_state.lost_docs = None
            st.session_state.current_opportunity = ""
            st.session_state.follow_up_responses = []
            st.session_state.show_analysis = False
            st.rerun()

        st.markdown("---")

        # Statistics
        st.header("📈 Statistics")
        st.metric("Overall Win Rate", f"{stats['overall_win_rate']*100:.1f}%")
        if isinstance(stats['avg_cycle_days'], dict):
            st.metric("Avg Sales Cycle (Won)", f"{stats['avg_cycle_days']['won']:.0f} days")
            st.metric("Avg Sales Cycle (Lost)", f"{stats['avg_cycle_days']['lost']:.0f} days")
        else:
            st.metric("Avg Sales Cycle", f"{stats['avg_cycle_days']:.0f} days")

        st.markdown("---")

        # Model Info
        with st.expander("📊 Model Info", expanded=False):
            st.write(f"**Chat Model:** {config['CHAT_MODEL']}")
            st.write(f"**Embedding Model:** {config['EMBEDDING_MODEL']}")

    # Main page
    st.title("💡 Sales Recommendation Advisor")

    # Show input section only if not showing analysis
    if not st.session_state.show_analysis:
        # Input section
        st.markdown("<p style='font-size: 1.25em;'>Enter details about your sales opportunity:</p>", unsafe_allow_html=True)

        opportunity_description = st.chat_input(
            "Example: We're pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX-2000 product. The sales rep is John Smith...",
            key="main_opportunity_input"
        )
    else:
        opportunity_description = None

    # Handle chat input submission (Enter key pressed)
    if opportunity_description and opportunity_description.strip():
        with st.spinner("Analyzing your opportunity..."):
            try:
                st.session_state.current_opportunity = opportunity_description

                # Extract attributes
                st.session_state.extracted_attrs = extract_attributes(
                    opportunity_description,
                    openai_client,
                    config['CHAT_MODEL']
                )

                # Show what was extracted
                with st.expander("🔍 Extracted Attributes", expanded=False):
                    st.json(st.session_state.extracted_attrs)

                # Get relevant stats
                st.session_state.relevant_stats = get_relevant_stats(
                    st.session_state.extracted_attrs,
                    stats,
                    qual_stats,
                    openai_client,
                    config['CHAT_MODEL']
                )

                # Retrieve similar opportunities
                st.session_state.won_docs = get_top_matches(
                    opportunity_description,
                    stage_filter="won",
                    search_client=search_client,
                    openai_client=openai_client,
                    embedding_model=config['EMBEDDING_MODEL'],
                    top_k=10
                )
                st.session_state.lost_docs = get_top_matches(
                    opportunity_description,
                    stage_filter="lost",
                    search_client=search_client,
                    openai_client=openai_client,
                    embedding_model=config['EMBEDDING_MODEL'],
                    top_k=10
                )

                # Build context
                context_msg = (
                    f"User Opportunity:\n{opportunity_description}\n"
                    f"Extracted Attributes: {json.dumps(st.session_state.extracted_attrs)}\n\n"
                    f"=== Top 10 Successful Matches ===\n{format_docs(st.session_state.won_docs)}\n\n"
                    f"=== Top 10 Failed Matches ===\n{format_docs(st.session_state.lost_docs)}\n"
                )

                # Create conversation
                conversation = [
                    {
                        "role": "system",
                        "content": get_sales_strategy_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": get_sales_strategy_user_prompt(context_msg, st.session_state.relevant_stats)
                    }
                ]

                # Get recommendation with low temperature for consistency
                st.session_state.recommendation = llm_chat(
                    conversation,
                    openai_client,
                    config['CHAT_MODEL'],
                    temperature=0.1,  # Low temperature for high consistency while maintaining natural language
                    seed=12345  # Fixed seed for reproducibility
                )
                st.session_state.conversation_history = conversation
                st.session_state.follow_up_responses = []
                st.session_state.show_analysis = True
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                return

    # Display results
    if st.session_state.show_analysis and st.session_state.recommendation:
        # Display the prompt entered
        st.subheader("Your Sales Opportunity")
        st.write(st.session_state.current_opportunity)

        # Display extracted attributes
        if st.session_state.extracted_attrs:
            st.subheader("Extracted Attributes")
            attrs = st.session_state.extracted_attrs
            attr_text = ""
            if attrs.get('product'):
                attr_text += f"Product: {attrs['product']}  "
            if attrs.get('sector'):
                attr_text += f"Sector: {attrs['sector']}  "
            if attrs.get('region'):
                attr_text += f"Region: {attrs['region']}  "
            if attrs.get('current_rep'):
                attr_text += f"Sales Rep: {attrs['current_rep']}  "
            if attrs.get('sales_price'):
                attr_text += f"Price: ${attrs['sales_price']}  "
            if attrs.get('expected_revenue'):
                attr_text += f"Expected Revenue: ${attrs['expected_revenue']}  "

            st.text(attr_text if attr_text else "No attributes extracted")

        # Display top 10 won and lost cases
        if st.session_state.won_docs or st.session_state.lost_docs:
            st.subheader("Similar Sales Opportunities")

            if st.session_state.won_docs:
                with st.expander("✅ Top 10 Won Cases", expanded=False):
                    for idx, doc in enumerate(st.session_state.won_docs, 1):
                        st.write(f"{idx}. {doc.get('opportunity_id')} | Rep: {doc.get('sales_rep')} | Product: {doc.get('product')} | Sector: {doc.get('account_sector')} | Region: {doc.get('account_region')} | Price: ${doc.get('sales_price'):,.0f} | Revenue: ${doc.get('revenue_from_deal'):,.0f} | Cycle: {doc.get('sales_cycle_duration')} days")
                        st.write(f"   Note: {doc.get('Notes', '')}")
                        st.write("")  # Empty line for spacing

            if st.session_state.lost_docs:
                with st.expander("❌ Top 10 Lost Cases", expanded=False):
                    for idx, doc in enumerate(st.session_state.lost_docs, 1):
                        st.write(f"{idx}. {doc.get('opportunity_id')} | Rep: {doc.get('sales_rep')} | Product: {doc.get('product')} | Sector: {doc.get('account_sector')} | Region: {doc.get('account_region')} | Price: ${doc.get('sales_price'):,.0f} | Revenue: ${doc.get('revenue_from_deal'):,.0f} | Cycle: {doc.get('sales_cycle_duration')} days")
                        st.write(f"   Note: {doc.get('Notes', '')}")
                        st.write("")  # Empty line for spacing

        # Display LLM recommendation
        st.subheader("AI Recommendation")
        # Escape dollar signs to prevent LaTeX rendering (e.g., $550 being treated as math)
        recommendation_text = st.session_state.recommendation.replace('$', r'\$')
        st.markdown(recommendation_text)

        # Display follow-up Q&A - show heading before first question
        if st.session_state.follow_up_responses:
            st.markdown("---")
            st.subheader("💬 Follow-up Questions & Answers")
            for idx, qa in enumerate(st.session_state.follow_up_responses, 1):
                st.markdown(f'<p class="followup-question">Q{idx}: {qa["question"]}</p>', unsafe_allow_html=True)
                # Escape dollar signs in follow-up answers too
                answer_text = qa['answer'].replace('$', r'\$')
                st.markdown(answer_text)

        # Follow-up question section
        st.markdown("---")
        st.subheader("Ask Follow-up Question")

        # Chat input for follow-up questions
        follow_up = st.chat_input(
            "Ask a follow-up question (e.g., What if we lower the price by 10%?)",
            key=f"follow_up_chat_{st.session_state.follow_up_input_key}"
        )

        # Handle follow-up question submission (Enter key pressed)
        if follow_up and follow_up.strip():
            with st.spinner("Thinking..."):
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": follow_up
                })
                # Use low temperature for consistent follow-up answers
                answer = llm_chat(
                    st.session_state.conversation_history,
                    openai_client,
                    config['CHAT_MODEL'],
                    temperature=0.1,
                    seed=12345
                )
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": answer
                })
                st.session_state.follow_up_responses.append({
                    "question": follow_up,
                    "answer": answer
                })
                # Increment key to clear input
                st.session_state.follow_up_input_key += 1
                st.rerun()

if __name__ == "__main__":
    main()