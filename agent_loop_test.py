import json
from pipeline_full import speech_to_text, extract_fields
from validator import validate_data, build_message
from agent_utils import merge_data

# ----------------------
# รอบแรก (สมมติว่ารันมาแล้ว)
# ----------------------
current_data = {
    "first_name": "สมชาย",
    "last_name": "ใจดี",
    "gender": "male",
    "phone": "0812345678",
    "license_plate": None
}

status, missing = validate_data(current_data)

print("=== ROUND 1 RESULT ===")
print(json.dumps({
    "status": status,
    "missing_fields": missing,
    "message": build_message(missing)
}, ensure_ascii=False, indent=2))

# ----------------------
# รอบสอง: รับเสียงใหม่ (เฉพาะที่ถาม)
# ----------------------
print("\n--- กรุณาพูดข้อมูลที่ระบบขอ ---")

# สมมติ user พูดแล้วอัดเป็น input2.wav
transcript_2 = speech_to_text("input3.wav")
new_data = extract_fields(transcript_2, expected_fields=missing)

# merge เฉพาะ field ที่ถาม
merged_data = merge_data(current_data, new_data, missing)

status2, missing2 = validate_data(merged_data)

print("\n=== ROUND 2 RESULT ===")
if status2 == "complete":
    print(json.dumps({
        "status": "complete",
        "data": merged_data
    }, ensure_ascii=False, indent=2))
else:
    print(json.dumps({
        "status": "incomplete",
        "missing_fields": missing2,
        "message": build_message(missing2)
    }, ensure_ascii=False, indent=2))

