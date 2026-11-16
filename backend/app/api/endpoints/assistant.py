import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import (
    User, Document, ExtractedField, VerificationResult, Issue,
    ChatConversation, ChatMessage
)
from backend.app.core.dependencies import get_current_user
from backend.app.core.config import settings
from backend.app.services.rag.engine import rag_engine

logger = logging.getLogger("evidencerag.assistant")

router = APIRouter(prefix="/assistant", tags=["Ask Your Document AI Assistant"])

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None

@router.get("/history")
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve chat history for the logged-in student."""
    conv = db.query(ChatConversation).filter(
        ChatConversation.user_id == current_user.id
    ).order_by(ChatConversation.updated_at.desc()).first()

    if not conv:
        return {"conversation_id": None, "messages": []}

    msgs = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conv.id
    ).order_by(ChatMessage.created_at.asc()).all()

    formatted_msgs = []
    for m in msgs:
        refs = []
        if m.evidence_references:
            try:
                refs = json.loads(m.evidence_references)
            except Exception:
                pass
        formatted_msgs.append({
            "id": m.id,
            "sender": m.sender,
            "message": m.message,
            "evidence_references": refs,
            "created_at": m.created_at
        })

    return {"conversation_id": conv.id, "messages": formatted_msgs}

@router.post("/chat")
def chat_with_assistant(
    chat_req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evidence-grounded conversational assistant that answers student questions
    strictly based on the student's uploaded documents and verification results.
    """
    query = chat_req.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Fetch authenticated student's documents and verified issues
    user_docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    user_doc_ids = [d.id for d in user_docs]
    user_issues = db.query(Issue).filter(Issue.document_id.in_(user_doc_ids)).all() if user_doc_ids else []

    # 2. Extract context from student's data
    doc_summaries = []
    evidence_citations = []

    for d in user_docs:
        field_strs = [f"{ef.field_name}: '{ef.field_value}'" for ef in d.extracted_fields[:6]]
        doc_summaries.append(f"• Document '{d.original_filename}' ({d.category}): {', '.join(field_strs)}")

    issue_summaries = []
    for iss in user_issues:
        issue_summaries.append(
            f"• Issue in {iss.document_name} [{iss.severity.upper()}]: {iss.title}. Evidence: '{iss.evidence_snippet}'. Correction: {iss.suggested_correction}"
        )
        evidence_citations.append({
            "document_name": iss.document_name,
            "page_number": iss.page_number or 1,
            "citation": f"[{iss.document_name}, Page {iss.page_number or 1}] - {iss.title}"
        })

    # Retrieve relevant RAG rules
    retrieved_rules = rag_engine.retrieve(query=query, top_k=2)
    rag_context = "\n".join([f"• [{r['rule_id']}] {r['title']}: {r['content']} (Source: {r['source']})" for r in retrieved_rules])

    # 3. Attempt Ollama LLM response
    llm_answer = None
    llm_used = False

    try:
        system_prompt = (
            "You are EvidenceRAG Assistant, an expert advisor helping scholarship students resolve application document errors. "
            "You MUST ONLY use the student's uploaded documents and verified issues provided in the context. "
            "Never invent missing dates, names, or false claims. Always cite the document name and page number."
        )
        user_context_prompt = (
            f"Student Query: {query}\n\n"
            f"Student's Uploaded Documents ({len(user_docs)} files):\n"
            f"{chr(10).join(doc_summaries) if doc_summaries else 'None uploaded yet.'}\n\n"
            f"Detected Issues in Student's Documents ({len(user_issues)} issues):\n"
            f"{chr(10).join(issue_summaries) if issue_summaries else 'Zero defects identified.'}\n\n"
            f"Applicable Regulatory Knowledge:\n{rag_context}\n\n"
            "Provide a helpful, precise, evidence-grounded answer with citations and actionable advice."
        )

        with httpx.Client(timeout=4.0) as client:
            resp = client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": f"{system_prompt}\n\n{user_context_prompt}",
                    "stream": False
                }
            )
            if resp.status_code == 200:
                llm_answer = resp.json().get("response", "").strip()
                llm_used = True
    except Exception as e:
        logger.info(f"Ollama unavailable for assistant chat, generating deterministic grounded answer: {e}")

    # 4. Deterministic Grounded Fallback if LLM is offline
    if not llm_answer:
        q_lower = query.lower()
        if "why" in q_lower or "flag" in q_lower or "issue" in q_lower or "error" in q_lower:
            if user_issues:
                issue_lines = [
                    f"**{iss.document_name}** (Page {iss.page_number or 1}): {iss.title}\n"
                    f"  - **Finding:** {iss.explanation}\n"
                    f"  - **Statutory Source:** {iss.rag_source or 'Scholarship Portal Guidelines'}\n"
                    f"  - **Action Required:** {iss.suggested_correction}"
                    for iss in user_issues[:3]
                ]
                llm_answer = (
                    f"Here is why your documents were flagged based on statutory verification rules:\n\n"
                    + "\n\n".join(issue_lines)
                )
            else:
                llm_answer = (
                    "None of your uploaded documents currently have any flagged critical issues! "
                    "Your uploaded credentials conform to mandatory completeness criteria."
                )
        elif "missing" in q_lower:
            missing_issues = [iss for iss in user_issues if "missing" in iss.category.lower() or "missing" in iss.title.lower()]
            if missing_issues:
                llm_answer = (
                    "The following mandatory statutory items are missing from your documents:\n"
                    + "\n".join([f"• [{iss.document_name}, Page {iss.page_number or 1}]: {iss.title} — Expected: '{iss.expected_value or 'Valid value'}'" for iss in missing_issues])
                )
            else:
                llm_answer = "All mandatory fields across your uploaded certificates are present and accounted for."
        else:
            top_rule = retrieved_rules[0] if retrieved_rules else None
            llm_answer = (
                f"Regarding your query: '{query}'\n\n"
                f"Based on your {len(user_docs)} uploaded certificate(s), the system evaluated mandatory statutory standards. "
            )
            if top_rule:
                llm_answer += f"Per **{top_rule['title']}** ({top_rule['source']}):\n> {top_rule['content']}\n\n"
            if user_issues:
                llm_answer += f"You have {len(user_issues)} issue(s) needing attention prior to portal submission. Check your Dashboard for detailed evidence highlighting."

    # 5. Persist to ChatConversation and ChatMessage
    conv = db.query(ChatConversation).filter(ChatConversation.user_id == current_user.id).first()
    if not conv:
        conv = ChatConversation(user_id=current_user.id, title="Scholarship Verification Chat")
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # User message
    user_msg = ChatMessage(conversation_id=conv.id, sender="user", message=query)
    db.add(user_msg)

    # Assistant message
    assistant_msg = ChatMessage(
        conversation_id=conv.id,
        sender="assistant",
        message=llm_answer,
        evidence_references=json.dumps(evidence_citations[:4])
    )
    db.add(assistant_msg)
    db.commit()

    return {
        "conversation_id": conv.id,
        "message": llm_answer,
        "evidence_references": evidence_citations[:4],
        "llm_used": llm_used,
        "model_name": settings.OLLAMA_MODEL if llm_used else "EvidenceRAG Deterministic Grounding Engine"
    }
