import json
import os
import re
from typing import Any, Dict, List, Optional

import requests


class LLMServiceError(Exception):
    pass


def _get_env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _get_env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _get_hf_config() -> Dict[str, Any]:
    api_key = os.getenv("HUGGINGFACE_API_KEY", "").strip()
    if not api_key:
        raise LLMServiceError("HUGGINGFACE_API_KEY is not configured")

    base_url = os.getenv(
        "HUGGINGFACE_API_BASE",
        "https://router.huggingface.co/hf-inference/models",
    ).strip()

    # Auto-migrate deprecated HF serverless endpoint to the new router endpoint.
    if base_url.startswith("https://api-inference.huggingface.co"):
        base_url = "https://router.huggingface.co/hf-inference/models"

    return {
        "api_key": api_key,
        "model_id": os.getenv("HUGGINGFACE_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.3").strip(),
        "base_url": base_url,
        "timeout_seconds": _get_env_int("HUGGINGFACE_TIMEOUT_SECONDS", 20),
        "max_new_tokens": _get_env_int("HUGGINGFACE_MAX_NEW_TOKENS", 240),
        "temperature": _get_env_float("HUGGINGFACE_TEMPERATURE", 0.2),
    }


def _extract_generated_text(response_json: Any) -> str:
    if isinstance(response_json, list) and response_json:
        first = response_json[0]
        if isinstance(first, dict):
            if first.get("generated_text"):
                return str(first["generated_text"]).strip()
            if first.get("summary_text"):
                return str(first["summary_text"]).strip()

    if isinstance(response_json, dict):
        if response_json.get("generated_text"):
            return str(response_json["generated_text"]).strip()
        if response_json.get("error"):
            raise LLMServiceError(f"Hugging Face error: {response_json['error']}")

    raise LLMServiceError("No generated text returned by Hugging Face")


def _call_huggingface(prompt: str, max_new_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
    cfg = _get_hf_config()
    url = f"{cfg['base_url']}/{cfg['model_id']}"
    headers = {"Authorization": f"Bearer {cfg['api_key']}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens if max_new_tokens is not None else cfg["max_new_tokens"],
            "temperature": temperature if temperature is not None else cfg["temperature"],
            "return_full_text": False,
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=cfg["timeout_seconds"])
    except requests.exceptions.Timeout as exc:
        raise LLMServiceError("Hugging Face request timed out") from exc
    except requests.RequestException as exc:
        raise LLMServiceError(f"Network error while calling Hugging Face: {exc}") from exc

    if response.status_code == 410:
        raise LLMServiceError(
            "Hugging Face endpoint is deprecated. Use HUGGINGFACE_API_BASE=https://router.huggingface.co/hf-inference/models"
        )

    if response.status_code >= 400:
        short_body = response.text[:300]
        raise LLMServiceError(f"Hugging Face API failed ({response.status_code}): {short_body}")

    try:
        response_json = response.json()
    except ValueError as exc:
        raise LLMServiceError("Invalid JSON response from Hugging Face") from exc

    return _extract_generated_text(response_json)


def _extract_json_object(text: str) -> Dict[str, Any]:
    cleaned = text.strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        candidate = match.group(0)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    raise LLMServiceError("Model response did not contain valid JSON")


def _normalize_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


def _med_disclaimer() -> str:
    return "This guidance is informational only and not a medical diagnosis. For severe symptoms, seek emergency care immediately."


def generate_personalized_advice(
    product_name: str,
    detected_allergens: List[str],
    user_allergies: List[str],
    ingredients_text: str,
) -> Dict[str, Any]:
    if not detected_allergens:
        return {
            "verdict_summary": "No matching allergens were detected for your profile.",
            "risk_explanation": "Based on the scan, there is no direct allergen match to your saved allergies.",
            "hidden_ingredient_watchouts": [],
            "safer_next_step": "Still review packaging labels for manufacturing warnings before consuming.",
            "disclaimer": _med_disclaimer(),
        }

    prompt = (
        "You are a food-allergy safety assistant. Return only JSON.\n"
        "Task: Explain personal risk from scanned food.\n"
        f"Product: {product_name}\n"
        f"Detected allergens: {', '.join(detected_allergens)}\n"
        f"User allergies: {', '.join(user_allergies) if user_allergies else 'not provided'}\n"
        f"OCR ingredients text: {ingredients_text[:1200] if ingredients_text else 'not available'}\n\n"
        "Return strict JSON object with keys:\n"
        "verdict_summary (string), risk_explanation (string), hidden_ingredient_watchouts (array of short strings), safer_next_step (string).\n"
        "Keep risk_explanation practical and concise."
    )

    raw = _call_huggingface(prompt, max_new_tokens=260, temperature=0.1)
    parsed = _extract_json_object(raw)

    return {
        "verdict_summary": str(parsed.get("verdict_summary", "Potentially unsafe for your allergy profile.")).strip(),
        "risk_explanation": str(parsed.get("risk_explanation", "Detected allergens overlap with your known allergies.")).strip(),
        "hidden_ingredient_watchouts": _normalize_list(parsed.get("hidden_ingredient_watchouts")),
        "safer_next_step": str(parsed.get("safer_next_step", "Avoid this product and verify safer alternatives.")).strip(),
        "disclaimer": _med_disclaimer(),
    }


def generate_alternatives(
    product_name: str,
    detected_allergens: List[str],
    user_allergies: List[str],
) -> Dict[str, Any]:
    prompt = (
        "You are a food-allergy shopping assistant. Return only JSON.\n"
        f"Product to avoid: {product_name}\n"
        f"Detected allergens: {', '.join(detected_allergens) if detected_allergens else 'unknown'}\n"
        f"User allergies: {', '.join(user_allergies) if user_allergies else 'not provided'}\n\n"
        "Return strict JSON with key alternatives as an array of 3 to 5 items.\n"
        "Each item keys: alternative_name, why_safer, caution_note.\n"
        "Do not claim guaranteed safety."
    )

    raw = _call_huggingface(prompt, max_new_tokens=300, temperature=0.3)
    parsed = _extract_json_object(raw)
    items = parsed.get("alternatives", [])

    results = []
    if isinstance(items, list):
        for item in items[:5]:
            if not isinstance(item, dict):
                continue
            results.append(
                {
                    "alternative_name": str(item.get("alternative_name", "")).strip(),
                    "why_safer": str(item.get("why_safer", "")).strip(),
                    "caution_note": str(item.get("caution_note", "")).strip(),
                }
            )

    if not results:
        results = [
            {
                "alternative_name": "Certified allergen-free equivalent",
                "why_safer": "Products with clear allergen-free labeling reduce accidental exposure risk.",
                "caution_note": "Always re-check labels for facility cross-contact warnings.",
            }
        ]

    return {"alternatives": results, "disclaimer": _med_disclaimer()}


def generate_emergency_guidance(
    suspected_allergen: str,
    symptoms: str,
    has_epinephrine: str,
    age_group: str,
) -> Dict[str, Any]:
    prompt = (
        "You are an emergency allergy triage assistant. Return only JSON.\n"
        f"Suspected allergen: {suspected_allergen}\n"
        f"Symptoms: {symptoms}\n"
        f"Epinephrine available: {has_epinephrine}\n"
        f"Age group: {age_group}\n\n"
        "Return strict JSON object with keys:\n"
        "severity_level (string: mild/moderate/severe), immediate_actions (array of step strings), when_to_seek_emergency (string), follow_up_actions (array of step strings).\n"
        "Prioritize calling emergency services for severe breathing/swelling symptoms."
    )

    raw = _call_huggingface(prompt, max_new_tokens=320, temperature=0.1)
    parsed = _extract_json_object(raw)

    return {
        "severity_level": str(parsed.get("severity_level", "unknown")).strip().lower(),
        "immediate_actions": _normalize_list(parsed.get("immediate_actions")),
        "when_to_seek_emergency": str(
            parsed.get("when_to_seek_emergency", "Call emergency services immediately if breathing trouble, throat swelling, dizziness, or fainting occur.")
        ).strip(),
        "follow_up_actions": _normalize_list(parsed.get("follow_up_actions")),
        "disclaimer": _med_disclaimer(),
    }


def answer_faq_question(question: str, user_allergies: List[str]) -> Dict[str, str]:
    prompt = (
        "You are a food allergy education assistant. Return only JSON.\n"
        f"User allergies: {', '.join(user_allergies) if user_allergies else 'not provided'}\n"
        f"Question: {question}\n\n"
        "Return strict JSON object with keys: answer, safety_disclaimer.\n"
        "Use concise educational language. No diagnosis. No medication dosage."
    )

    raw = _call_huggingface(prompt, max_new_tokens=220, temperature=0.2)
    parsed = _extract_json_object(raw)

    return {
        "answer": str(parsed.get("answer", "I could not generate an answer right now.")).strip(),
        "safety_disclaimer": str(parsed.get("safety_disclaimer", _med_disclaimer())).strip(),
    }


def generate_allergy_advice(
    allergens: str,
    product_name: str = "this product",
    user_allergies: str = "",
) -> str:
    detected = [a.strip() for a in allergens.split(",") if a.strip()]
    user_list = [a.strip() for a in user_allergies.split(",") if a.strip()]
    result = generate_personalized_advice(
        product_name=product_name,
        detected_allergens=detected,
        user_allergies=user_list,
        ingredients_text="",
    )
    return f"{result['verdict_summary']} {result['risk_explanation']}".strip()
