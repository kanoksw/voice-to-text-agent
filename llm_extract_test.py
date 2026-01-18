import json
import re
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct"

def extract_fields(transcript: str) -> dict:
    system_prompt = (
        "You extract structured fields from Thai speech transcripts.\n"
        "Return ONLY a valid JSON object with these keys:\n"
        "first_name, last_name, gender, phone, license_plate.\n\n"
        "Rules:\n"
        "- Use null if a field is missing.\n"
        "- gender must be one of: male, female, other, null.\n"
        "- Thai gender mapping: ชาย/ผู้ชาย = male, หญิง/ผู้หญิง = female.\n"
        "- phone must contain digits only (remove spaces).\n"
        "- Do NOT add any explanation or markdown."
    )

    user_prompt = f"""
Transcript:
{transcript}
"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()

    content = r.json()["message"]["content"].strip()

    # safety: remove ```json fences if model adds them
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    return json.loads(content)


if __name__ == "__main__":
    transcript = "ชื่อสมชาย นามสกุลใจดี ผู้ชาย เบอร์ 081 234 55678"

    data = extract_fields(transcript)
    print(json.dumps(data, ensure_ascii=False, indent=2))