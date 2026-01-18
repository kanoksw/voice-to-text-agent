from faster_whisper import WhisperModel
import re
import json
import requests

# ---------- STT ----------
def speech_to_text(audio_path: str) -> str:
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, beam_size=5)

    parts = [seg.text.strip() for seg in segments]
    raw_text = " ".join(parts)

    # normalize spacing
    final_text = re.sub(r"\s+", " ", raw_text).strip()
    return final_text


# ---------- LLM ----------
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct"

def extract_fields(transcript: str) -> dict:
    system_prompt = (
        "You extract structured fields from Thai speech transcripts.\n"
        "Return ONLY valid JSON with keys:\n"
        "first_name, last_name, gender, phone, license_plate.\n\n"
        "Rules:\n"
        "- Use null if missing.\n"
        "- gender: male, female, other, null.\n"
        "- Thai gender mapping: ชาย/ผู้ชาย=male, หญิง/ผู้หญิง=female.\n"
        "- phone digits only.\n"
        "- No explanation."
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transcript:\n{transcript}"},
        ],
        "stream": False
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()

    content = r.json()["message"]["content"].strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    return json.loads(content)


# ---------- PIPELINE ----------
if __name__ == "__main__":
    transcript = speech_to_text("input.wav")
    print("=== TRANSCRIPT ===")
    print(transcript)

    data = extract_fields(transcript)
    print("\n=== EXTRACTED DATA ===")
    print(json.dumps(data, ensure_ascii=False, indent=2))
