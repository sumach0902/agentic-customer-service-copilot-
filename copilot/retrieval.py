"""RAG retrieval over policy documents, with no external service.

Design choices worth talking about in the interview:
- Chunk by section, so a rule stays with its exception.
- Metadata filter BEFORE ranking: only current versions, only the
  effective version, never a superseded document.
- Hybrid in spirit: TF-IDF ranking plus an exact-term bonus, so a
  policy code or exact phrase is not lost to paraphrase.
- Every chunk carries its citation (title, section, version, date),
  and the agent must cite it or escalate.
"""
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY_DIR = ROOT / "copilot" / "policies"

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "what", "how", "do", "does",
    "did", "can", "could", "my", "i", "me", "please", "tell", "about", "for",
    "to", "of", "and", "or", "in", "on", "with", "when", "where", "is",
}


def tokenize(text):
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def parse_policy_file(path):
    """Parse a policy markdown file: header fields + ## sections."""
    text = path.read_text()
    meta = {}
    body = text
    if text.startswith("---"):
        _, header, body = text.split("---", 2)
        for line in header.strip().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip()
    chunks = []
    current_section = "Overview"
    current_lines = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_lines:
                chunks.append((current_section, "\n".join(current_lines).strip()))
            current_section = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        chunks.append((current_section, "\n".join(current_lines).strip()))
    out = []
    for section, content in chunks:
        if content:
            out.append({
                "title": meta.get("title", path.stem),
                "version": meta.get("version", "?"),
                "effective_date": meta.get("effective_date", "?"),
                "status": meta.get("status", "current"),
                "product": meta.get("product", ""),
                "section": section,
                "text": content,
            })
    return out


def load_chunks(policy_dir=POLICY_DIR):
    """Load chunks, excluding anything that is not current.

    This is the stale-policy guardrail: a superseded version is never
    retrievable, no matter how well it matches the question.
    """
    chunks = []
    for path in sorted(policy_dir.glob("*.md")):
        for chunk in parse_policy_file(path):
            if chunk["status"] == "current":
                chunks.append(chunk)
    return chunks


class Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.docs = [tokenize(c["title"] + " " + c["section"] + " " + c["text"]) for c in chunks]
        n = len(self.docs) or 1
        df = {}
        for doc in self.docs:
            for token in set(doc):
                df[token] = df.get(token, 0) + 1
        self.idf = {t: math.log((n + 1) / (count + 1)) + 1 for t, count in df.items()}

    def _vector(self, tokens):
        vec = {}
        for token in tokens:
            vec[token] = vec.get(token, 0) + 1
        for token in vec:
            vec[token] = vec[token] * self.idf.get(token, 1.0)
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def retrieve(self, query, top_k=2):
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        query_vec = self._vector(query_tokens)
        scored = []
        for chunk, doc in zip(self.chunks, self.docs):
            doc_vec = self._vector(doc)
            cosine = sum(query_vec.get(t, 0) * doc_vec.get(t, 0) for t in query_vec)
            # Exact-term bonus: an exact policy phrase should not lose
            # to a paraphrase that merely shares common words.
            exact = len(set(query_tokens) & set(doc)) / max(len(set(query_tokens)), 1)
            score = cosine + 0.25 * exact
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [(score, chunk) for score, chunk in scored[:top_k] if score > 0]


def citation(chunk):
    return (f"{chunk['title']}, {chunk['section']} "
            f"(v{chunk['version']}, effective {chunk['effective_date']})")
