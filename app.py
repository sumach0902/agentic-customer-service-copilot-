"""Optional Streamlit UI. Only needed if you want a Streamlit demo.

Install first:  pip install streamlit
Run:            streamlit run app.py

The CLI (cli.py) and the standard-library web server (server.py)
show the same agent and need no installation at all.
"""
import streamlit as st

from copilot.agent import Agent
from copilot.data import init_db

init_db()
agent = Agent()

st.title("Customer Service Copilot (demo)")
st.caption("Synthetic data only. Read-only demo: no payment, refund, or account change is ever taken.")
customer = st.selectbox("Customer", ["CUST-1001", "CUST-1002", "CUST-1003"])
question = st.text_input("Ask about your account, a ticket, or a product")
if st.button("Ask") and question:
    answer = agent.ask(customer, question)
    if answer.escalated:
        st.warning("Handed off to a human agent (no action taken by the copilot).")
    st.write(answer.text)
    if answer.sources:
        st.write("Sources:")
        for source in answer.sources:
            st.write(f"- {source}")
    if answer.handoff_note:
        st.caption(f"Handoff note (agent only): {answer.handoff_note}")
