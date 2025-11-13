"""
Streamlit UI for Sales Recommendation Advisor
Pure UI code - all business logic is in SalesAdvisorEngine
"""

import streamlit as st
import json
import logging
from sales_advisor_engine import SalesAdvisorEngine
from prompts import get_sales_strategy_system_prompt, get_sales_strategy_user_prompt

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

# Initialize Sales Advisor Engine
@st.cache_resource
def init_engine():
    """Initialize the SalesAdvisorEngine (cached for performance)."""
    return SalesAdvisorEngine(log_level=logging.INFO)

# Main UI
def main():
    # Initialize engine
    try:
        engine = init_engine()
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
        st.metric("Overall Win Rate", f"{engine.stats['overall_win_rate']*100:.1f}%")
        if isinstance(engine.stats['avg_cycle_days'], dict):
            st.metric("Avg Sales Cycle (Won)", f"{engine.stats['avg_cycle_days']['won']:.0f} days")
            st.metric("Avg Sales Cycle (Lost)", f"{engine.stats['avg_cycle_days']['lost']:.0f} days")
        else:
            st.metric("Avg Sales Cycle", f"{engine.stats['avg_cycle_days']:.0f} days")

        st.markdown("---")

        # Model Info
        with st.expander("📊 Model Info", expanded=False):
            st.write(f"**Chat Model:** {engine.config['CHAT_MODEL']}")
            st.write(f"**Embedding Model:** {engine.config['EMBEDDING_MODEL']}")

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
        try:
            st.session_state.current_opportunity = opportunity_description

            # Call the engine to analyze the opportunity
            with st.spinner("🤖 Analyzing your opportunity..."):
                result = engine.analyze_opportunity(opportunity_description)

            # Check if analysis was successful
            if not result["success"]:
                st.error(f"❌ {result['error_message']}")
                return

            # Store results in session state
            st.session_state.extracted_attrs = result["extracted_attributes"]
            st.session_state.relevant_stats = result["relevant_stats"]
            st.session_state.recommendation = result["recommendation"]
            st.session_state.won_docs = result["won_matches"]
            st.session_state.lost_docs = result["lost_matches"]

            # Build conversation history for follow-up questions
            context_msg = (
                f"User Opportunity:\n{opportunity_description}\n"
                f"Extracted Attributes: {json.dumps(result['extracted_attributes'])}\n\n"
                f"=== Top 10 Successful Matches ===\n{engine._format_docs(result['won_matches'])}\n\n"
                f"=== Top 10 Failed Matches ===\n{engine._format_docs(result['lost_matches'])}\n"
            )
            st.session_state.conversation_history = [
                {
                    "role": "system",
                    "content": get_sales_strategy_system_prompt()
                },
                {
                    "role": "user",
                    "content": get_sales_strategy_user_prompt(context_msg, result["relevant_stats"])
                },
                {
                    "role": "assistant",
                    "content": result["recommendation"]
                }
            ]

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

        # Show extracted attributes - as heading with text below (no expander)
        st.subheader("Extracted Attributes")
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

        # Display similar opportunities - as heading with 2 expanders (won and lost)
        if st.session_state.won_docs or st.session_state.lost_docs:
            st.subheader("Similar Sales Opportunities")

            # Won cases expander
            if st.session_state.won_docs:
                with st.expander("✅ Top 10 Won Cases", expanded=False):
                    for idx, doc in enumerate(st.session_state.won_docs, 1):
                        st.text(f"{idx}. {doc.get('opportunity_id')} | Rep: {doc.get('sales_rep')} | Product: {doc.get('product')} | Sector: {doc.get('account_sector')} | Region: {doc.get('account_region')} | Price: ${doc.get('sales_price'):,.0f} | Revenue: ${doc.get('revenue_from_deal'):,.0f} | Cycle: {doc.get('sales_cycle_duration')} days")
                        # Display Notes in normal font
                        note_text = doc.get('Notes', '')
                        st.text(f"Note: {note_text}")
                        st.text("")  # Add spacing between entries

            # Lost cases expander
            if st.session_state.lost_docs:
                with st.expander("❌ Top 10 Lost Cases", expanded=False):
                    for idx, doc in enumerate(st.session_state.lost_docs, 1):
                        st.text(f"{idx}. {doc.get('opportunity_id')} | Rep: {doc.get('sales_rep')} | Product: {doc.get('product')} | Sector: {doc.get('account_sector')} | Region: {doc.get('account_region')} | Price: ${doc.get('sales_price'):,.0f} | Revenue: ${doc.get('revenue_from_deal'):,.0f} | Cycle: {doc.get('sales_cycle_duration')} days")
                        # Display Notes in normal font
                        note_text = doc.get('Notes', '')
                        st.text(f"Note: {note_text}")
                        st.text("")  # Add spacing between entries

        # Display recommendation
        st.markdown("---")
        st.subheader("🎯 AI-Powered Recommendation")
        # Escape dollar signs to prevent LaTeX rendering
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
                # Use engine's LLM chat method for follow-up
                answer = engine._llm_chat(
                    st.session_state.conversation_history,
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
