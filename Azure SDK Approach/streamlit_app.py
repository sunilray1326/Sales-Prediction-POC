"""
Streamlit UI for Sales Recommendation Advisor
This app provides an interactive interface for getting AI-powered sales recommendations
based on Azure OpenAI and Azure Cognitive Search.
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

# Custom CSS - minimal styling
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    /* Reduce Statistics metric font size by 50% */
    [data-testid="stMetricValue"] {
        font-size: 1.5em !important;
    }
    /* Reduce font size for main title and headers */
    h1 {
        font-size: 1.5rem !important;
    }
    h2 {
        font-size: 1.2rem !important;
    }
    /* Simple font for text elements */
    .stText, [data-testid="stText"],
    .stText div, [data-testid="stText"] div {
        font-family: "Source Sans Pro", sans-serif !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        line-height: 1.6 !important;
        color: rgb(250, 250, 250) !important;
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
if 'clear_input' not in st.session_state:
    st.session_state.clear_input = False

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
    with open(script_dir / "Cline_stats.json", "r", encoding="utf-8") as f:
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
        f"Deal Value Ratio: {doc.get('deal_value_ratio')} | Note: {doc.get('Notes', '')[:800]}..."  
        for doc in docs
    ])

def extract_attributes(prompt, openai_client, chat_model):
    """Use LLM to extract key attributes from the user prompt."""
    extraction_prompt = [
        {
            "role": "system",
            "content": "You are an attribute extractor. Parse the user prompt and extract: product (str or None), sector (str or None), region (str or None), sales_price (float or None), expected_revenue (float or None), current_rep (str or None). Return as JSON dict."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    response = openai_client.chat.completions.create(
        model=chat_model,
        messages=extraction_prompt,
        temperature=0.1,
        max_tokens=4000
    )
    try:
        extracted = json.loads(response.choices[0].message.content)
        return extracted
    except json.JSONDecodeError:
        return {}

def llm_chat(messages, openai_client, chat_model):
    response = openai_client.chat.completions.create(
        model=chat_model,
        messages=messages,
        temperature=0.6,
        max_tokens=4000
    )
    return response.choices[0].message.content

def get_relevant_stats(extracted_attrs, stats, qual_stats, openai_client, chat_model):
    """Filter and summarize relevant stats from JSON based on extracted attributes."""
    # Handle avg_cycle_days which can be a dict or a number
    avg_cycle = stats["avg_cycle_days"]
    if isinstance(avg_cycle, dict):
        avg_cycle_value = (avg_cycle.get("won", 0) + avg_cycle.get("lost", 0)) / 2
    else:
        avg_cycle_value = avg_cycle

    relevant = {
        "overall_win_rate": stats["overall_win_rate"],
        "avg_cycle_days": avg_cycle_value,
        "avg_cycle_days_detail": stats["avg_cycle_days"],  # Keep original for reference
        "correlations": stats["correlations"]
    }
    
    # Product-specific
    product = extracted_attrs.get("product")
    if product and product in stats["product"]["win_rate"]:
        prod_stats = stats["product"]
        relevant["products"] = {product: prod_stats["win_rate"][product]}
        alts = sorted(
            [(k, prod_stats["lift"][k]) for k in prod_stats["lift"] if k != product],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        for alt_prod, _ in alts:
            relevant["products"][alt_prod] = prod_stats["win_rate"][alt_prod]
        relevant["avg_revenue_by_product"] = {k: stats["avg_revenue_by_product"][k] for k in relevant["products"]}
    
    # Sector-specific
    sector = extracted_attrs.get("sector")
    if sector and sector in stats["account_sector"]["win_rate"]:
        sec_stats = stats["account_sector"]
        relevant["sector"] = {
            sector: {
                "win_rate": sec_stats["win_rate"][sector],
                "lift": sec_stats["lift"][sector]
            }
        }
        alts = sorted(
            [(k, sec_stats["lift"][k]) for k in sec_stats["lift"] if k != sector],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        for alt_sec, _ in alts:
            relevant["sector"][alt_sec] = {
                "win_rate": sec_stats["win_rate"][alt_sec],
                "lift": sec_stats["lift"][alt_sec]
            }
        
        if product:
            prod_sec_key = f"{product}_{sector}"
            relevant["product_sector"] = {}
            if prod_sec_key in stats["product_sector_win_rates"]:
                relevant["product_sector"][prod_sec_key] = stats["product_sector_win_rates"][prod_sec_key]
            
            sec_combos = [(k.split("_")[0], v) for k, v in stats["product_sector_win_rates"].items() if k.endswith(f"_{sector}")]
            if sec_combos:
                alts = sorted(sec_combos, key=lambda x: x[1], reverse=True)[:3]
                for alt_prod, wr in alts:
                    if alt_prod != product:
                        relevant["product_sector"][f"{alt_prod}_{sector}"] = wr
    
    # Region-specific
    region = extracted_attrs.get("region")
    if region and region in stats["account_region"]["win_rate"]:
        reg_stats = stats["account_region"]
        relevant["region"] = {
            region: {
                "win_rate": reg_stats["win_rate"][region],
                "lift": reg_stats["lift"][region]
            }
        }
    
    # Sales Rep stats
    rep_stats = stats["sales_rep"]
    current_rep = extracted_attrs.get("current_rep")
    if current_rep and current_rep in rep_stats["win_rate"]:
        relevant["current_rep"] = {
            "name": current_rep,
            "win_rate": rep_stats["win_rate"][current_rep],
            "lift": rep_stats["lift"][current_rep],
            "sample_size": rep_stats["sample_size"][current_rep]
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
    if "sector" in relevant and sector:
        sec_lift = relevant["sector"][sector]["lift"]
        simulations.append({
            "description": f"Baseline adjusted for {sector} sector",
            "estimated_win_rate": baseline_wr * sec_lift,
            "uplift_percent": (sec_lift - 1) * 100
        })
    if "products" in relevant:
        for prod, wr in relevant["products"].items():
            lift = stats["product"]["lift"][prod]
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

    # Qualitative Insights: Filter by extracted attrs (e.g., sector), threshold freq > 0.1
    relevant["qualitative_insights"] = {}
    if sector and sector in qual_stats.get("segmented", {}):
        # Normalize segmented on-the-fly since raw counts
        seg_data = qual_stats["segmented"][sector]
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
                        "examples": []  # No snippets for segmented
                    }
                # Filter freq > 0.1
                filtered = {k: v for k, v in normalized_cat.items() if v["frequency"] > 0.1}
                normalized_seg[cat_type] = filtered
        relevant["qualitative_insights"] = normalized_seg
    else:
        # Fallback to overall top 3 (already normalized)
        for cat_type in ["win_drivers", "loss_risks"]:
            if cat_type in qual_stats:
                top_cats = Counter({k: v["frequency"] for k, v in qual_stats[cat_type].items() if v["frequency"] > 0.1}).most_common(3)
                relevant["qualitative_insights"][cat_type] = {cat[0]: qual_stats[cat_type][cat[0]] for cat in top_cats}

    # Simple "lift" estimate from qual: Chain LLM for dynamic uplift
    if "loss_risks" in relevant["qualitative_insights"] and relevant["qualitative_insights"]["loss_risks"]:
        top_risk = max(relevant["qualitative_insights"]["loss_risks"], key=lambda k: relevant["qualitative_insights"]["loss_risks"][k]["frequency"])
        top_risk_freq = relevant["qualitative_insights"]["loss_risks"][top_risk]["frequency"]
        # Chain LLM for uplift estimation
        sim_prompt = [
            {
                "role": "system",
                "content": "You are a sales uplift estimator. Given a top qualitative risk (e.g., 'pricing_high') in a sector, estimate % win probability uplift if addressed (e.g., via bundling). Base on frequency and general sales knowledge. Return only a float (e.g., 12.5)."
            },
            {
                "role": "user",
                "content": f"Estimate % win uplift if addressing '{top_risk}' (freq: {top_risk_freq}) in {sector or 'general'} sector."
            }
        ]
        try:
            uplift_str = llm_chat(sim_prompt, openai_client, chat_model)
            qual_uplift = float(uplift_str.strip("%"))  # Parse float
            relevant["qual_lift_estimate"] = qual_uplift
            simulations.append({
                "description": f"Address top qual risk '{top_risk}'",
                "estimated_win_rate": baseline_wr * (1 + qual_uplift / 100),
                "uplift_percent": qual_uplift,
                "from_qual": True
            })
        except ValueError:
            relevant["qual_lift_estimate"] = (1 - top_risk_freq) * 10  # Fallback

    # Price/Revenue checks
    price = extracted_attrs.get("sales_price")
    if price:
        corr_price = stats["correlations"]["sales_price"]
        relevant["price_insight"] = f"Current price {price}: Correlation with win rate {corr_price:.4f} (negative suggests lower price may help)."
    rev = extracted_attrs.get("expected_revenue")
    if rev:
        relevant["revenue_insight"] = f"Expected revenue {rev}: Compare to product avgs for uplift potential."

    relevant["simulations"] = simulations  # Update with any new sims

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

        # Model Info as expandable section
        with st.expander("📊 Model Info", expanded=False):
            st.write(f"**Chat Model:** {config['CHAT_MODEL']}")
            st.write(f"**Embedding Model:** {config['EMBEDDING_MODEL']}")

        st.markdown("---")
        st.header("📈 Statistics")
        st.metric("Overall Win Rate", f"{stats['overall_win_rate']*100:.1f}%")
        if isinstance(stats['avg_cycle_days'], dict):
            st.metric("Avg Sales Cycle (Won)", f"{stats['avg_cycle_days']['won']:.0f} days")
            st.metric("Avg Sales Cycle (Lost)", f"{stats['avg_cycle_days']['lost']:.0f} days")
        else:
            st.metric("Avg Sales Cycle", f"{stats['avg_cycle_days']:.0f} days")
        
        if st.button("🔄 Clear History"):
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
    
    # Show input area only if no analysis is shown
    if not st.session_state.show_analysis:
        st.write("")  # Add spacing
        st.write("")  # Add spacing
        st.title("💡 Sales Recommendation Advisor")
        st.caption("AI-Powered Sales Opportunity Analysis using Azure OpenAI & Cognitive Search")

        st.header("📝 Describe Your Sales Opportunity")

        opportunity_description = st.text_area(
            "Enter details about your sales opportunity:",
            height=150,
            placeholder="Example: We're pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX-2000 product. The sales rep is John Smith, and we're competing against two other vendors...",
            help="Include details like product, sector, region, price, sales rep, and any other relevant information."
        )

        analyze_button = st.button("🔍 Analyze", type="primary")
    else:
        # When analysis is shown, don't display the input area
        analyze_button = False
        opportunity_description = st.session_state.current_opportunity

    if analyze_button and opportunity_description.strip():
        st.session_state.current_opportunity = opportunity_description.strip()
        with st.spinner("🔍 Analyzing your opportunity..."):
            try:
                # Extract attributes
                st.session_state.extracted_attrs = extract_attributes(
                    opportunity_description,
                    openai_client,
                    config['CHAT_MODEL']
                )

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
                    "won",
                    search_client,
                    openai_client,
                    config['EMBEDDING_MODEL'],
                    top_k=10
                )
                st.session_state.lost_docs = get_top_matches(
                    opportunity_description,
                    "lost",
                    search_client,
                    openai_client,
                    config['EMBEDDING_MODEL'],
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

                            "RELEVANT_STATS is tailored to extracted attributes (e.g., sector, product); use it for precise suggestions. "
                            "Incorporate SIMULATIONS for estimated impacts (e.g., 'Switch to top rep for +4.7% win rate based on simulation').\n"
                            "QUALITATIVE_INSIGHTS provide behavioral patterns (e.g., 'In retail losses, 22% cite pricing—mitigate via bundling for +8% win lift, citing example: \"Pricing too high... lost to LCD\"'). "
                            "Only suggest if freq > 0.1; incorporate into suggestions with examples/snippets.\n"
                            "For reps: Suggest changes if top_reps show >5% lift over current_rep.\n"
                            "Ground all in data; cite simulations/relevant metrics/qual insights.\n\n"

                            "Structure your responses as follows:\n"
                            "Additions/Improvements for Success: List 3-5 prioritized suggestions (e.g., product/rep changes), referencing won examples and quantifying with RELEVANT_STATS/SIMULATIONS/QUALITATIVE_INSIGHTS (e.g., '+3% win rate, $X revenue; address demo_success pattern').\n"
                            "Removals/Risks to Avoid: List 3-5 suggestions to mitigate risks (e.g., pricing adjustments), referencing lost examples and quantifying downsides (e.g., 'Avoid feature_mismatch: 15% loss risk').\n"
                            "Overall Strategy: Summarize plan, estimated win probability improvement (from simulations/qual_lift_estimate), revenue/cycle impact, and next steps.\n\n"
                            "Always provide all sections including Next Steps in your response. If information is not available for any section, clearly state that recommendation cannot be provided due to lack of data."

                            "Be concise, actionable, and professional."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Based on the following details:\n"
                            f"{context_msg}\n\n"
                            f"RELEVANT_STATS (filtered for this opportunity):\n{json.dumps(st.session_state.relevant_stats, indent=2)}\n\n"

                            "Provide tailored recommendations, using RELEVANT_STATS, SIMULATIONS, and QUALITATIVE_INSIGHTS to quantify impacts:\n"
                            "1. What 3-5 key additions/improvements (e.g., product/rep changes) to boost win chances? Prioritize, reference won examples, quantify (e.g., '+2% win rate via simulation, $X revenue; leverage demo_success insight').\n"
                            "2. What 3-5 elements to remove/mitigate (e.g., pricing risks)? Reference lost examples, quantify risks (e.g., 'Mitigate competitor risk: 20% freq in losses').\n"
                            "3. Overall Strategy: Summarize plan, estimated win probability improvement (from simulations/qual_lift_estimate), revenue/cycle impact, and next steps."
                            "4. Next Steps: Provide a clear, concise summary of the next steps to take based on the recommendations."
                        )
                    }
                ]
                
                # Get recommendation
                st.session_state.recommendation = llm_chat(conversation, openai_client, config['CHAT_MODEL'])
                st.session_state.conversation_history = conversation
                st.session_state.follow_up_responses = []  # Clear previous follow-ups
                st.session_state.show_analysis = True  # Show analysis view
                st.rerun()  # Rerun to update UI

            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                return
    
    # Display results - Show when analysis is available
    if st.session_state.show_analysis and st.session_state.recommendation:
        st.write("")  # Add spacing
        st.write("")  # Add spacing
        st.header("🧠 AI Recommendation")

        # Display extracted attributes - simple single line
        if st.session_state.extracted_attrs:
            with st.expander("📋 Extracted Attributes", expanded=False):
                attrs = st.session_state.extracted_attrs
                attr_parts = []
                if attrs.get('product'):
                    attr_parts.append(f"Product: {attrs['product']}")
                if attrs.get('sector'):
                    attr_parts.append(f"Sector: {attrs['sector']}")
                if attrs.get('region'):
                    attr_parts.append(f"Region: {attrs['region']}")
                if attrs.get('current_rep'):
                    attr_parts.append(f"Sales Rep: {attrs['current_rep']}")
                if attrs.get('sales_price'):
                    attr_parts.append(f"Price: ${attrs['sales_price']}")
                if attrs.get('expected_revenue'):
                    attr_parts.append(f"Expected Revenue: ${attrs['expected_revenue']}")

                # Simple join with comma separator - use st.text to avoid LaTeX rendering
                attr_line = ", ".join(attr_parts)
                st.text(attr_line)

        # Display similar opportunities - in a text area with scroll
        if st.session_state.won_docs or st.session_state.lost_docs:
            with st.expander("🔍 Similar Sales Opportunities Matching Your Opportunity", expanded=False):
                # Build content for text area
                content_lines = []

                if st.session_state.won_docs:
                    content_lines.append("✅ TOP 10 WON CASES")
                    content_lines.append("_" * 170)
                    content_lines.append("")
                    for idx, doc in enumerate(st.session_state.won_docs, 1):
                        content_lines.append(f"{idx}. {doc.get('opportunity_id')} | Rep: {doc.get('sales_rep')} | Product: {doc.get('product')} | Sector: {doc.get('account_sector')} | Region: {doc.get('account_region')} | Price: ${doc.get('sales_price'):,.0f} | Revenue: ${doc.get('revenue_from_deal'):,.0f} | Cycle: {doc.get('sales_cycle_duration')} days")
                        content_lines.append(f" Note: {doc.get('Notes', '')}")
                        
                if st.session_state.lost_docs:
                    if content_lines:
                        content_lines.append("")
                    content_lines.append("❌ TOP 10 LOST CASES")
                    for idx, doc in enumerate(st.session_state.lost_docs, 1):
                        content_lines.append(f"{idx}. {doc.get('opportunity_id')} | Rep: {doc.get('sales_rep')} | Product: {doc.get('product')} | Sector: {doc.get('account_sector')} | Region: {doc.get('account_region')} | Price: ${doc.get('sales_price'):,.0f} | Revenue: ${doc.get('revenue_from_deal'):,.0f} | Cycle: {doc.get('sales_cycle_duration')} days")
                        content_lines.append(f" Note: {doc.get('Notes', '')}")
                        
                # Display in custom text area with transparent background
                content_text = "\n".join(content_lines)
                st.markdown(f"""
                    <div style="
                        background-color: transparent;
                        border: 1px solid rgba(250, 250, 250, 0.2);
                        border-radius: 5px;
                        padding: 10px;
                        height: 300px;
                        overflow-y: auto;
                        font-family: 'Source Sans Pro', sans-serif;
                        font-size: 14px;
                        font-weight: 400;
                        color: rgb(250, 250, 250);
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    ">{content_text}</div>
                """, unsafe_allow_html=True)
        
        # Display key statistics - compact format
        if st.session_state.relevant_stats and 'simulations' in st.session_state.relevant_stats:
            with st.expander("📊 Detailed Simulations & Statistics", expanded=False):
                # Compact simulation display - no "Simulated Scenarios" header
                for sim in st.session_state.relevant_stats['simulations'][:5]:
                    uplift_color = "🟢" if sim['uplift_percent'] > 0 else "🔴"
                    st.text(f"{sim['description']} | Win Rate: {sim['estimated_win_rate']*100:.1f}% | Uplift: {uplift_color} {sim['uplift_percent']:.1f}%")

                # Display qualitative insights if available - side by side
                if 'qualitative_insights' in st.session_state.relevant_stats:
                    st.text("")
                    st.markdown("**<u>📝 Qualitative Insights from Notes</u>**", unsafe_allow_html=True)
                    st.text("")
                    qual_insights = st.session_state.relevant_stats['qualitative_insights']

                    col1, col2 = st.columns(2)

                    with col1:
                        if 'win_drivers' in qual_insights and qual_insights['win_drivers']:
                            st.text("✅ Win Drivers (Success Patterns):")
                            for driver, data in qual_insights['win_drivers'].items():
                                freq_pct = data['frequency'] * 100
                                st.text(f"• {driver.replace('_', ' ').title()}: {freq_pct:.1f}% ({data.get('count', 'N/A')} cases)")

                    with col2:
                        if 'loss_risks' in qual_insights and qual_insights['loss_risks']:
                            st.text("⚠️ Loss Risks (Failure Patterns):")
                            for risk, data in qual_insights['loss_risks'].items():
                                freq_pct = data['frequency'] * 100
                                st.text(f"• {risk.replace('_', ' ').title()}: {freq_pct:.1f}% ({data.get('count', 'N/A')} cases)")

                    st.text("")
                    if 'qual_lift_estimate' in st.session_state.relevant_stats:
                        st.text(f"💡 Estimated uplift from addressing top qualitative risk: +{st.session_state.relevant_stats['qual_lift_estimate']:.1f}%")

        # Display recommendation - Print directly on UI
        st.markdown("💡 **Initial Recommendation**")
        st.write(st.session_state.recommendation)

        # Display all follow-up Q&A pairs
        if st.session_state.follow_up_responses:
            st.markdown("---")
            st.subheader("💬 Follow-up Discussions")
            for idx, qa in enumerate(st.session_state.follow_up_responses, 1):
                st.markdown(f"### Question {idx}")
                st.markdown(f"**Q:** {qa['question']}\n\n**A:** {qa['answer']}")

        # Follow-up questions section - Always at the bottom
        st.markdown("---")

        # Clear input flag handling
        if st.session_state.clear_input:
            follow_up = st.text_input(
                "💬 Ask a follow-up question about this opportunity:",
                value="",
                placeholder="e.g., What if we lower the price by 10%?",
                key=f"follow_up_input_{len(st.session_state.follow_up_responses)}"
            )
            st.session_state.clear_input = False
        else:
            follow_up = st.text_input(
                "💬 Ask a follow-up question about this opportunity:",
                placeholder="e.g., What if we lower the price by 10%?",
                key=f"follow_up_input_{len(st.session_state.follow_up_responses)}"
            )

        col1, col2, _ = st.columns([0.5, 1.5, 8])
        with col1:
            ask_button = st.button("Ask", type="primary", use_container_width=True)
        with col2:
            new_analysis_button = st.button("Analyze New Opportunity", type="secondary", use_container_width=True)

        # Handle "Analyze New Opportunity" button
        if new_analysis_button:
            # Clear all session state
            st.session_state.conversation_history = []
            st.session_state.recommendation = None
            st.session_state.extracted_attrs = None
            st.session_state.relevant_stats = None
            st.session_state.won_docs = None
            st.session_state.lost_docs = None
            st.session_state.current_opportunity = ""
            st.session_state.follow_up_responses = []
            st.session_state.show_analysis = False
            st.session_state.clear_input = False
            st.rerun()

        # Handle "Ask" button
        if ask_button and follow_up.strip():
            with st.spinner("Thinking..."):
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": follow_up
                })
                answer = llm_chat(st.session_state.conversation_history, openai_client, config['CHAT_MODEL'])
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": answer
                })
                # Add to follow-up responses
                st.session_state.follow_up_responses.append({
                    "question": follow_up,
                    "answer": answer
                })
                st.session_state.clear_input = True  # Set flag to clear input on next render
                st.rerun()  # Rerun to display the new Q&A

if __name__ == "__main__":
    main()

