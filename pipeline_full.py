import json
import re
import requests
from faster_whisper import WhisperModel
from validator import validate_data, build_message
from romanize import romanize_person
from plate_normalizer import normalize_license_plate

# =====================
# STT
# =====================
def speech_to_text(audio_path: str) -> str:
    model = WhisperModel("large", device="cpu", compute_type="int8")

    segments, _ = model.transcribe(
        audio_path,
        beam_size=10,
        language="th",
        vad_filter=True
    )

    parts = [seg.text.strip() for seg in segments]
    raw_text = " ".join(parts)

    # normalize spacing
    final_text = re.sub(r"\s+", " ", raw_text).strip()
    
    print("\n=== TRANSCRIPT ===")
    print(final_text)
    return final_text


# =====================
# LLM Extraction
# =====================
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct"

def extract_fields(transcript: str, expected_fields: list[str] | None = None) -> dict:
    expected_fields = expected_fields or []

    base_rules = (
        "Return ONLY valid JSON with keys:\n"
        "first_name, last_name, gender, phone, license_plate.\n"
        "- Always return all keys.\n"
        "- Use null for missing.\n"
        "- Do not hallucinate.\n"
        "- phone: digits only.\n"
        "- gender: male/female/other/null; ชาย/ผู้ชาย=male, หญิง/ผู้หญิง=female.\n"
    )

    # โหมดรอบถามกลับ: จำกัดให้เติมเฉพาะ field ที่ถาม
    if expected_fields:
        focus_rules = (
            f"You are ONLY allowed to fill these fields: {expected_fields}.\n"
            "All other fields MUST be null.\n"
            "You may infer implicitly if transcript matches the requested field(s).\n"
        )
    else:
        # โหมดรอบแรก: ให้พยายามเติมทุก field ตาม transcript
        focus_rules = (
            "Fill as many fields as you can from the transcript.\n"
            "If a field is not explicitly present, set it to null.\n"
        )

    license_rules = (
        "License plate rules:\n"
        "- Convert Thai spelled letters to Thai characters.\n"
        "- Example: 'กอไก่ ขอไข่ 1234' -> 'กข1234'\n"
    )

    system_prompt = (
        "You extract structured fields from Thai speech transcripts.\n"
        + base_rules
        + focus_rules
        + license_rules
        + "No explanation, no markdown.\n"
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transcript:\n{transcript}"},
        ],
        "stream": False,
        "options": {  # ✅ ทำให้ผลนิ่งขึ้น
            "temperature": 0,
            "top_p": 1
        }
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()

    content = r.json()["message"]["content"].strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    raw = json.loads(content)

    # ✅ NORMALIZE OUTPUT (หัวใจของ bug นี้)
    normalized = {
        "first_name": raw.get("first_name"),
        "last_name": raw.get("last_name"),
        "gender": raw.get("gender"),
        "phone": raw.get("phone"),
        "license_plate": raw.get("license_plate"),
    }

    return normalized


# =====================
# FULL PIPELINE (Step 4.6)
# =====================
def run_pipeline(audio_path: str) -> dict:
    # Step 1: STT
    transcript = speech_to_text(audio_path)

    # Step 2: LLM extraction
    data = extract_fields(transcript)
    
    if data.get("license_plate") is not None:
        data["license_plate"] = normalize_license_plate(data["license_plate"])
        
    # Step 3: Validation
    status, missing = validate_data(data)

    # Step 4: Final output (ask all missing at once)
    if status == "complete":
        data_en = romanize_person(data)
        return {
            "status": "complete",
            "data": data_en
        }
    else:
        return {
            "status": "incomplete",
            "missing_fields": missing,
            "message": build_message(missing)
        }


if __name__ == "__main__":
    result = run_pipeline("testcase1.wav")
    print(json.dumps(result, ensure_ascii=False, indent=2))

