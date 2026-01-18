import re
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct"

def romanize_thai_name(th_name: str) -> str:
    """
    Convert Thai personal name to common English romanization.
    If conversion is uncertain, return the original Thai name.
    """
    system_prompt = (
        "You convert Thai personal names to English romanization.\n"
        "Rules:\n"
        "- Use common Thai-to-English spelling.\n"
        "- Return ONLY the romanized name (no explanation).\n"
        "- If uncertain, return the original Thai name.\n"
        "- Capitalize the first letter."
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": th_name},
        ],
        "stream": False
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()

    out = r.json()["message"]["content"].strip()
    # safety: remove code fences if any
    out = re.sub(r"^```.*?\n", "", out)
    out = re.sub(r"\n```$", "", out)
    out = out.strip()
    out = out.replace(" ", "")  # ลบ space ให้เป็นคำเดียว เช่น Jai Dei -> Jaidee
    
    # ถ้า LLM ส่งของแปลก/ว่าง → fallback
    if not out or any(ch in out for ch in "{}[]:"):
        return th_name

    return out


def romanize_person(data: dict) -> dict:
    """
    Romanize first_name and last_name only when present.
    """
    new_data = data.copy()

    if new_data.get("first_name"):
        new_data["first_name"] = romanize_thai_name(new_data["first_name"])

    if new_data.get("last_name"):
        new_data["last_name"] = romanize_thai_name(new_data["last_name"])

    return new_data
