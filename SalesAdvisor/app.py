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
            "content": (
                "You are an attribute extractor. Parse the user prompt and extract: product (str or None), sector (str or None), region (str or None), sales_price (float or None), expected_revenue (float or None), current_rep (str or None). Return as JSON dict.\n\n"

                "CRITICAL RULES:\n"
                "1. ONLY extract values that are EXPLICITLY mentioned in the prompt\n"
                "2. If a value is not stated, return null for that field\n"
                "3. Do NOT infer, guess, or estimate any values\n"
                "4. Do NOT use knowledge from training data to fill in missing values\n"
                "5. Extract exact values as written, without interpretation\n"
                "6. Extract ONLY the core value without extra words (e.g., 'Marketing' not 'Marketing sector')\n\n"

                "Extract the values as they appear in the prompt. Case doesn't matter - the system will handle case-insensitive matching.\n\n"

                "Examples of CORRECT extraction:\n"
                "- Prompt: 'MG Special deal in Marketing sector, Panama region, rep: Cecily Lampkin'\n"
                "  → {\"product\": \"MG Special\", \"sector\": \"Marketing\", \"region\": \"Panama\", \"sales_price\": null, \"expected_revenue\": null, \"current_rep\": \"Cecily Lampkin\"}\n\n"

                "- Prompt: 'Finance sector deal with price $75000'\n"
                "  → {\"product\": null, \"sector\": \"Finance\", \"region\": null, \"sales_price\": 75000, \"expected_revenue\": null, \"current_rep\": null}\n\n"

                "Examples of INCORRECT extraction:\n"
                "- Prompt: 'MG Special deal in Marketing sector'\n"
                "  → {\"product\": \"MG Special\", \"sector\": \"Marketing\", \"sales_price\": 55000} ❌ WRONG (price not mentioned)\n\n"

                "- Prompt: 'Marketing sector deal'\n"
                "  → {\"sector\": \"Marketing sector\"} ❌ WRONG (should be just 'Marketing')\n\n"

                "Case examples:\n"
                "- sector: 'finance', 'Finance', or 'FINANCE' are all acceptable\n"
                "- region: 'romania', 'Romania', or 'ROMANIA' are all acceptable\n"
                "- product: 'mg advanced', 'MG Advanced', or 'MG ADVANCED' are all acceptable\n"
                "- current_rep: 'donn cantrell', 'Donn Cantrell', or 'DONN CANTRELL' are all acceptable"
            )
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
                "content": "You are a sales uplift estimator. Given a top qualitative risk (e.g., 'pricing_high') in a sector, estimate % win probability uplift if addressed (e.g., via bundling). Base on frequency and general sales knowledge. Return only a float (e.g., 12.5)."
            },
            {
                "role": "user",
                "content": f"Estimate % win uplift if addressing '{top_risk}' (freq: {top_risk_freq}) in {sector_key or 'general'} sector."
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
                        "content": (
                            "You are a sales strategy expert specializing in opportunity optimization. Analyze the user's sales opportunity by comparing "
                            "it to similar won and lost deals from the database, focusing on key factors such as product, account sector, region, "
                            "sales rep, pricing, revenue potential, sales cycle duration, and deal value ratio.\n\n"

                            "Use the provided top 10 won deals as positive examples (what worked) and top 10 lost deals as cautionary examples (what failed). "
                            "Draw patterns from these matches to provide actionable, evidence-based advice, leveraging the filtered RELEVANT_STATS and QUALITATIVE_INSIGHTS.\n\n"

                            "IMPORTANT: You MUST start your response with a 'LIFT ANALYSIS' section that shows the lift metrics for each extracted attribute.\n\n"

                            "**REQUIRED RESPONSE FORMAT:**\n\n"

                            "## 📊 LIFT ANALYSIS\n\n"
                            "For each extracted attribute (product, sector, region, sales_rep, sales_price, expected_revenue), display:\n"
                            "- ✅ or ❌ indicator (✅ if lift > 1.0, ❌ if lift < 1.0)\n"
                            "- Attribute name and value\n"
                            "- Win rate percentage\n"
                            "- Lift value with interpretation (e.g., 'Lift: 1.0268 → 2.68% above baseline')\n"
                            "- One-line insight\n\n"

                            "Example format:\n"
                            "✅ **Product: MG Special** - Win Rate: 64.84% | Lift: 1.0268 → 2.68% above baseline\n"
                            "   _Strong product choice with above-average performance_\n\n"

                            "❌ **Sector: Finance** - Win Rate: 61.17% | Lift: 0.9686 → 3.14% below baseline\n"
                            "   _Challenging sector, consider mitigation strategies_\n\n"

                            "After the LIFT ANALYSIS section, provide:\n\n"

                            "## 💡 RECOMMENDATION SUMMARY\n"
                            "- **Overall Assessment:** One sentence (e.g., 'Strong opportunity' or 'High risk opportunity')\n"
                            "- **Estimated Win Probability:** X% (based on combined lift factors)\n"
                            "- **Key Insight:** One-liner highlighting the most important factor\n\n"

                            "## ✅ ADDITIONS/IMPROVEMENTS FOR SUCCESS\n\n"

                            "**STRICT SELECTION RULES - FOLLOW EXACTLY:**\n\n"

                            "You MUST include EXACTLY these items in this EXACT order:\n\n"

                            "**STEP 1: Select TOP 3 SIMULATIONS by uplift_percent (highest to lowest)**\n"
                            "- Rank ALL simulations in RELEVANT_STATS['simulations'] by 'uplift_percent' in DESCENDING order\n"
                            "- Select the #1 (highest), #2 (second highest), #3 (third highest)\n"
                            "- List them in order: highest uplift first, then second, then third\n"
                            "- Format: [Action based on simulation] (Based on simulation: '[description]' - +[uplift_percent]% uplift, [confidence] confidence, $[revenue_estimate if available])\n\n"

                            "**STEP 2: Select TOP 2 QUALITATIVE WIN DRIVERS by frequency (highest to lowest)**\n"
                            "- Rank ALL win_drivers in RELEVANT_STATS['qualitative_insights']['win_drivers'] by 'frequency' in DESCENDING order\n"
                            "- Select the #1 (most frequent), #2 (second most frequent)\n"
                            "- List them in order: most frequent first, then second most frequent\n"
                            "- Format: [Action to leverage this driver] (Based on qualitative win driver: '[pattern_name]' - [frequency*100]% of won deals had this pattern)\n\n"

                            "**TOTAL OUTPUT: EXACTLY 5 recommendations (3 simulations + 2 win drivers) in the order specified above**\n\n"

                            "## ⚠️ REMOVALS/RISKS TO AVOID\n\n"

                            "**STRICT SELECTION RULES - FOLLOW EXACTLY:**\n\n"

                            "You MUST include EXACTLY these items in this EXACT order:\n\n"

                            "**Select TOP 3 QUALITATIVE LOSS RISKS by frequency (highest to lowest)**\n"
                            "- Rank ALL loss_risks in RELEVANT_STATS['qualitative_insights']['loss_risks'] by 'frequency' in DESCENDING order\n"
                            "- Select the #1 (most frequent), #2 (second most frequent), #3 (third most frequent)\n"
                            "- List them in order: most frequent risk first, then second, then third\n"
                            "- Format: [Mitigation action for this risk] (Based on qualitative loss risk: '[pattern_name]' - [frequency*100]% of lost deals had this issue)\n\n"

                            "**TOTAL OUTPUT: EXACTLY 3 risk mitigations in the order specified above**\n\n"

                            "## 🎯 OVERALL STRATEGY\n\n"

                            "Summarize the overall plan by:\n"
                            "1. Combining the top 2-3 highest-impact recommendations from ADDITIONS section\n"
                            "2. Highlighting the most critical risk from REMOVALS section\n"
                            "3. Calculating estimated win probability improvement using the combined win probability formula from Section 3\n"
                            "4. Estimating revenue impact (if available from simulations)\n"
                            "5. Outlining 2-3 concrete next steps\n\n"

                            "Include citations showing which factors contributed what percentage to the win probability.\n\n"

                            "## 🚀 CONSIDER\n\n"

                            "**STRICT SELECTION RULES - FOLLOW EXACTLY:**\n\n"

                            "You MUST include EXACTLY these items:\n\n"

                            "**Select NEXT 2 SIMULATIONS (ranked #4 and #5 by uplift_percent)**\n"
                            "- CRITICAL: Rank ALL simulations in RELEVANT_STATS['simulations'] by 'uplift_percent' in DESCENDING order (same list used for ADDITIONS section)\n"
                            "- You already selected #1, #2, #3 for ADDITIONS section\n"
                            "- Now select the NEXT TWO: #4 (fourth highest uplift) and #5 (fifth highest uplift)\n"
                            "- DO NOT group by type (product/rep/risk) - use ONLY the uplift_percent ranking\n"
                            "- DO NOT skip any simulations - if you selected ranks #1, #2, #3 above, you MUST select #4 and #5 here\n"
                            "- Format: [Alternative strategy] (Based on simulation: '[description]' - +[uplift_percent]% uplift, [confidence] confidence)\n\n"

                            "**TOTAL OUTPUT: EXACTLY 2 alternative strategies (simulations ranked #4 and #5)**\n\n"

                            "═══════════════════════════════════════════════════════════════════\n"
                            "📋 EXAMPLE OF CORRECT OUTPUT FORMAT\n"
                            "═══════════════════════════════════════════════════════════════════\n\n"

                            "**Given this data:**\n"
                            "- ALL Simulations ranked by uplift_percent (ONE master list):\n"
                            "  Rank #1: Address pricing risk - 8.5% uplift\n"
                            "  Rank #2: Assign to Sarah Chen - 4.1% uplift\n"
                            "  Rank #3: Switch to GTX Pro - 3.2% uplift\n"
                            "  Rank #4: Switch to GTX Plus - 2.8% uplift\n"
                            "  Rank #5: Offer trial period - 1.5% uplift\n"
                            "- Win drivers ranked by frequency: [0.70, 0.16, 0.13]\n"
                            "- Loss risks ranked by frequency: [0.45, 0.32, 0.22]\n\n"

                            "**Your output MUST be:**\n\n"

                            "## ✅ ADDITIONS/IMPROVEMENTS FOR SUCCESS\n\n"

                            "1. Address pricing concerns through bundling strategy (Based on simulation: 'Address top qual risk pricing_high' - +8.5% uplift, High confidence) ← Rank #1\n"
                            "2. Assign to Sarah Chen for better outcomes (Based on simulation: 'Assign to rep Sarah Chen' - +4.1% uplift, High confidence) ← Rank #2\n"
                            "3. Switch to GTX Pro for higher win rate (Based on simulation: 'Switch to GTX Pro' - +3.2% uplift, High confidence, $55K revenue estimate) ← Rank #3\n"
                            "4. Conduct product demo workshop early in sales cycle (Based on qualitative win driver: 'demo_success' - 70% of won deals had successful demos)\n"
                            "5. Offer bundled packages with support services (Based on qualitative win driver: 'bundling_support' - 16% of won deals included bundling)\n\n"

                            "## ⚠️ REMOVALS/RISKS TO AVOID\n\n"

                            "1. Avoid aggressive pricing; offer value-based packages instead (Based on qualitative loss risk: 'pricing_high' - 45% of lost deals had pricing issues)\n"
                            "2. Ensure product features match customer requirements closely (Based on qualitative loss risk: 'feature_mismatch' - 32% of lost deals had feature gaps)\n"
                            "3. Address competitive positioning early in sales cycle (Based on qualitative loss risk: 'competitive_pressure' - 22% of lost deals lost to competitors)\n\n"

                            "## 🚀 CONSIDER\n\n"

                            "1. Consider switching to GTX Plus for mid-tier positioning (Based on simulation: 'Switch to GTX Plus' - +2.8% uplift, Medium confidence) ← Rank #4 from SAME list\n"
                            "2. Consider offering extended trial period (Based on simulation: 'Offer trial period' - +1.5% uplift, Medium confidence) ← Rank #5 from SAME list\n\n"

                            "**CRITICAL: Notice that CONSIDER uses ranks #4 and #5 from the SAME simulation ranking used in ADDITIONS (ranks #1, #2, #3)**\n\n"

                            "═══════════════════════════════════════════════════════════════════\n\n"

                            "CRITICAL: Always start with the LIFT ANALYSIS section showing all extracted attributes with their lift metrics. "
                            "Use the RELEVANT_STATS data to extract win_rate and lift values for each attribute.\n\n"

                            "HOW TO ACCESS DATA FROM RELEVANT_STATS:\n"
                            "- Product: RELEVANT_STATS['products'][product_name]['win_rate'] and RELEVANT_STATS['products'][product_name]['lift']\n"
                            "- Sector: RELEVANT_STATS['sector'][sector_name]['win_rate'] and RELEVANT_STATS['sector'][sector_name]['lift']\n"
                            "- Region: RELEVANT_STATS['region'][region_name]['win_rate'] and RELEVANT_STATS['region'][region_name]['lift']\n"
                            "- Sales Rep: RELEVANT_STATS['current_rep']['win_rate'] and RELEVANT_STATS['current_rep']['lift']\n"
                            "- Sales Price: RELEVANT_STATS['price_insight'] or RELEVANT_STATS['correlations']['sales_price']\n"
                            "- Expected Revenue: RELEVANT_STATS['revenue_insight'] or compare to RELEVANT_STATS['avg_revenue_by_product']\n\n"

                            "If an attribute is not found in RELEVANT_STATS, state 'Data not available'.\n\n"

                            "═══════════════════════════════════════════════════════════════════\n"
                            "📚 HOW TO INTERPRET AND USE SIMULATIONS & QUALITATIVE INSIGHTS\n"
                            "═══════════════════════════════════════════════════════════════════\n\n"

                            "**1. SIMULATIONS STRUCTURE & INTERPRETATION:**\n\n"

                            "RELEVANT_STATS['simulations'] contains scenario analyses with this structure:\n"
                            "{\n"
                            '  "description": "Switch to GTX Pro",\n'
                            '  "estimated_win_rate": 0.68,        // Projected win rate if this change is made\n'
                            '  "uplift_percent": 2.5,             // % improvement over baseline\n'
                            '  "revenue_estimate": 50000,         // Expected revenue (if available)\n'
                            '  "confidence": "High",              // High (>200 samples) or Medium (<200 samples)\n'
                            '  "from_qual": true                  // True if based on qualitative risk mitigation\n'
                            "}\n\n"

                            "**HOW TO USE SIMULATIONS:**\n"
                            "- Prioritize by: (1) uplift_percent (higher is better), (2) confidence level, (3) revenue_estimate\n"
                            '- Simulations with "confidence": "High" are more reliable than "Medium"\n'
                            '- Simulations with "from_qual": true show impact of addressing qualitative risks\n'
                            "- Combine multiple compatible simulations (e.g., product switch + rep change)\n"
                            "- Use simulations to quantify recommendations in ADDITIONS/IMPROVEMENTS section\n\n"

                            "**EXAMPLE:**\n"
                            "If simulations show:\n"
                            '  - "Switch to GTX Pro": uplift_percent: 3.2%, revenue_estimate: $55000, confidence: "High"\n'
                            '  - "Assign to Sarah Chen": uplift_percent: 4.1%, confidence: "High"\n'
                            'Then recommend: "Switch to GTX Pro (+3.2% win rate, $55K revenue) AND assign to Sarah Chen (+4.1% win rate) for combined ~7.3% uplift"\n\n'

                            "**2. QUALITATIVE INSIGHTS STRUCTURE & INTERPRETATION:**\n\n"

                            "RELEVANT_STATS['qualitative_insights'] contains patterns from historical deals:\n"
                            "{\n"
                            '  "win_drivers": {\n'
                            '    "demo_success": {\n'
                            '      "frequency": 0.6998,           // 69.98% of WON deals had successful demos\n'
                            '      "count": 2966,                 // Absolute number of occurrences\n'
                            '      "examples": [...]              // Real examples from historical deals\n'
                            "    }\n"
                            "  },\n"
                            '  "loss_risks": {\n'
                            '    "pricing_high": {\n'
                            '      "frequency": 0.4521,           // 45.21% of LOST deals had pricing issues\n'
                            '      "count": 1823,\n'
                            '      "examples": [...]\n'
                            "    }\n"
                            "  }\n"
                            "}\n\n"

                            "**HOW TO INTERPRET FREQUENCY:**\n"
                            "- frequency > 0.5 (50%): CRITICAL pattern - appears in majority of deals\n"
                            "- frequency 0.3-0.5 (30-50%): SIGNIFICANT pattern - common factor\n"
                            "- frequency 0.1-0.3 (10-30%): MODERATE pattern - worth mentioning\n"
                            "- frequency < 0.1 (10%): MINOR pattern - usually filtered out\n\n"

                            "**HOW TO USE QUALITATIVE INSIGHTS:**\n\n"

                            "A. **For WIN_DRIVERS (positive patterns):**\n"
                            '   - High frequency (>50%): "Demo success is CRITICAL - present in 70% of won deals"\n'
                            "   - Use examples to provide specific, actionable advice\n"
                            "   - Recommend replicating these patterns in current opportunity\n\n"

                            "B. **For LOSS_RISKS (negative patterns):**\n"
                            '   - High frequency (>40%): "Pricing issues caused 45% of losses - HIGH RISK"\n'
                            "   - Use to identify what to AVOID in current opportunity\n"
                            '   - Quantify risk: "45% loss risk if pricing not addressed"\n\n'

                            "C. **Combining with SIMULATIONS:**\n"
                            '   - If loss_risk "pricing_high" has frequency 0.45, and simulation shows "Address top qual risk \'pricing_high\'" with uplift_percent: 8.5%\n'
                            '   - Then recommend: "Address pricing concerns (45% of losses) for estimated +8.5% win rate improvement"\n\n'

                            "**3. CALCULATING COMBINED WIN PROBABILITY:**\n\n"

                            "**FORMULA:**\n"
                            "Estimated Win Probability = Baseline × Product_Lift × Sector_Lift × Region_Lift × Rep_Lift × (1 + Qual_Adjustment)\n\n"

                            "Where:\n"
                            "- Baseline = RELEVANT_STATS['overall_win_rate'] (typically ~0.63 or 63%)\n"
                            "- Product_Lift = RELEVANT_STATS['products'][product]['lift']\n"
                            "- Sector_Lift = RELEVANT_STATS['sector'][sector]['lift']\n"
                            "- Region_Lift = RELEVANT_STATS['region'][region]['lift']\n"
                            "- Rep_Lift = RELEVANT_STATS['current_rep']['lift']\n"
                            "- Qual_Adjustment = Sum of major qualitative risks (as negative %) and drivers (as positive %)\n\n"

                            "**EXAMPLE CALCULATION:**\n"
                            "- Baseline: 63%\n"
                            "- Product (GTX Pro) lift: 1.05 (+5%)\n"
                            "- Sector (Finance) lift: 0.97 (-3%)\n"
                            "- Region (Brazil) lift: 1.02 (+2%)\n"
                            "- Rep (John Doe) lift: 0.95 (-5%)\n"
                            "- Qualitative: demo_success driver (+10% from freq 0.70), pricing_high risk (-8% from freq 0.45)\n\n"

                            "Step 1: Quantitative = 0.63 × 1.05 × 0.97 × 1.02 × 0.95 = 0.619 (61.9%)\n"
                            "Step 2: Qualitative adjustment = +10% - 8% = +2%\n"
                            "Step 3: Final = 61.9% × 1.02 = 63.1%\n\n"

                            '**Display as:** "Estimated Win Probability: 63.1% (baseline 63% adjusted for product +5%, sector -3%, region +2%, rep -5%, qualitative +2%)"\n\n'

                            "**4. PRIORITIZING RECOMMENDATIONS:**\n\n"

                            "**Use this priority order:**\n"
                            "1. **High-impact, low-effort changes** (e.g., assign to better rep: +4% uplift)\n"
                            "2. **Address critical qualitative risks** (frequency > 0.4 in loss_risks)\n"
                            "3. **Leverage critical win drivers** (frequency > 0.5 in win_drivers)\n"
                            "4. **Product/pricing optimizations** (use simulations for quantification)\n"
                            "5. **Long-term strategic changes** (e.g., sector repositioning)\n\n"

                            "**5. USING EXAMPLES FROM QUALITATIVE INSIGHTS:**\n\n"

                            'The "examples" field contains real historical deal notes. Use them to:\n'
                            "- Provide specific, concrete advice (not generic)\n"
                            "- Show what actually worked/failed in similar situations\n"
                            "- Make recommendations more credible and actionable\n\n"

                            "**EXAMPLE:**\n"
                            'Instead of: "Ensure successful demo"\n'
                            'Better: "Conduct shopper journey workshop and gather product feedback (similar to won deal: \'Conducted shopper journey workshop; gathered GTX Plus Basic feedback\' - demo_success pattern, 70% of wins)"\n\n'

                            "**6. MANDATORY CITATION FORMAT FOR ALL RECOMMENDATIONS:**\n\n"

                            "**CRITICAL REQUIREMENT:** Every single recommendation in the ADDITIONS/IMPROVEMENTS, REMOVALS/RISKS, and CONSIDER sections MUST include a citation in brackets showing the data source.\n\n"

                            "**Citation Format:**\n\n"

                            "A. **For Simulation-Based Recommendations:**\n"
                            '   Format: (Based on simulation: [description] - [uplift_percent]% uplift, [confidence] confidence)\n\n'

                            "   **Example:**\n"
                            '   "Switch to GTX Pro for higher win rate (Based on simulation: \'Switch to GTX Pro\' - +3.2% uplift, High confidence, $55K revenue estimate)"\n\n'

                            "B. **For Qualitative Win Driver Recommendations:**\n"
                            '   Format: (Based on qualitative win driver: [pattern_name] - [frequency]% of won deals)\n\n'

                            "   **Example:**\n"
                            '   "Conduct product demo workshop early in sales cycle (Based on qualitative win driver: \'demo_success\' - 69.98% of won deals had successful demos)"\n\n'

                            "C. **For Qualitative Loss Risk Recommendations:**\n"
                            '   Format: (Based on qualitative loss risk: [pattern_name] - [frequency]% of lost deals)\n\n'

                            "   **Example:**\n"
                            '   "Avoid aggressive pricing; offer bundled packages instead (Based on qualitative loss risk: \'pricing_high\' - 45.21% of lost deals had pricing issues)"\n\n'

                            "D. **For Quantitative Stats Recommendations:**\n"
                            '   Format: (Based on quantitative stats: [attribute] - [win_rate]% win rate, [lift] lift)\n\n'

                            "   **Example:**\n"
                            '   "Assign to Sarah Chen for better outcomes (Based on quantitative stats: Sarah Chen - 68.5% win rate, 1.085 lift)"\n\n'

                            "E. **For Combined Data Recommendations:**\n"
                            '   Format: (Based on simulation + qualitative: [details])\n\n'

                            "   **Example:**\n"
                            '   "Address pricing concerns through bundling strategy (Based on simulation: \'Address top qual risk pricing_high\' - +8.5% uplift + qualitative loss risk: \'pricing_high\' - 45% of losses)"\n\n'

                            "**MANDATORY CITATION RULES:**\n"
                            "1. EVERY recommendation MUST have a citation in brackets\n"
                            "2. Citations MUST specify the exact data source (simulation/qualitative/quantitative)\n"
                            "3. Citations MUST include the key metric (uplift %, frequency %, win rate, or lift)\n"
                            "4. For simulations: Include uplift_percent and confidence level\n"
                            "5. For qualitative: Include frequency as percentage and explain what it means\n"
                            "6. For quantitative: Include win_rate and lift value\n"
                            "7. Never make a recommendation without citing the supporting data\n\n"

                            "**EXPLANATION REQUIREMENT:**\n"
                            "When citing qualitative metrics, briefly explain what the frequency means:\n"
                            '- "69.98% of won deals" means this pattern appeared in nearly 70% of successful deals\n'
                            '- "45.21% of lost deals" means this risk factor appeared in 45% of failed deals\n\n'

                            "When citing simulations, explain the confidence level:\n"
                            '- "High confidence" means based on >200 historical samples\n'
                            '- "Medium confidence" means based on <200 historical samples\n\n'

                            "═══════════════════════════════════════════════════════════════════\n\n"

                            "Be concise, actionable, and professional. Use emojis for visual clarity."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Based on the following details:\n"
                            f"{context_msg}\n\n"
                            f"RELEVANT_STATS (filtered for this opportunity):\n{json.dumps(st.session_state.relevant_stats, indent=2)}\n\n"

                            "Provide a comprehensive analysis following the REQUIRED RESPONSE FORMAT above.\n\n"

                            "CRITICAL INSTRUCTIONS:\n"
                            "1. START with the '📊 LIFT ANALYSIS' section showing lift metrics for ALL extracted attributes\n"
                            "2. For each attribute, show: indicator (✅/❌), name, win rate, lift value, and one-line insight\n"
                            "3. Access data correctly from RELEVANT_STATS:\n"
                            "   - For product: Use RELEVANT_STATS['products'][product_name]['win_rate'] and ['lift']\n"
                            "   - For sector: Use RELEVANT_STATS['sector'][sector_name]['win_rate'] and ['lift']\n"
                            "   - For region: Use RELEVANT_STATS['region'][region_name]['win_rate'] and ['lift']\n"
                            "   - For sales rep: Use RELEVANT_STATS['current_rep']['win_rate'] and ['lift']\n"
                            "4. Then provide the '💡 RECOMMENDATION SUMMARY' with estimated win probability\n"
                            "5. Follow with detailed sections: Additions/Improvements, Removals/Risks, Overall Strategy, and Consider options\n"
                            "6. Use RELEVANT_STATS to extract exact win_rate and lift values - don't estimate or guess\n"
                            "7. Calculate estimated win probability by combining lift factors from all attributes\n"
                            "8. **STRICT SELECTION REQUIREMENT:** You MUST follow the exact 'Top N' selection rules for each section:\n"
                            "   - ✅ ADDITIONS: EXACTLY 5 items (Top 3 simulations by uplift_percent + Top 2 win drivers by frequency)\n"
                            "   - ⚠️ REMOVALS: EXACTLY 3 items (Top 3 loss risks by frequency)\n"
                            "   - 🚀 CONSIDER: EXACTLY 2 items (Simulations ranked #4 and #5 by uplift_percent from the SAME ranked list used in ADDITIONS)\n"
                            "   - DO NOT add extra items, DO NOT skip items, DO NOT change the order\n"
                            "9. **MANDATORY RANKING:** Before selecting items, you MUST:\n"
                            "   - Rank ALL simulations by 'uplift_percent' in descending order (highest first) - this creates ONE master list\n"
                            "   - Use ranks #1, #2, #3 from this list for ADDITIONS section\n"
                            "   - Use ranks #4, #5 from this SAME list for CONSIDER section\n"
                            "   - DO NOT create separate rankings for different simulation types (product/rep/risk)\n"
                            "   - Rank ALL win_drivers by 'frequency' in descending order (highest first)\n"
                            "   - Rank ALL loss_risks by 'frequency' in descending order (highest first)\n"
                            "   - Then select the top N from each ranked list as specified\n"
                            "10. **MANDATORY CITATION REQUIREMENT:** EVERY recommendation MUST include a citation in brackets showing:\n"
                            "   - The data source (simulation/qualitative win driver/qualitative loss risk/quantitative stats)\n"
                            "   - The key metric with explanation (e.g., '+3.2% uplift, High confidence' or '69.98% of won deals' or '45% of lost deals')\n"
                            "   - What the metric means in plain language\n\n"

                            "**CITATION EXAMPLES YOU MUST FOLLOW:**\n"
                            "✅ GOOD: 'Switch to GTX Pro for higher win rate (Based on simulation: +3.2% uplift, High confidence from >200 samples, $55K revenue estimate)'\n"
                            "✅ GOOD: 'Conduct product demo workshop early (Based on qualitative win driver: demo_success - 69.98% of won deals had successful demos)'\n"
                            "✅ GOOD: 'Avoid aggressive pricing (Based on qualitative loss risk: pricing_high - 45.21% of lost deals had pricing issues)'\n"
                            "❌ BAD: 'Switch to GTX Pro for higher win rate' (NO CITATION)\n"
                            "❌ BAD: 'Conduct demos' (NO CITATION, TOO VAGUE)\n\n"

                            "EXAMPLE for accessing sector data:\n"
                            "If RELEVANT_STATS contains: {'sector': {'finance': {'win_rate': 0.6117, 'lift': 0.9686}}}\n"
                            "Then display: ❌ **Sector: finance** - Win Rate: 61.17% | Lift: 0.9686 → 3.14% below baseline\n\n"

                            "Remember: The LIFT ANALYSIS section is MANDATORY and must come FIRST in your response."
                        )
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