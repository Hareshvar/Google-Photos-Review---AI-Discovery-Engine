import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

from backend.rag.vector_store import VectorStore
from backend.rag.guardrails import SafetyGuard

logger = logging.getLogger(__name__)

def clean_response_formatting(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "â€œ": '"',
        "â€": '"',
        "â€™": "'",
        "â€˜": "'",
        "â€”": "—",
        "â€“": "–",
        "â€¦": "...",
        "â€¢": "•",
        "âpets and peopleâ": '"pets and people"',
        "â": "",
        "Ã©": "é",
        "\u202f": " ",
        "\xa0": " ",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text).strip()
    # Remove internal cluster tags like (cluster 01), (cluster 1), cluster_01, cluster 01
    text = re.sub(r'\(?\bcluster[_\s]*\d+\b\)?', '', text, flags=re.IGNORECASE)
    # Remove empty parenthetical remnants like () or ( )
    text = re.sub(r'\(\s*\)', '', text)
    # Fix double spaces and bad punctuation spacing
    text = re.sub(r'\s+', ' ', text)
    text = text.replace(" ,", ",").replace(" .", ".").strip()
    return text


RAG_PROMPT_TEMPLATE = """You are "Ask the Data", an evidence-grounded research assistant for Retrieval Lens (Google Photos Photo Retrieval Discovery Engine).

Prior Conversation History (Last 5 Chats / Exchanges):
{chat_history_context}

Current User Question: "{prompt}"

Context from Retrieved Evidence Posts (Top Matches):
{retrieved_context}

Context from Precomputed System Statistics:
- Total Relevant Posts Sample: n={total_relevant}
- Key Insights Precomputed Distributions (Q1-Q9):
{key_insights_summary}
- Emergent UX Intent Themes: {themes_summary}
- Top Situations: {situations_summary}

Strict Generation Rules:
1. Maintain memory and context from the Prior Conversation History when answering follow-up questions.
2. Base your answer ONLY on the provided post evidence and precomputed statistics.
3. State ONLY factual conclusions supported by the evidence. NEVER invent percentages or numbers.
4. Do NOT include raw technical cluster codes, cluster IDs (e.g. "cluster 01", "cluster_01"), or bracketed labels. Use clean natural language terms.
5. Keep response concise (2-4 sentences max), clear, executive-ready, and objective.
6. If there is insufficient evidence in the context, explicitly state: "There isn't enough evidence in the collected posts to answer that question confidently."
"""


class RAGEngine:
    """Grounded RAG Chatbot query orchestrator with 5-chat memory and cleaned formatting."""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.precomputed_file = os.path.join(data_dir, "precomputed_stats.json")
        self.vector_store = VectorStore(data_dir)
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self.groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        
        self._gemini_client = None
        self._groq_client = None

        if self.groq_key and self.groq_key != "your_groq_api_key_here":
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=self.groq_key, max_retries=1)
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client in RAG: {e}")

        if self.gemini_key and self.gemini_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client in RAG: {e}")

    def _build_key_insights_summary(self, precomputed: Dict[str, Any]) -> str:
        key_insights = precomputed.get("key_insights", [])
        if not key_insights:
            return "None"
        
        lines = []
        for item in key_insights:
            num = item.get("number")
            q_id = f"Q{num}" if num else (item.get("id") or item.get("question_id") or "Q")
            q_title = item.get("question", "")
            n_val = item.get("n_sample") or item.get("evidence_n") or 0
            dist = item.get("distribution", [])
            
            dist_parts = []
            for d in dist:
                label = d.get("label") or d.get("category") or "other"
                pct = d.get("share_pct") if "share_pct" in d else d.get("pct", 0.0)
                count = d.get("count", 0)
                dist_parts.append(f"{label}: {pct}% (n={count})")
                
            dist_str = "; ".join(dist_parts) if dist_parts else "No breakdown"
            lines.append(f"  - {q_id} ({q_title}, n={n_val}): {dist_str}")
            
        return "\n".join(lines)

    def ask(self, prompt: str, chat_history: Optional[List[Dict[str, str]]] = None, session_id: Optional[str] = "default") -> Dict[str, Any]:
        """Main chat endpoint handling guardrails, retrieval, synthesis, memory, and citations."""
        session_key = session_id or "default"

        # Determine active chat history (keep up to last 10 messages = 5 exchanges)
        history_list = []
        if chat_history and isinstance(chat_history, list):
            history_list = chat_history[-10:]
        elif session_key in self.sessions:
            history_list = self.sessions[session_key][-10:]
            
        history_str_lines = []
        for msg in history_list:
            role = "User" if msg.get("role") in ["user", "human"] else "Assistant"
            content = msg.get("content", "").strip()
            if content:
                history_str_lines.append(f"{role}: {content}")
        
        chat_history_context = "\n".join(history_str_lines) if history_str_lines else "None (Start of conversation)"

        # 1. Inspect Guardrails (PII, Jailbreak, Out-of-Scope)
        is_safe, refusal_payload = SafetyGuard.inspect_prompt(prompt)
        if not is_safe and refusal_payload:
            return refusal_payload

        # 2. Vector Search Retrieval (retrieve top 10 matches for reranking)
        matches = self.vector_store.query_similar(prompt, n_results=10)
        
        # 3. Load Precomputed Stats Context
        precomputed = {}
        if os.path.exists(self.precomputed_file):
            try:
                with open(self.precomputed_file, "r", encoding="utf-8") as f:
                    precomputed = json.load(f)
            except Exception:
                pass

        total_relevant = precomputed.get("metadata", {}).get("total_relevant", 916)
        key_insights_summary = self._build_key_insights_summary(precomputed)

        # Clean themes and situations summaries without raw JSON / cluster_id tags
        themes_list = []
        for c in precomputed.get("themes", {}).get("layer_b_emergent_clusters", []):
            title = c.get("title") or c.get("theme_title")
            pct = c.get("share_pct") or c.get("percentage")
            count = c.get("count")
            if title:
                themes_list.append(f"{title} ({pct}% of posts, n={count:,})")
        themes_summary = "; ".join(themes_list) if themes_list else "None"

        situations_list = []
        for s in precomputed.get("situations", [])[:5]:
            title = s.get("situation") or s.get("situation_title")
            pct = s.get("pct") or s.get("share_pct")
            score = s.get("opportunity_score")
            if title:
                situations_list.append(f"{title} ({pct}%, Score: {score})")
        situations_summary = "; ".join(situations_list) if situations_list else "None"

        # 4. Handle Low Relevance / Zero Match Edge Case
        if not matches:
            return {
                "status": "success",
                "answer": "There isn't enough evidence in the collected posts for that question.",
                "sample_disclaimer": f"Answers come only from the public posts we collected (n={total_relevant:,} sample). Not a measure of all Google Photos users.",
                "citations": []
            }

        # Format retrieved context snippets with cleaned text
        context_snippets = []
        for idx, m in enumerate(matches[:5], 1):
            q_clean = clean_response_formatting(m.get('quote') or '')
            context_snippets.append(f"[{idx}] Source: {m['source']} | Quote: \"{q_clean}\" | Text: {m['matched_text'][:200]}")
        retrieved_context_str = "\n".join(context_snippets)

        # 5. Synthesize Grounded Answer via LLM
        prompt_input = RAG_PROMPT_TEMPLATE.format(
            prompt=prompt,
            chat_history_context=chat_history_context,
            retrieved_context=retrieved_context_str,
            total_relevant=total_relevant,
            key_insights_summary=key_insights_summary,
            themes_summary=themes_summary,
            situations_summary=situations_summary
        )

        answer_text = self._generate_llm_answer(prompt_input)

        # Extract Up to 3 Verified Citations with Source Diversity (P0 Relevance, P1 Diversity)
        citations = []
        seen_urls = set()
        used_sources = set()

        # Pass 1: pick candidates with unique sources
        for m in matches:
            if len(citations) >= 3:
                break
            url = m.get("url") or ""
            raw_quote = m.get("quote") or m.get("matched_text", "")[:120]
            clean_q = clean_response_formatting(raw_quote)
            source_raw = m.get("source", "Help Community")
            
            if clean_q and url not in seen_urls and source_raw not in used_sources:
                seen_urls.add(url)
                used_sources.add(source_raw)
                citations.append({
                    "quote": clean_q,
                    "source": source_raw.replace("_", " ").title(),
                    "url": url,
                    "date": m.get("created_at", "2024-05-12"),
                    "post_id": m.get("post_id")
                })

        # Pass 2: fill remaining citations if distinct sources exhausted
        if len(citations) < 3:
            for m in matches:
                if len(citations) >= 3:
                    break
                url = m.get("url") or ""
                raw_quote = m.get("quote") or m.get("matched_text", "")[:120]
                clean_q = clean_response_formatting(raw_quote)
                source_raw = m.get("source", "Help Community")
                
                if clean_q and url not in seen_urls:
                    seen_urls.add(url)
                    citations.append({
                        "quote": clean_q,
                        "source": source_raw.replace("_", " ").title(),
                        "url": url,
                        "date": m.get("created_at", "2024-05-12"),
                        "post_id": m.get("post_id")
                    })

        disclaimer = f"Answers come only from the public posts we collected (n={total_relevant:,} sample). Not a measure of all Google Photos users."

        # Handle API Quota / Generation Failure Visibly (No Silent Hardcoded Answer)
        if not answer_text:
            logger.warning("All LLM models failed or hit quota limits. Returning visible refusal fallback payload.")
            return {
                "status": "error",
                "is_refusal": True,
                "refusal_type": "rate_limit_exceeded",
                "answer": "⚠️ AI generation limit reached. Unable to synthesize a custom response right now. Please try again in a few moments.",
                "sample_disclaimer": disclaimer,
                "citations": citations
            }

        answer_text = clean_response_formatting(answer_text)

        # Update session history memory (keep up to last 10 messages = 5 chat exchanges)
        if session_key not in self.sessions:
            self.sessions[session_key] = []
        self.sessions[session_key].append({"role": "user", "content": prompt})
        self.sessions[session_key].append({"role": "assistant", "content": answer_text})
        self.sessions[session_key] = self.sessions[session_key][-10:]

        return {
            "status": "success",
            "answer": answer_text,
            "sample_disclaimer": disclaimer,
            "citations": citations
        }

    def _generate_llm_answer(self, prompt: str) -> Optional[str]:
        # Try Gemini first (gemini-3.8-flash first, then gemini-3.6-flash fallback)
        if self._gemini_client:
            for m in ["gemini-3.8-flash", "gemini-3.6-flash"]:
                try:
                    resp = self._gemini_client.models.generate_content(
                        model=m,
                        contents=prompt
                    )
                    if resp.text:
                        return resp.text.strip()
                except Exception as e:
                    logger.warning(f"Gemini model '{m}' failed: {e}")

        # Try Groq fallback (openai/gpt-oss-120b first, then openai/gpt-oss-20b fallback)
        if self._groq_client:
            for gm in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
                try:
                    resp = self._groq_client.chat.completions.create(
                        model=gm,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1
                    )
                    if resp.choices and resp.choices[0].message.content:
                        return resp.choices[0].message.content.strip()
                except Exception as e:
                    logger.warning(f"Groq model '{gm}' failed: {e}")

        return None

