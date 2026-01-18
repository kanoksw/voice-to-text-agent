from faster_whisper import WhisperModel
import re

# 1) โหลดโมเดล STT
model = WhisperModel("small", device="cpu", compute_type="int8")

# 2) Transcribe
segments, info = model.transcribe("input.wav", beam_size=5)

# 3) เก็บข้อความแต่ละ segment
parts = []
for seg in segments:
    parts.append(seg.text.strip())

# 4) รวม list -> string (raw transcript)
raw_text = " ".join(parts)

print("=== TRANSCRIPT (raw) ===")
print(raw_text)

# 5) Normalize spacing: ตัดช่องว่างซ้ำ ๆ ให้เหลือช่องเดียว
final_text = re.sub(r"\s+", " ", raw_text).strip()

print("\n=== TRANSCRIPT (normalized) ===")
print(final_text)
