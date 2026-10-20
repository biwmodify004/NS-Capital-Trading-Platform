# NS Capital Trading Platform V3 — คู่มือภาษาไทย

## สถานะที่ทำงานได้
- React Dashboard 6 หน้า พร้อมข้อมูลสาธิต; Google Sign-In ผ่าน Google Identity Services (ID token)
- FastAPI ตรวจ Google ID token ฝั่งเซิร์ฟเวอร์และตรวจ allowlist อีเมล
- MT5 Windows bridge อ่านบัญชี, OHLC, ประวัติดีล เมื่อเปิด `MT5_ENABLED=true`
- SQLAlchemy บันทึกข้อเสนอ AI (signals) และ audit log ใน SQLite หรือ PostgreSQL
- Risk Engine: SL/TP, lot step, risk/trade, daily realized + floating, exposure, broker pre-check
- Kill switch บล็อกคำสั่งใหม่ (ไม่ปิด position เดิม)

**ข้อจำกัดสำคัญ:** ระบบ AI อัตโนมัติยังไม่ส่งคำสั่งจริง: `/api/v3/signals/{id}/execute` คืน HTTP 501 โดยตั้งใจ จนกว่าจะมี execution worker ที่ผ่านการทดสอบเรื่อง idempotency, การรีสตาร์ต, partial fill, broker fill mode และการตรวจสอบความเสี่ยงแบบอะตอมมิก ห้ามนำไปอ้างว่าเป็นระบบเทรดเงินจริงที่พร้อมใช้

## ติดตั้ง
1. Windows 10/11 หรือ Windows Server VPS, MT5 Terminal ติดตั้งและล็อกอินบัญชี Demo
2. ติดตั้ง Node.js 20+ และ Python 3.11+; เปิด Terminal ที่โฟลเดอร์หลัก
3. `npm install` แล้ว `npm run dev` (เว็บ http://localhost:5173)
4. `cd backend`; `python -m venv .venv`; Windows: `.venv\Scripts\activate`; `pip install -r requirements.txt`
5. คัดลอก `backend/.env.example` เป็น `backend/.env` และ `.env.example` เป็น `.env` ในโฟลเดอร์หลัก
6. สร้าง Google OAuth Client ID ประเภท Web application ใน Google Cloud Console, ใส่ Authorized JavaScript origins: `http://localhost:5173` และใส่ Client ID เดียวกันทั้งสอง .env; ตั้ง ALLOWED_EMAILS เป็นอีเมลผู้ดูแลจริง
7. เปิด Backend **จากโฟลเดอร์หลัก**: `uvicorn backend.main:app --host 127.0.0.1 --port 8000` (หากใช้ `.env` ใน backend ให้รันจาก backend ด้วย `uvicorn main:app` จะใช้ไม่ได้เพราะ relative import; แนะนำตั้ง env ผ่าน root หรือใช้ `uvicorn backend.main:app --env-file backend/.env`)
8. สำหรับอ่าน MT5 ให้ตั้ง `MT5_ENABLED=true`, ตั้ง terminal path และตรวจ `/api/health` แล้วล็อกอิน Google บนเว็บ
9. สำหรับ PostgreSQL สร้าง database แล้วตั้ง `DATABASE_URL=postgresql+psycopg://...` ก่อนเปิด API (ตารางสร้างโดย SQLAlchemy)

## Local + VPS
- ติดตั้ง Backend และ MT5 บน **Windows host แต่ละเครื่อง**; Frontend ติดต่อกับ Backend ที่เลือกผ่าน `VITE_API_BASE`
- ไม่แชร์บัญชี MT5 ระหว่าง host ที่ส่งคำสั่งพร้อมกัน; เลือก active bridge เพียงตัวเดียว
- Production ต้องใช้ HTTPS ผ่าน reverse proxy / private network; อย่าเปิด port MT5/8000 สู่สาธารณะโดยตรง
- ใช้ process เดียวสำหรับ order execution; Kill switch แบบ in-memory จะกลับไปล็อกทุกครั้งเมื่อรีสตาร์ต (fail closed)
- Google ID token เป็น token อายุสั้น: เวอร์ชันนี้ยังไม่มีระบบ refresh/session production

## AI Trading
- POST `/api/v3/signals` เพื่อบันทึกสัญญาณที่ผ่าน schema; `confidence` เป็นค่าที่ผู้ส่งกำหนด **ไม่ใช่ผลโมเดลที่เทรนแล้ว**
- GET `/api/v3/signals` ดูประวัติข้อเสนอ; POST `/api/v3/orders/preview` คำนวณ risk จาก MT5
- เปิด AI_EXECUTION_ENABLED และ TRADING_ENABLED อย่างเดียว **ไม่ทำให้ส่งคำสั่งจริง**: ระบบ fail closed ตามข้อจำกัดด้านบน
- ต้องพัฒนา model inference + validation + backtesting/walk-forward + live demo shadow mode และ independent risk checks ก่อน production

## ความปลอดภัย
อย่าใส่รหัส MT5, Google Client Secret หรือ DATABASE_URL ใน Frontend/GitHub; อย่าปิด kill switch ในบัญชีเงินจริงก่อนผ่านการทดสอบ Demo และการตรวจสอบการทำงานของระบบ
