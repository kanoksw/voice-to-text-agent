import os
import uuid
import tempfile
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from pipeline_full import speech_to_text, extract_fields
from validator import validate_data, build_message
from agent_utils import merge_data
from plate_normalizer import normalize_license_plate
from romanize import romanize_person

app = FastAPI(title="Voice Input Validation API", version="1.0")

# -------------------------
# In-memory session store
# -------------------------
# sessions[session_id] = {
#   "data": {...},
#   "missing_fields": [...],
# }
sessions: Dict[str, Dict[str, Any]] = {}

def _save_upload_to_temp(upload: UploadFile) -> str:
    """
    บันทึกไฟล์ upload ลง temp แล้วคืน path ออกมา
    เหตุผล: faster-whisper ชอบทำงานกับ path ไฟล์
    """
    suffix = os.path.splitext(upload.filename or "")[1] or ".wav"
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    with open(path, "wb") as f:
        f.write(upload.file.read())

    return path

def _normalize_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    normalize ข้อมูลบาง field ให้เป็นมาตรฐานก่อน validate
    """
    if data.get("license_plate") is not None:
        data["license_plate"] = normalize_license_plate(data["license_plate"])
    return data

@app.post("/process-audio")
def process_audio(audio: UploadFile = File(...)):
    """
    รอบแรก:
    - รับไฟล์เสียง
    - STT -> Extract (ทุก field) -> Normalize -> Validate
    - ถ้าไม่ครบ: สร้าง session_id แล้วคืนให้
    """
    temp_path = _save_upload_to_temp(audio)

    try:
        transcript = speech_to_text(temp_path)
        data = extract_fields(transcript, expected_fields=[])

        data = _normalize_fields(data)

        status, missing = validate_data(data)

        # ครบแล้ว -> romanize แล้วจบ
        if status == "complete":
            data = romanize_person(data)
            return JSONResponse(
                {
                    "status": "complete",
                    "data": data,
                    "transcript": transcript, 
                }
            )

        # ถ้าไม่ครบจะเปิด session
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "data": data,
            "missing_fields": missing,
        }

        return JSONResponse(
            {
                "status": "incomplete",
                "session_id": session_id,
                "missing_fields": missing,
                "message": build_message(missing),
                "transcript": transcript,
                "data_partial": data,
            }
        )

    finally:
        # ลบไฟล์ temp ทิ้ง
        try:
            os.remove(temp_path)
        except OSError:
            pass


@app.post("/submit-audio")
def submit_audio(
    session_id: str = Form(...),
    audio: UploadFile = File(...),
):
    """
    รอบถัดไป:
    - รับ session_id + ไฟล์เสียงใหม่
    - STT -> Extract เฉพาะ missing_fields -> Normalize -> Merge -> Validate
    - ถ้าครบ: ลบ session
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="session_id not found")

    temp_path = _save_upload_to_temp(audio)

    try:
        # โหลด state เดิม
        current = sessions[session_id]
        current_data = current["data"]
        missing = current["missing_fields"]

        transcript = speech_to_text(temp_path)

        # จำกัดให้ extract เฉพาะ field ที่ถาม (ช่วยลดหลุด)
        new_data = extract_fields(transcript, expected_fields=missing)

        new_data = _normalize_fields(new_data)

        # merge เฉพาะ field ที่ถาม
        merged = merge_data(current_data, new_data, missing)

        # normalize ซ้ำหลัง merge (กันเคสได้ค่าแปลก)
        merged = _normalize_fields(merged)

        status, missing2 = validate_data(merged)

        if status == "complete":
            merged = romanize_person(merged)
            # จบแล้ว ลบ session
            del sessions[session_id]

            return JSONResponse(
                {
                    "status": "complete",
                    "data": merged,
                    "transcript": transcript,
                }
            )

        # ถ้ายังไม่ครบจะ update session แล้วถามต่อ
        sessions[session_id] = {
            "data": merged,
            "missing_fields": missing2,
        }

        return JSONResponse(
            {
                "status": "incomplete",
                "session_id": session_id,
                "missing_fields": missing2,
                "message": build_message(missing2),
                "transcript": transcript,
                "data_partial": merged,
            }
        )

    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
