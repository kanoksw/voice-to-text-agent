import json
import os

from validator import validate_data, build_message
from agent_utils import merge_data
from pipeline_full import speech_to_text, extract_fields
from romanize import romanize_person
from plate_normalizer import normalize_license_plate

def run_interactive_agent(first_audio_path: str) -> dict:
    """
    Interactive agent loop:
    - Run round 1 on first_audio_path
    - If incomplete, ask user to provide next audio path
    - Merge only requested fields, validate again, repeat
    """

    # ---------- Round 1 ----------
    transcript = speech_to_text(first_audio_path)
    data = extract_fields(transcript, expected_fields=[])
    
    # ✅ normalize หลัง extract
    if data.get("license_plate") is not None:
        data["license_plate"] = normalize_license_plate(data["license_plate"])
    
    # ✅ validate หลัง normalize
    status, missing = validate_data(data)   

    # ถ้าครบตั้งแต่รอบแรก -> romanize แล้วจบ
    if status == "complete":
        data = romanize_person(data)
        return {"status": "complete", "data": data}
    

    # ---------- Multi-turn ----------
    while status != "complete":
        print("\n=== CURRENT RESULT ===")
        print(json.dumps(
            {
                "status": "incomplete",
                "missing_fields": missing,
                "message": build_message(missing),
                "data_partial": data
            },
            ensure_ascii=False,
            indent=2
        ))

        # ถามผู้ใช้ให้ส่งไฟล์รอบถัดไป
        next_path = input("\nพิมพ์ path ไฟล์เสียงรอบถัดไป (หรือพิมพ์ q เพื่อออก): ").strip()

        # ออกจากโปรแกรม
        if next_path.lower() in ["q", "quit", "exit"]:
            return {
                "status": "incomplete",
                "missing_fields": missing,
                "message": build_message(missing),
                "data_partial": data
            }

        # เช็คว่ามีไฟล์จริงไหม
        if not os.path.isfile(next_path):
            print(f"ไม่พบไฟล์: {next_path}\nลองใหม่อีกครั้ง")
            continue

        # ---------- Next round ----------
        transcript_i = speech_to_text(next_path)

        # สำคัญ: ส่ง expected_fields=missing เพื่อรองรับ implicit answer
        new_data = extract_fields(transcript_i, expected_fields=missing)
        
        # normalize license plate จากคำตอบใหม่
        if new_data.get("license_plate") is not None:
            new_data["license_plate"] = normalize_license_plate(new_data["license_plate"])

        # merge เฉพาะ field ที่ระบบถาม
        data = merge_data(data, new_data, missing)

        # validate ใหม่
        status, missing = validate_data(data)

    # ---------- Complete ----------
    data = romanize_person(data)
    return {"status": "complete", "data": data}


if __name__ == "__main__":
    first = input("ใส่ path ไฟล์เสียงรอบแรก (เช่น input.wav): ").strip()
    if not os.path.isfile(first):
        print(f"ไม่พบไฟล์: {first}")
    else:
        result = run_interactive_agent(first)
        print("\n=== FINAL RESULT ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        