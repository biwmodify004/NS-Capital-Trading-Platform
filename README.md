# NS Capital Trading Platform — UI Demo

เว็บต้นแบบ React + Vite จากภาพอ้างอิง (ไม่ใช่ซอร์สโค้ดของ KuyTrade)

## เริ่มต้น

```bash
npm install
npm run dev
```

เปิด URL ที่ Vite แสดง (โดยทั่วไป http://localhost:5173)

## ฟีเจอร์
- ภาพรวมพร้อม KPI, balance curve และกราฟ P/L
- เทรด: กราฟราคา **จำลองแบบเส้น** พร้อม EMA, ฟอร์ม Buy/Sell และ SL/TP (ไม่ส่งคำสั่งจริง)
- บันทึกเทรด: ตาราง, ตัวกรอง symbol/side, ส่งออก CSV
- วิเคราะห์: Win Rate, Profit Factor, Expectancy, ผลตามกลยุทธ์
- กลยุทธ์ AI: สวิตช์เปิดปิดในหน้า UI (ยังไม่มี AI engine)
- ตั้งค่า: ฟอร์มตัวอย่าง (ยังไม่ persist)

**ข้อจำกัด:** ทุกข้อมูลเป็นตัวอย่าง ไม่มี MT4/MT5, Broker API, backend, login, database, live market feed หรือระบบ risk enforcement จริง ตัวกรองช่วงเวลาเป็น UI placeholder และยังไม่กรองตามวันที่

## การต่อยอด production
1. Backend (FastAPI/Node), PostgreSQL, Auth (Google OAuth)
2. MT5 bridge บน Windows VPS ที่รัน MT5 Terminal + Python MetaTrader5 หรือ MQL5 EA ที่เชื่อม API อย่างปลอดภัย
3. REST/WebSocket สำหรับ account, positions, OHLC, history, order state
4. Server-side Risk Engine ตรวจ SL, lot, max exposure, daily loss และ kill switch ก่อนส่งคำสั่ง
5. Audit log, secrets management, HTTPS, RBAC, reconciliation และการทดสอบบน demo account
6. กราฟแท่งเทียนจริงด้วย lightweight-charts + ข้อมูล OHLC จาก MT5

## New: MT5 / Google authentication backend scaffold
See `backend/README.md` and `backend/.env.example`. Provides token-verified, allowlisted MT5 account, OHLC, trade-history and order-risk-preview endpoints. **Frontend remains demo-only until wired to backend.** Live orders deliberately fail closed; AI model and OAuth UI are not yet implemented. Never commit `.env`.
