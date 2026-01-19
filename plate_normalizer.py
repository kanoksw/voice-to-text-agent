import re

# map คำอ่าน → ตัวอักษรไทย (เติมเพิ่มได้เรื่อย ๆ)
THAI_SPELL_MAP = {
    "กอไก่": "ก",
    "ขอไข่": "ข",
    "คอควาย": "ค",
    "งองู": "ง",
    "จอจาน": "จ",
    "ฉอฉิ่ง": "ฉ",
    "ชอช้าง": "ช",
    "ซอโซ่": "ซ",
    "ดอเด็ก": "ด",
    "ตอเต่า": "ต",
    "ถอถุง": "ถ",
    "ทอทหาร": "ท",
    "นอหนู": "น",
    "บอใบไม้": "บ",
    "ปอปลา": "ป",
    "ผอผึ้ง": "ผ",
    "ฝอฝา": "ฝ",
    "พอพาน": "พ",
    "ฟอฟัน": "ฟ",
    "มอม้า": "ม",
    "ยอยักษ์": "ย",
    "รอเรือ": "ร",
    "ลอลิง": "ล",
    "วอแหวน": "ว",
    "ศอศาลา": "ศ",
    "สอเสือ": "ส",
    "หอหีบ": "ห",
    "ฮอนกฮูก": "ฮ",
    "ขอควาย": "ค",
    "ซอช้าง": "ช",
    "พอผึ้ง": "ผ",
}

FILLERS = ["ทะเบียน", "ป้ายทะเบียน", "ทะเบียนรถ", "รถ", "จังหวัด", "กรุงเทพ", "กทม", "ครับ", "ค่ะ"]

def normalize_license_plate(text: str | None) -> str | None:
    if not text:
        return None

    s = text.strip()
    
    # 1) ลบคำฟิลเลอร์แบบ "ไม่ทำลายรูปประโยค"
    #    (แทนที่จะลบ space ทั้งหมดก่อน)
    s_up = s.upper()
    for w in FILLERS:
        s_up = s_up.replace(w.upper(), " ")

    # 2) EN plate: รองรับ AB1234 / AB 1234 / AB-1234 / AB1234.
    #    ใช้ boundary กันตัวอักษรแปลก ๆ ติดหน้า-ท้าย
    m_en = re.search(
        r"(?<![A-Z0-9])([A-Z]{1,3})[\s\-\.]*([0-9]{1,4})(?![A-Z0-9])",
        s_up
    )
    if m_en:
        return f"{m_en.group(1)}{m_en.group(2)}"

    # 3) TH plate: กข1234 / ก.ไก่ ข.ไข่ 1 2 3 4 (ผ่าน map)
    s_th = s.strip()

    # ลบฟิลเลอร์อีกรอบฝั่งไทย
    for w in FILLERS:
        s_th = s_th.replace(w, " ")

    # normalize separators
    s_th = s_th.replace("-", " ").replace(".", " ")
    s_th = re.sub(r"\s+", " ", s_th).strip().lower()

    # แปลงคำอ่านเป็นตัวอักษรไทย (greedy)
    for k in sorted(THAI_SPELL_MAP.keys(), key=len, reverse=True):
        s_th = s_th.replace(k, THAI_SPELL_MAP[k])

    # ดึงเฉพาะ ไทย+เลข แล้วเอามาต่อกัน
    s_th = re.sub(r"[^0-9ก-๙]", "", s_th)
    
    # ✅ NEW: บีบให้ติดกันไปเลย (กันกรณีมีช่องว่างหลงเหลือ)
    s_th = s_th.replace(" ", "")

    m_th = re.fullmatch(r"([ก-ฮ]{1,3})(\d{1,4})", s_th)
    if not m_th:
        return None

    return f"{m_th.group(1)}{m_th.group(2)}"

