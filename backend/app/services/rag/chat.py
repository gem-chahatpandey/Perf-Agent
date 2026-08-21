import json
from datetime import datetime
from app.ai.gemini import gemini_provider
from app.ai.prompts import CHATBOT_PROMPT
from app.ai.rag import rag_engine
from app.storage.filesystem import storage
from app.core.logging import logger


class ChatService:
    async def ask(self, question: str, run_id: str | None = None, history: list[dict] | None = None) -> dict:
        context_parts = []

        if run_id:
            try:
                analysis = await storage.load(f"runs/{run_id}/analysis.json")
                context_parts.append(f"Analysis for {run_id}: {json.dumps(analysis, indent=2)[:3000]}")
            except FileNotFoundError:
                pass
            try:
                rca = await storage.load(f"runs/{run_id}/rca.json")
                context_parts.append(f"RCA for {run_id}: {json.dumps(rca, indent=2)[:2000]}")
            except FileNotFoundError:
                pass

        rag_results = await rag_engine.retrieve(question, n_results=3)
        if rag_results:
            context_parts.append("Knowledge Base Context:\n" + "\n---\n".join(rag_results[:3]))

        context = "\n\n".join(context_parts) if context_parts else "No specific context available."
        history_text = ""
        if history:
            history_text = "\n".join(
                f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('content', '')}"
                for m in history[-10:]
            )

        if not gemini_provider.is_configured():
            return {
                "answer": "AI is not configured. Please set GEMINI_API_KEY in your environment.",
                "sources": [],
                "timestamp": datetime.now().isoformat(),
            }

        prompt = CHATBOT_PROMPT.format(context=context, history=history_text, question=question)

        try:
            answer = await gemini_provider.generate(prompt)
            return {
                "answer": answer,
                "sources": [{"type": "rag", "snippet": r[:200]} for r in rag_results[:3]],
                "run_id": run_id,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Chat AI failed: {e}")
            return {
                "answer": f"AI service unavailable: {type(e).__name__}",
                "sources": [],
                "timestamp": datetime.now().isoformat(),
            }


chat_service = ChatService()
