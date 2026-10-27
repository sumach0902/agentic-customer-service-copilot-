"""Streamlit Web UI for the Customer Service Copilot.

Run: streamlit run app.py
"""
import streamlit as st

from copilot import data
from copilot.agent import Agent, mask_email
from copilot.data import init_db

init_db()
agent = Agent()

st.set_page_config(page_title="Customer Service Copilot", layout="wide")
st.title("Customer Service Copilot")
st.caption("Enterprise Agentic AI: Scoped Read-Only Truth, Versioned Policy Governance & Guardrails")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Customer Profile")
    customer = st.selectbox("Active Customer Context", ["CUST-1001", "CUST-1002", "CUST-1003"])
    
    cust_record = data.get_customer(data.DB_PATH, customer)
    acct_record = data.get_account(data.DB_PATH, customer)
    
    if cust_record and acct_record:
        st.info(f"""
        **Name:** {cust_record['name']}  
        **Tier:** {cust_record['segment']} Customer  
        **Account:** {acct_record['account_type']} (`{acct_record['display_number']}`)  
        **Status:** {acct_record['status']}  
        **Contact:** `{mask_email(cust_record['email'])}`
        """)

with col2:
    st.subheader("Copilot Assistance")
    question = st.text_input(
        "Customer Inquiry",
        placeholder="Ask about account status, ticket status, or product guidance..."
    )
    
    if st.button("Ask Copilot", type="primary") and question:
        answer = agent.ask(customer, question)
        st.divider()
        if answer.escalated:
            st.warning("🛡️ **Escalation Triggered:** Handed off to human agent (copilot is strictly read-only).")
        else:
            st.success("✅ **Verified Answer Generated**")
        
        st.markdown(f"**Classified Intent:** `{answer.intent}`")
        st.markdown(answer.text)
        
        if answer.sources:
            st.markdown("**Citations & Sources:**")
            for source in answer.sources:
                st.caption(f"📌 {source}")
        
        if answer.handoff_note:
            st.info(f"📋 **Human Agent Handoff Note:**\n\n*{answer.handoff_note}*")
