from __future__ import annotations

import json
import os
import urllib.request


def deterministic_narrative(summary: dict, exceptions: list[dict]) -> dict:
    top = exceptions[:3]
    attention = [
        f"{row['severity']}: {row['code']} {row['customer'] or row['employee']} — {row['actual']}."
        for row in top
    ]
    actions = []
    for row in top:
        action = row["recommended_action"]
        if action and action not in actions:
            actions.append(action)
    return {
        "source": "Deterministic fallback",
        "suggested_interpretation": (
            f"Operations finished {summary['jobs_completed']} of {summary['jobs_scheduled']} scheduled jobs. "
            f"The rule engine found {summary['exception_counts']['Critical']} critical and "
            f"{summary['exception_counts']['High']} high-severity exceptions."
        ),
        "management_attention": attention,
        "recommended_actions": actions,
        "confidence": "High for rule counts; no AI root-cause inference used",
    }


def generate_ai_narrative(summary: dict, exceptions: list[dict]) -> dict:
    api_key = os.getenv("AI_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "").strip()
    if not api_key or not model:
        return deterministic_narrative(summary, exceptions)

    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    evidence = {
        "summary": summary,
        "exceptions": [
            {k: row[k] for k in ("code", "severity", "customer", "employee", "actual", "variance", "evidence", "recommended_action")}
            for row in exceptions[:30]
        ],
    }
    prompt = (
        "You are writing a concise daily operations exception summary for PowerWash management. "
        "Use only the supplied deterministic evidence. Do not add facts or change rule severities. "
        "Return JSON with keys suggested_interpretation (string), management_attention (array of up to 3 strings), "
        "recommended_actions (array of up to 3 strings), and confidence (High, Medium, or Low plus a short reason).\n\n"
        + json.dumps(evidence, ensure_ascii=False)
    )
    payload = json.dumps({"model": model, "input": prompt}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/responses",
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        text = result.get("output_text")
        if not text:
            for item in result.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        text = content.get("text")
                        break
        parsed = json.loads(text)
        parsed["source"] = "AI suggested interpretation"
        return parsed
    except Exception as exc:
        fallback = deterministic_narrative(summary, exceptions)
        fallback["source"] = f"Deterministic fallback; AI call unavailable ({type(exc).__name__})"
        return fallback

