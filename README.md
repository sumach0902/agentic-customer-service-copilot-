# Agentic Customer Service Copilot

A working demo for an FDE interview: an agentic copilot for customer servicing that answers account questions, ticket status, and product guidance, with citations and human escalation.

**Honest scope, say this in the interview:** this is a working prototype on synthetic data, built to be pilot-ready. It is read-only by design. It never takes a payment, refund, transfer, or account change, and it never claims to have done so. That restraint is the point.

## What it demonstrates

- **Snowflake-style structured truth:** customer, account, activity, and ticket tables. Locally in SQLite so it runs anywhere; the schema and queries map directly to Snowflake (see `snowflake_schema.sql`).
- **RAG over policies:** markdown policy documents, chunked by section, filtered to current versions only, retrieved with TF-IDF plus an exact-term bonus.
- **Prompt-free guardrails in code:** every answer is either grounded in a retrieved source or a structured record, or it escalates. No guessing.
- **Escalation with context:** complaints, vulnerable-customer cases, and irreversible actions produce a handoff note, not an action.
- **Privacy by design:** account numbers, emails, and phones are masked in answers; retrieval is always scoped to one customer.
- **Evaluation, not vibes:** a 30-question golden set. Run `python3 evaluate.py` after every change.

## Run it in 2 minutes (no API key, no install)

```bash
cd agentic-customer-service-copilot
python3 generate_data.py
python3 cli.py --demo
```

That runs 4 scripted questions: an account question, a ticket status, a product fee question, and a cancel/transfer request that must escalate.

Interactive mode:

```bash
python3 cli.py --interactive
```

Single question:

```bash
python3 cli.py --customer CUST-1001 --ask "What is the status of my ticket TKT-5001?"
```

Visual demo, no install (standard library only):

```bash
python3 server.py
# open http://localhost:8000
```

Optional Streamlit demo:

```bash
pip install streamlit
streamlit run app.py
```

## Demo customers (all synthetic)

- `CUST-1001` Priya Sharma, Savings ****4321, ticket `TKT-5001` (card delivery, In Progress)
- `CUST-1002` Arjun Patel, Checking ****9876, ticket `TKT-5003` (billing question, Waiting for customer)
- `CUST-1003` Maya Chen, Savings ****5550, ticket `TKT-5004` (login help, Resolved)

## How the agent works

1. **Guardrail check first:** complaint, vulnerable-customer, or irreversible-action language escalates immediately, before any lookup.
2. **Intent:** ticket status, account question, product guidance, or unknown.
3. **Tools (read-only):** account summary and recent activity from the customer tables; ticket status scoped to that customer; policy retrieval for product questions.
4. **Answer with sources:** Snowflake-style table names for structured facts; policy title, section, version, and effective date for document facts.
5. **Escalate when unsure:** no current policy, no ticket for this customer, or low retrieval confidence means a handoff, not a guess.

## The stale-policy trap (a good interview story)

The policies folder contains a superseded Savings fees document (v1.0, $25 monthly fee) alongside the current one (v2.0, no monthly fee). The retriever excludes `status != current` before ranking, so the old fee can never be cited, no matter how well it matches. If you remove that filter, the demo will happily quote the wrong fee. That is exactly the kind of silent failure an FDE has to design out.

## Project structure

```
copilot/
  data.py        Synthetic Snowflake-style tables in SQLite
  retrieval.py   Policy parsing, version filtering, TF-IDF retrieval
  agent.py       Intent, guardrails, tools, citations, handoff
  policies/      Versioned policy documents (one superseded, on purpose)
cli.py           Terminal demo and interactive mode
server.py        Zero-dependency web demo
app.py           Optional Streamlit UI
evaluate.py      30-question golden-set evaluation
generate_data.py Rebuild the synthetic database
snowflake_schema.sql  Production schema mapping
```

## Evaluation

```bash
python3 evaluate.py
```

It checks intent accuracy, source/citation accuracy, and escalation accuracy, and writes `results/eval_results.json`. Quote the numbers from your own run in the interview, not from this README, so they are always true for the code you show.

## What I would do next (say this when they ask)

1. Pilot as agent-assist first: human agents approve or correct drafts in shadow mode, so learning is fast and customers see no risk.
2. Add a real LLM for answer wording only, keeping retrieval, citations, and guardrails exactly as they are here, so the model cannot invent facts.
3. Connect the SQLite queries to Snowflake secure views, add identity and role-based access, and log every turn for weekly human review.
4. Expand one intent at a time, gated by the same rule: primary KPIs move, guardrails hold, otherwise fix or stop.

## What this demo deliberately does not do

- Take payments, refunds, transfers, or account changes.
- Answer from model memory when a source is available.
- Retrieve another customer's records.
- Use real customer data, API keys, or a paid service.

## Interview talk track

See `DEMO_SCRIPT.md` for the 5-minute version: problem, live demo, architecture, two real issues and fixes, and how it runs today.
