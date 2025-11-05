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
        max_tokens=200
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
        temperature=0.8,
        max_tokens=4000
    )
    return response.choices[0].message.content

def get_relevant_stats(extracted_attrs, stats, qual_stats, openai_client, chat_model):
    """Filter and summarize relevant stats from JSON based on extracted attributes."""
    relevant = {
        "overall_win_rate": stats["overall_win_rate"],
        "avg_cycle_days": stats["avg_cycle_days"],
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

    # Qualitative Insights
    relevant["qualitative_insights"] = {}
    if sector and sector in qual_stats.get("segmented", {}):
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
                "content": f"Estimate % win uplift if addressing '{top_risk}' (freq: {top_risk_freq}) in {sector or 'general'} sector."
            }
        ]
        try:
            uplift_str = llm_chat(sim_prompt, openai_client, chat_model)
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

                            "RELEVANT_STATS is tailored to extracted attributes (e.g., sector, product); use it for precise suggestions. "
                            "Incorporate SIMULATIONS for estimated impacts (e.g., 'Switch to top rep for +4.7% win rate based on simulation').\n"
                            "QUALITATIVE_INSIGHTS provide behavioral patterns (e.g., 'In retail losses, 22% cite pricing—mitigate via bundling for +8% win lift, citing example: \"Pricing too high... lost to LCD\"'). "
                            "Only suggest if freq > 0.1; incorporate into suggestions with examples/snippets.\n"
                            "For reps: Suggest changes if top_reps show >5% lift over current_rep.\n"
                            "Ground all in data; cite simulations/relevant metrics/qual insights.\n\n"

                            "Structure your responses as follows:\n"
                            "- **Additions/Improvements for Success:** List 3-5 prioritized suggestions (e.g., product/rep changes), referencing won examples and quantifying with RELEVANT_STATS/SIMULATIONS/QUALITATIVE_INSIGHTS (e.g., '+3% win rate, $X revenue; address demo_success pattern').\n"
                            "- **Removals/Risks to Avoid:** List 3-5 suggestions to mitigate risks (e.g., pricing adjustments), referencing lost examples and quantifying downsides (e.g., 'Avoid feature_mismatch: 15% loss risk').\n"
                            "- **Overall Strategy:** Summarize plan, estimated win probability improvement (from simulations/qual_lift_estimate), revenue/cycle impact, and next steps.\n"
                            "Always provide all sections including Next Steps in your response. If information is not available for any of the above 3 sections, clearly state that recommendation cannot be provided due to lack of data."

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
                            "3. Overall: Estimated win probability improvement (e.g., +5-10% from baseline, including qual_lift_estimate), revenue/cycle impact, next steps."
                        )
                    }
                ]

                # Get recommendation
                st.session_state.recommendation = llm_chat(conversation, openai_client, config['CHAT_MODEL'])
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
        st.markdown(st.session_state.recommendation)

        # Display follow-up Q&A - show heading before first question
        if st.session_state.follow_up_responses:
            st.markdown("---")
            st.subheader("💬 Follow-up Questions & Answers")
            for idx, qa in enumerate(st.session_state.follow_up_responses, 1):
                st.markdown(f'<p class="followup-question">Q{idx}: {qa["question"]}</p>', unsafe_allow_html=True)
                st.markdown(qa['answer'])

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
                answer = llm_chat(st.session_state.conversation_history, openai_client, config['CHAT_MODEL'])
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

