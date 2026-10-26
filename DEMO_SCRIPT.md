# 5-Minute Demo Script (say this, in this order)

## 1. Problem, 1 minute

"Customers ask the same three questions: what is my account status, where is my request, and what does this product do. Agents answer them differently, policy lookups take too long, and a wrong answer costs a repeat contact. I built a copilot scoped to those three intents, read-only, so it can prove value without risking an irreversible action."

## 2. Live demo, 2 minutes

Run `python3 cli.py --demo` or open the web demo, as customer CUST-1001.

- **Account:** "What is my account status and recent activity?" Point out: balance and activity come from the customer tables, contact details are masked, and the source is named.
- **Ticket:** "What is the status of my ticket TKT-5001?" Point out: status plus next step and date, not just a status word.
- **Product:** "What are the fees for my savings account?" Point out: the citation with title, section, version, and effective date, and that the old $25 fee document is excluded because it is superseded.
- **Escalation:** "I want to cancel my account and transfer all my money out." Point out: it does not do it, it does not claim to do it, and it hands off with context so the customer does not repeat themselves.

## 3. Architecture, 1 minute

"Guardrail check first, then intent, then read-only tools: Snowflake-style tables for structured facts, version-filtered retrieval for policies, citations on every factual claim, and a handoff when confidence is low or the request is out of scope. Every turn could be logged with question, sources, and outcome, which is how you measure containment and accuracy in a pilot."

## 4. Issues and fixes, 1 minute

Pick two, and only claim the ones that are true for this code:

- "Early retrieval returned a superseded policy, so I filter by status before ranking. A stale answer that matches well is still a wrong answer."
- "Early answers were confident but uncited, so I made citations part of the answer contract. If a claim has no source, the agent escalates instead of answering."
- "Ticket lookups were not scoped to the customer, so I added the customer filter to the query itself, not just to the display. Retrieval must never be a back door around access control."

## 5. Close, 30 seconds

"Today it runs locally on synthetic data, with a 30-question evaluation set I run after every change. Next I would pilot it as agent-assist in shadow mode, then expand one intent at a time, gated by containment and first-contact resolution moving while accuracy and escalation quality hold. That is the same pilot discipline I would bring to the enterprise scenario."

## If something breaks live

Say so, show the backup: "Let me show the recorded run instead," then walk the same four questions from `cli.py --demo` output. A calm recovery scores better than a perfect demo that you panic over.
