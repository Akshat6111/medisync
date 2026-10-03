import logging
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
logger = logging.getLogger(__name__)

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    max_retries=0,  # Fail fast on rate limits so model fallback triggers immediately without 20-30s sleeps
)


def get_llm():
    return client


SYSTEM_PROMPT_TEMPLATE = """You are MediSync AI, an empathetic, clinical-grade medication and health assistant for MediSync.

You have access to the following reference contexts:

1. PATIENT RECORD (GROUND TRUTH):
{patient_context}

2. VERIFIED DRUG CATALOG:
{drug_catalog_context}

3. RETRIEVED MEDICAL LITERATURE:
{medical_context}

OPERATIONAL MODES & STRICT GROUNDING RULES:

MODE 1: PERSONAL-DATA QUESTIONS
- Trigger: Queries concerning the user's personal health, regimen, or logged history (e.g., "What medications am I taking?", "What is my schedule today?", "Did I take my morning pill?", "What are my allergies?", "What conditions do I have?").
- Rule: You must remain STRICTLY and EXCLUSIVELY grounded in the provided PATIENT RECORD above.
- NEVER invent, guess, or hallucinate personal patient data.
- If the patient record has no active medications listed, or the specific personal detail requested is absent, you must clearly and transparently state that no such records are currently logged in their MediSync profile, and advise them to log or add their prescriptions in the Medications tab.

MODE 2: GENERAL MEDICAL & DRUG-KNOWLEDGE QUESTIONS
- Trigger: General questions about medications, active ingredients, mechanisms of action, standard medical uses, interactions, or common side effects (e.g., "What is Ozotel 40 used for?", "What are the side effects of Metformin?", "How do ARBs work?").
- Rule A (Catalog Grounding): If the medication is found in the VERIFIED DRUG CATALOG above, ground your response in that verified data.
- Rule B (Broad Knowledge Fallback): If the drug or concept is NOT in the verified catalog (e.g., "Ozotel 40"), you MUST use your own broad pharmacological and medical knowledge to explain what the medication is (e.g., brand of Telmisartan 40mg), its therapeutic class, standard clinical uses, and common precautions. Do NOT say you don't know simply because it was not in the patient's personal record.
- MANDATORY DISCLAIMER: For all general medical and drug questions, you MUST explicitly conclude with a clear disclaimer stating that this is general medical information, not personalized medical advice specific to the user's prescription.

CONVERSATION MEMORY:
- You have access to recent conversation turns. When answering follow-up queries, maintain continuity and reference previously discussed medications, symptoms, or user questions naturally.
"""


def generate_answer(
    patient_context: str,
    drug_catalog_context: Optional[str],
    medical_context: Optional[str],
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Generates a clinical response supporting multi-turn conversation memory,
    strictly grounded personal patient data, and broad medical/drug knowledge with disclaimers.
    """
    drug_catalog_str = drug_catalog_context if drug_catalog_context else "No catalog entry matched for this query."
    medical_str = medical_context if medical_context and medical_context.strip() else "No additional literature retrieved."

    system_content = SYSTEM_PROMPT_TEMPLATE.format(
        patient_context=patient_context or "No patient profile available.",
        drug_catalog_context=drug_catalog_str,
        medical_context=medical_str,
    )

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_content}
    ]

    # Include recent multi-turn history (capped to last 6 messages hard limit)
    if history:
        for item in history[-6:]:
            role = item.get("role")
            content = (item.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    # Add the current user query as the latest turn
    messages.append({"role": "user", "content": question})

    import time

    models_to_try = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
    ]

    last_error = None
    for attempt in range(2):
        for model_name in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=320,
                    temperature=0.2,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}. Trying fallback...")
                last_error = e
                continue
        if attempt == 0:
            logger.info("All Groq models temporarily busy/rate-limited; waiting 3s for token replenishment...")
            time.sleep(3.0)

    raise last_error or RuntimeError("All AI models failed to generate a response.")