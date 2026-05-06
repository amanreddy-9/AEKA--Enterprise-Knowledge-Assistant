"""LLM Handler — Ollama REST API integration"""

import requests

OLLAMA_URL = "http://localhost:11434"

SYSTEM_RAG = """You are AEKA — Enterprise Knowledge Assistant, a professional AI assistant deployed in a corporate environment.

Your rules:
- Answer ONLY from the provided document context when context is given.
- Be precise, professional, and structured in your responses.
- If the answer is not in the context, clearly state: "This information is not available in the current knowledge base."
- Format answers clearly. Use bullet points or numbered lists when appropriate.
- Cite relevant parts of the context to support your answer.
- Never fabricate or assume information not present in the context."""

SYSTEM_GENERAL = """You are AEKA — Enterprise Knowledge Assistant, a professional AI assistant.
Answer the user's question accurately and professionally. Be concise, clear, and helpful."""


class LLMHandler:
    def __init__(self, base_url: str = OLLAMA_URL):
        self.base_url = base_url

    def check_connection(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return r.status_code == 200
        except:
            return False

    def list_models(self) -> list:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
        except:
            pass
        return []

    def generate_response(
        self,
        query: str,
        context: str = "",
        model: str = "mistral",
        use_context: bool = True,
        temperature: float = 0.1,
    ) -> str:
        if use_context and context:
            system = SYSTEM_RAG
            user_msg = f"""Document Context:
---
{context}
---

User Question: {query}

Answer based strictly on the context above:"""
        else:
            system = SYSTEM_GENERAL
            user_msg = query

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": 4096},
        }

        try:
            r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
            r.raise_for_status()
            return r.json().get("message", {}).get("content", "No response generated.")
        except requests.exceptions.ConnectionError:
            return "❌ Cannot connect to Ollama. Please run `ollama serve` in your terminal."
        except requests.exceptions.Timeout:
            return "⏱️ Request timed out. The model may still be loading — please try again."
        except requests.exceptions.HTTPError as e:
            if "404" in str(e):
                return f"❌ Model `{model}` not found. Run `ollama pull {model}` to download it."
            return f"❌ HTTP Error: {e}"
        except Exception as e:
            return f"❌ Unexpected error: {e}"
