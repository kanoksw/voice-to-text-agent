import json
from validator import validate_data, build_message

data = {
    "first_name": "สมชาย",
    "last_name": "นับสกุนใจดี",
    "gender": "male",
    "phone": "08123455678",
    "license_plate": None
}

status, missing = validate_data(data)

if status == "complete":
    output = {"status": "complete", "data": data}
else:
    output = {
        "status": "incomplete",
        "missing_fields": missing,
        "message": build_message(missing)
    }

print(json.dumps(output, ensure_ascii=False, indent=2))

FIELD_THAI = {
    "first_name": "ชื่อ",
    "last_name": "นามสกุล",
    "phone": "เบอร์โทรศัพท์",
    "license_plate": "ทะเบียนรถ"
}

def join_thai_list(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]}และ{items[1]}"
    return "、".join(items[:-1]) + f" และ{items[-1]}"

def build_message(missing_fields: list[str]) -> str:
    fields_th = [FIELD_THAI[f] for f in missing_fields]
    return (
        f"ขอรบกวนยืนยัน{join_thai_list(fields_th)}อีกครั้ง "
        "เนื่องจากระบบอาจได้ยินไม่ชัด"
    )