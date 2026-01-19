import re
from typing import Dict, List, Tuple

def validate_phone(phone: str | None) -> bool:
    if phone is None:
        return False
    return bool(re.fullmatch(r"0\d{9}", phone))

def validate_name(name: str | None) -> bool:
    if name is None:
        return False

    # คำที่มักเกิดจาก STT error
    suspicious_words = ["นับสกุน", "นามสกุล", "ชื่อ"]

    for w in suspicious_words:
        if w in name:
            return False

    return True

def validate_license_plate(p: str | None) -> bool:
    if p is None:
        return False

    p = p.strip()

    # EN: AB1234 / ABC1234
    if re.fullmatch(r"[A-Za-z]{1,3}\d{1,4}", p):
        return True

    # TH: กข1234
    if re.fullmatch(r"[ก-๙]{1,3}\d{1,4}", p):
        return True

    return False

def validate_gender(g: str | None) -> bool:
    if g is None:
        return False
    g = g.strip().lower()
    return g in ["male", "female"]

def validate_data(data: Dict) -> Tuple[str, List[str]]:
    missing_or_invalid = []

    if not validate_name(data.get("first_name")):
        missing_or_invalid.append("first_name")

    if not validate_name(data.get("last_name")):
        missing_or_invalid.append("last_name")

    if not validate_phone(data.get("phone")):
        missing_or_invalid.append("phone")
        
    if not validate_gender(data.get("gender")):
        missing_or_invalid.append("gender")

    if not validate_license_plate(data.get("license_plate")):
        missing_or_invalid.append("license_plate")

    status = "complete" if not missing_or_invalid else "incomplete"
    return status, missing_or_invalid

FIELD_THAI = {
    "first_name": "ชื่อ",
    "last_name": "นามสกุล",
    "phone": "เบอร์โทรศัพท์",
    "gender": "เพศ",
    "license_plate": "ทะเบียนรถ"
}

def build_message(missing_fields: List[str]) -> str:
    fields_th = [FIELD_THAI[f] for f in missing_fields]
    return (
        "ขอรบกวนยืนยัน"
        + "และ".join(fields_th)
        + "อีกครั้ง เนื่องจากระบบอาจได้ยินไม่ชัด"
    )