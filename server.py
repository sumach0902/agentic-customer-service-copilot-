"""Zero-dependency web demo (Python standard library only).

Run:  python3 server.py
Then open http://localhost:8000 in a browser.

This is the zero-dependency visual web demo when Streamlit is not
installed. The CLI (cli.py) shows the same answers in a terminal.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from copilot.agent import Agent
from copilot.data import init_db

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>Customer Service Copilot - Demo</title>
<style>body{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 20px}
label,select,input,button{font-size:16px} #answer{white-space:pre-wrap;background:#f4f4f4;padding:16px;border-radius:8px}
.note{color:#555}</style></head><body>
<h1>Customer Service Copilot</h1>
<p class="note">Demo only. All data is synthetic. No action is taken without a human agent.</p>
<label>Customer <select id="customer">
<option>CUST-1001</option><option>CUST-1002</option><option>CUST-1003</option>
</select></label><br><br>
<input id="q" size="70" placeholder="Ask about your account, a ticket, or a product...">
<button onclick="ask()">Ask</button>
<p>Try: What is my account status? / What is the status of my ticket TKT-5001? /
What are the fees for my savings account? / I want to cancel my account</p>
<div id="answer"></div>
<script>async function ask(){
 const r = await fetch('/ask', {method:'POST',
  headers:{'Content-Type':'application/json'},
  body: JSON.stringify({customer: document.getElementById('customer').value,
                        question: document.getElementById('q').value})});
 const d = await r.json();
 document.getElementById('answer').textContent =
  '[' + d.intent + '] escalated=' + d.escalated + '\\n\\n' + d.text +
  (d.sources.length ? '\\n\\nSources:\\n- ' + d.sources.join('\\n- ') : '') +
  (d.handoff_note ? '\\n\\nHandoff note (agent only): ' + d.handoff_note : '');
}</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    agent = None

    def do_GET(self):
        if urlparse(self.path).path in ("/", "/index.html"):
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if urlparse(self.path).path != "/ask":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        answer = self.agent.ask(payload.get("customer", "CUST-1001"),
                                payload.get("question", ""))
        body = json.dumps({
            "text": answer.text, "intent": answer.intent,
            "sources": answer.sources, "escalated": answer.escalated,
            "handoff_note": answer.handoff_note,
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    init_db()
    Handler.agent = Agent()
    print("Open http://localhost:8000")
    HTTPServer(("localhost", 8000), Handler).serve_forever()
