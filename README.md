# voice-to-text-agent

ระบบแปลงเสียงพูดหรือ transcript เป็น Structured Data โดยออกแบบมาเพื่อรองรับเสียงพูดที่ไม่ครบหรือไม่ชัด โดยมีการใช้ Speech-to-Text (STT), Large Language Model (LLM) และกฎแบบ Rule-based เพื่อให้ได้ผลลัพธ์ที่ถูกต้องและเชื่อถือได้

--------
## ภาพรวมของระบบ (Overview)

ระบบนี้ถูกออกแบบมาเพื่อดึงข้อมูลต่อไปนี้จากเสียงพูดของผู้ใช้ รองรับทั้งการพูดภาษาไทยและอังกฤษ

- `first_name` : ชื่อ
- `last_name` : นามสกุล
- `gender` : เพศ
- `phone` : เบอร์โทรศัพท์
- `license_plate` : ป้ายทะเบียนรถ

ระบบมีการทำงาน 2 แบบ คือ
1. การประมวลผลครั้งเดียว (Single-pass pipeline) : ใส่เสียงเข้ามา หากข้อมูลครบและถูกต้อง จะขึ้นแจ้งเตือนว่า complete หากข้อมูลไม่ครบหรือมีบางส่วนไม่ชัดเจน จะแสดงผลว่า incomplete และขาดข้อมูลส่วนไหนอยู่
2. การโต้ตอบหลายรอบ (Interactive ) : หากข้อมูลไม่ครบ ระบบจะสามารถแจ้งกลับว่าขาดข้อมูลอะไร และขอข้อมูลเป็นไฟล์เสียงเพิ่ม

-----

## สถาปัตยกรรมของระบบ (Architecture)

โครงสร้างการทำงานโดยรวมเป็นดังนี้

Audio Input (.wav)  
↓  
Speech-to-Text (Faster-Whisper)  
↓  
Text Normalization  
↓  
Information Extraction (LLM)  
↓  
Rule-based Validation & Normalization  
↓  
Structured JSON Output



### องค์ประกอบหลัก

| ส่วน | หน้าที่ |
|---|---|
| STT | แปลงเสียงพูดเป็นข้อความ |
| LLM | ดึงข้อมูลเชิงโครงสร้างจากข้อความ |
| Rule-based Logic | ตรวจสอบความถูกต้องของข้อมูล |

-----

## การแบ่งส่วนการใช้งาน AI และ Rule-based

ระบบนี้ไม่ได้ใช้ AI ทั้งหมด แต่เลือกใช้ในจุดที่เหมาะสม

ส่วนที่ใช้ AI / ML คือ
- **Speech-to-Text** : Faster-Whisper (Whisper large)
- **Information Extraction** : LLM (ผ่าน Ollama)

### AI ถูกใช้ในส่วนที่:
- ข้อมูลมีความไม่แน่นอน
- ภาษามีความหลากหลาย
- ผู้ใช้พูดแบบไม่ระบุ label ชัดเจน
- รองรับทั้งภาษาไทยและภาษาอังกฤษ

### ส่วนที่ใช้ Rule-based (จุดที่ต้องการความถูกต้องแบบกำหนดชัดเจน)
- ตรวจสอบเบอร์โทรศัพท์ว่าครบ 10 หลักหรือไม่
- ตรวจสอบรูปแบบป้ายทะเบียน
- แปลงคำอ่านป้ายทะเบียน (กอไก่ → ก)
- ตัดสินว่าข้อมูลครบหรือไม่ครบ

-----

## การเลือกใช้ Speech-to-Text (STT)
เหตุผลที่เลือก Faster-Whisper:
- ทำงานแบบ local 100%
- รองรับภาษาไทยและอังกฤษได้ดี
- ไม่มีค่าใช้จ่าย
- ควบคุม model / parameter ได้เอง
- คุณภาพดีในสภาพเสียงไม่สมบูรณ์
  
การตั้งค่าที่ใช้:
- Model: `large`
- Beam size: `10`
- VAD filter: เปิดใช้งาน
  
---

## การเลือกใช้ LLM
เหตุผลที่เลือก Ollama:
- ทำงานบนเครื่อง local
- ไม่มีค่าใช้จ่าย
- ควบคุม prompt ได้เต็มที่
- ไม่มีปัญหาเรื่อง privacy

---

## การรองรับภาษาไทยและภาษาอังกฤษ

### ความสามารถของระบบ
- รองรับเสียงพูดและ transcript ภาษาไทยและภาษาอังกฤษ ( faster whisper รองรับทั้งสองภาษา )
- รองรับการตอบแบบ implicit (ไม่ต้องพูด label ชัดเจน)

ตัวอย่าง: “My gender is male, I am a male”


---

## ข้อจำกัดของไฟล์เสียง (Input Constraints)

ระบบรองรับเฉพาะไฟล์เสียง **`.wav`** ไฟล์อื่นต้องแปลงเป็น `.wav` ก่อนใช้งาน

### เหตุผล
- ลดปัญหา codec
- ควบคุม sample rate ได้ง่าย
- ลด error ใน STT
- ทำให้ pipeline เสถียร


---

## รูปแบบการรันระบบ

### 1) Pipeline Mode (Single-pass)

ไฟล์หลัก: `pipeline_full.py`

ลักษณะ:
- รับไฟล์เสียง 1 ไฟล์
- ประมวลผลครั้งเดียว
- หากข้อมูลที่ได้ไม่ครบ จะขึ้นแสดงผลว่าขาดข้อมูลส่วนไหนอยู่ แต่ไม่มีการถามกลับ
  
### 2) Interactive Mode (Multi-turn)

ไฟล์หลัก: `interactive_agent.py`

ลักษณะ:
- รันแบบ agent
- ถ้าข้อมูลไม่ครบ จะมีการถามเพิ่มเฉพาะ field ที่ขาด และให้ใส่ไฟล์เสียงเพิ่ม

---

## การจัดการ Uncertainty (ความไม่ชัดเจน)

ระบบจะถามกลับเมื่อ:
- Field ใดไม่มีข้อมูล
- ข้อมูลไม่ผ่าน validation
- STT หรือ LLM ไม่มั่นใจ

ระบบจะไม่มีการเดาเอง เลือกความถูกต้องมาก่อนความเร็ว

---

## กฎการตรวจสอบข้อมูล (Validation)

### เบอร์โทรศัพท์
- ต้องเป็นตัวเลข 10 หลัก
- ไม่มีขีดหรือช่องว่าง

### ชื่อ / นามสกุล
- ต้องไม่เป็นคำบอก label เช่น “ชื่อ”, “นามสกุล”

### ป้ายทะเบียน
- รองรับไทย / อังกฤษ
- แปลงเป็นรูปแบบย่อ (เช่น `กข1234`, `AB1234`)
- รองรับคำอ่านภาษาไทย (เช่น `กอไก่` )

### เพศ
- ชายหรือหญิงเท่านั้น
-----

### การทำ Normalization และ Romanization ในระบบ

ระบบนี้มีการจัดการข้อความหลังจากได้ผลลัพธ์จาก Speech-to-Text และ LLM Extraction เพื่อเพิ่มความถูกต้อง ความสม่ำเสมอ และความพร้อมในการนำข้อมูลไปใช้งานต่อ โดยแบ่งออกเป็น 2 ส่วนหลัก คือ Normalization และ Romanization 

### 1. Text & Field Normalization (ขั้นตอนก่อน Validation)  
เพื่อลดผลกระทบจากความคลาดเคลื่อนของ Speech-to-Text และรูปแบบการพูดของผู้ใช้
ก่อนนำข้อมูลไปตรวจสอบความครบถ้วน (Validation)

1.1) Text Normalization (ระดับข้อความ)  
- ทำทันทีหลังจาก STT
- รวมข้อความจากหลาย segment ให้เป็นประโยคเดียว
- จัดการช่องว่าง (spacing) ให้สม่ำเสมอ
- ลบสัญลักษณ์หรือ token ที่ไม่จำเป็นจาก STT

1.2) Field-level Normalization (หลัง LLM Extraction)

หลังจาก LLM ดึงข้อมูล first name, phone, license plate, gender แล้ว ระบบจะทำ normalization เฉพาะราย field ด้วย rule-based logic

ตัวอย่างที่ทำจริงในระบบ:  

Phone Number
- ลบ - และช่องว่าง
- คงเฉพาะตัวเลข
- ตรวจสอบว่ามีความยาวถูกต้อง (เช่น 9–10 หลัก)
  
License Plate (ทะเบียนรถ)
- รองรับทั้งภาษาไทยและภาษาอังกฤษ
- รองรับหลายรูปแบบ เช่น AB1234, AB 1234, AB-1234, กอไก่ ขอไข่ 1234, กข1234
- แปลงคำอ่านภาษาไทยเป็นตัวอักษรไทยด้วย mapping
- ลบคำฟิลเลอร์ เช่น “ทะเบียนรถ”, “คือ”, “ครับ”

### 2. Rule-based Validation 

หลังจาก normalization แล้ว ระบบจะตรวจสอบความถูกต้องของข้อมูลด้วย rule-based logic เช่น  
- ชื่อ / นามสกุล ต้องไม่เป็น null
- เบอร์โทรศัพท์ต้องเป็นตัวเลขล้วน และมีความยาวถูกต้อง
- ทะเบียนรถต้อง match รูปแบบที่กำหนด

หากข้อมูลใดไม่ผ่าน validation จะถูกจัดเป็น missing_fields
และระบบจะขอให้ผู้ใช้ยืนยันเฉพาะข้อมูลที่ยังขาด (ในโหมด interactive)

### 3. Romanization (ขั้นตอนปลายทาง – Output Stage)  
การแปลงข้อความภาษาไทยเป็นอักษรละติน เช่น สมชาย → somchai ซึ่งจะทำหลังจากข้อมูลผ่านการ Validation แล้ว


---
## โครงสร้าง Repository
├── pipeline_full.py  
├── interactive_agent.py  
├── validator.py  
├── plate_normalizer.py  
├── romanize.py  
├── api_server.py  
└── README.md  
-----

### การใช้งาน 

### 1) โหมด Single-pass: pipeline_full.py  

เหมาะสำหรับการรันครั้งเดียวจบ  

รูปแบบคำสั่ง: ``` python pipeline_full.py <path_to_audio.wav> ```
ตัวอย่าง: ```python pipeline_full.py test_audio/testcase_thai_1.wav```

ผลลัพธ์ที่คาดหวัง:  
- ถ้าข้อมูลครบ → ได้ status: complete และ data ครบ  
- ถ้าข้อมูลไม่ครบ/ไม่ผ่าน validation → ได้ status: incomplete พร้อม missing_fields และ message  

ตัวอย่าง output (complete):
```
{
  "status": "complete",
  "data": {
    "first_name": "Somchai",
    "last_name": "Jai Dee",
    "gender": "male",
    "phone": "0812345678",
    "license_plate": "กข1234"
  }
}
```

ตัวอย่าง output (incomplete):
```
{
  "status": "incomplete",
  "missing_fields": ["license_plate"],
  "message": "ขอรบกวนยืนยันทะเบียนรถอีกครั้ง เนื่องจากระบบอาจได้ยินไม่ชัด"
}
```

### 2) โหมด Interactive (Multi-turn): interactive_agent.py  

เหมาะสำหรับการใช้งานแบบถามกลับอัตโนมัติเมื่อข้อมูลยังไม่ครบ  

รูปแบบคำสั่ง: ``` python interactive_agent.py <path_to_audio.wav> ```  
ตัวอย่าง: ```python interactive_agent.py test_audio/testcase_thai_1.wav```


วิธีใช้งาน  
1. รันโปรแกรม  
2. ใส่ path ไฟล์เสียงรอบแรก เช่น test_audio/testcase_thai_2.1.wav  
3. ถ้าระบบแจ้งว่ายังขาด → อัดเสียงเพิ่มเฉพาะข้อมูลที่ขาด แล้วใส่ path รอบถัดไป  
4. ทำซ้ำจนได้ status: complete  

ตัวอย่างการใช้งาน  
```
- ใส่ path ไฟล์เสียงรอบแรก (เช่น input.wav): test_audio/testcase_thai_2.1.wav
... CURRENT RESULT ...
status: incomplete
missing_fields: ["license_plate"]

พิมพ์ path ไฟล์เสียงรอบถัดไป (หรือพิมพ์ q เพื่อออก): test_audio/testcase_thai_2.2.wav
... FINAL RESULT ...
status: complete
```

### เงื่อนไขไฟล์เสียง  
รองรับ เฉพาะไฟล์ .wav  
ตัวอย่างการแปลง (ถ้ามี ffmpeg):  
```
ffmpeg -i input.m4a -ar 16000 -ac 1 input.wav
```
