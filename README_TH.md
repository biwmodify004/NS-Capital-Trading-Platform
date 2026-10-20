# NS Capital MT5 Connector — คู่มือภาษาไทย

## สถานะ
เชื่อมข้อมูลจริงแบบ **อ่านอย่างเดียว**: Health, Balance, Equity, Margin, OHLC, Positions ผ่าน MT5 Python API บน Windows. ไม่มีการส่งคำสั่ง BUY/SELL ไปยัง Broker. ปุ่ม Paper Trading เดิมยังเป็นข้อมูลจำลอง.

## ติดตั้งบน Windows ที่เปิด MT5
1. ติดตั้ง Python 3.11+ และ MetaTrader 5 Terminal (ล็อกอิน Demo ก่อน)
2. เปิด PowerShell ในโฟลเดอร์โปรเจกต์
3. `py -m venv .venv`
4. `.venv\\Scripts\\activate`
5. `pip install -r backend/requirements.txt`
6. สร้างค่า API Key แบบสุ่ม เช่น `python -c "import secrets;print(secrets.token_urlsafe(36))"`
7. ตั้งค่าตัวแปรสภาพแวดล้อมใน PowerShell: `$env:BRIDGE_API_KEY='คีย์ที่สร้าง'` และ `$env:ALLOWED_ORIGINS='http://127.0.0.1:5500'`
8. รัน `uvicorn backend.server:app --host 127.0.0.1 --port 8000`
9. เปิด PowerShell อีกหน้าต่างแล้วรัน `python -m http.server 5500 --bind 127.0.0.1` จากโฟลเดอร์โปรเจกต์
10. เปิด `http://127.0.0.1:5500` และใส่ Bridge URL `http://127.0.0.1:8000` กับ API Key ในกล่อง MT5 Connector แล้วกดเชื่อมต่อ

> หมายเหตุ: ให้รันจากโฟลเดอร์หลักที่มี `backend/` และ `index.html`. ถ้าใช้เครื่องหลาย MT5 terminals ให้กำหนด `MT5_TERMINAL_PATH` เป็นพาธของ terminal64.exe และรัน Bridge แยก process/port สำหรับแต่ละ terminal.

## Local/VPS / GitHub Pages
หน้าเว็บที่เผยแพร่ผ่าน HTTPS (GitHub Pages) **ไม่สามารถเรียก HTTP localhost บน VPS โดยตรงได้**. ให้ติดตั้ง Bridge บน VPS Windows และวาง HTTPS reverse proxy ที่มี TLS, การตรวจสอบตัวตน และการจำกัด IP หรือเชื่อมผ่าน VPN/Tailscale แล้วใช้ Frontend ที่โฮสต์ในเครือข่ายที่เข้าถึง Bridge ได้. อย่าเปิดพอร์ต 8000 สู่สาธารณะหรือเก็บ API Key ใน GitHub. ควรใช้ Backend กลางพร้อม OAuth/Session, แทนการใส่คีย์ Bridge ในเว็บสาธารณะ.

## ข้อจำกัดสำคัญ
- ปุ่ม Buy/Sell ยังทำ Paper Trading ไม่ใช่ Live Execution.
- ข้อมูล Account/Equity ที่อ่านได้จะอัปเดตบน Dashboard หลังเชื่อมต่อ; OHLC และ Positions มี API พร้อมให้ Frontend รุ่นถัดไปดึง แต่กราฟเดิมยังเป็นกราฟจำลอง.
- ไม่มีการยืนยันการทำงานกับ MT5 จริงในสภาพแวดล้อมนี้ ต้องทดสอบบน Windows ของคุณ.
- ห้ามใส่รหัสผ่าน MT5 ในหน้าเว็บหรือส่งให้ผู้อื่น.
