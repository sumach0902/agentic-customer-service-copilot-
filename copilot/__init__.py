"""Agentic Customer Service Copilot.

A small, honest demo: no LLM API key, no real customer data.
Structured customer facts live in SQLite (standing in for Snowflake),
unstructured policy truth lives in markdown files (retrieved with
TF-IDF, filtered by version and status), and the agent answers only
from those sources, with citations, or escalates to a human.
"""
