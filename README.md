# Binance Futures Crypto Scanner Bot (ภาษาไทย 🇹🇭)

บอทสแกนเหรียญ Binance Futures (USDT-M) อัตโนมัติด้วยกลยุทธ์ Multi-Timeframe แจ้งเตือนเข้า Telegram เป็นภาษาไทย

## 📌 เงื่อนไขการสแกนสัญญาณ

### 🟢 ขาขึ้น (BUY / LONG Signal)
1. **เทรนด์ใหญ่ (1D):** ราคาปัจจุบัน **อยู่เหนือ EMA 89 Day**
2. **สัญญาณเปลี่ยนเทรนด์ (1H):** **EMA 9 ตัดขึ้น EMA 21**
3. **การบีบอัดพลัง (1H):** **Bollinger Bands บีบตัวแน่น (BB Squeeze)**
4. **โครงสร้างราคา (1H):** ราคาทำทรง **ยก Low สูงขึ้น (Higher Low)** หรือ **ยก High สูงขึ้น (Higher High)** เตรียม Breakout

### 🔴 ขาลง (SELL / SHORT Signal)
1. **เทรนด์ใหญ่ (1D):** ราคาปัจจุบัน **อยู่ใต้ EMA 89 Day**
2. **สัญญาณเปลี่ยนเทรนด์ (1H):** **EMA 9 ตัดลง EMA 21**
3. **การบีบอัดพลัง (1H):** **Bollinger Bands บีบตัวแน่น (BB Squeeze)**
4. **โครงสร้างราคา (1H):** ราคาทำทรง **High ต่ำลง (Lower High)** หรือ **Low ต่ำลง (Lower Low)** เตรียม Breakdown

---

## 🛠 วิธีติดตั้งและใช้งาน

### 1. ติดตั้ง Dependencies
เปิด Terminal ในโฟลเดอร์โปรเจกต์ แล้วพิมพ์:
```bash
pip install -r requirements.txt
```

### 2. วิธีเอา Telegram Bot Token และ Chat ID (ฟรี 100%)
1. **สร้างบอท:** เข้าแอป Telegram ค้นหา `@BotFather` กดเริ่มคัดแล้วพิมพ์ `/newbot` ตั้งชื่อบอท จะได้ **HTTP API Token** (นำมาใส่ใน `TELEGRAM_BOT_TOKEN`)
2. **หา Chat ID:** ค้นหา `@userinfobot` ใน Telegram กดเริ่มคัด บอทจะตอบกลับ **Id** ของคุณ (นำมาใส่ใน `TELEGRAM_CHAT_ID`)
3. **เริ่มแชทกับบอทของคุณ:** ค้นหาชื่อบอทที่คุณเพิ่งสร้างแล้วกด **Start** (เปิดแชททิ้งไว้เพื่อให้บอทส่งข้อความหาคุณได้)

### 3. ใส่ค่าในไฟล์ `.env`
เปิดไฟล์ `.env` แล้วใส่ Token และ Chat ID:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=987654321
```

### 4. รันบอทสแกน
```bash
python main.py
```

*(หมายเหตุ: หากยังไม่ได้ใส่ Telegram Token บอทจะพิมพ์ข้อความแจ้งเตือนสีสันสวยงามลงในหน้าจอ Terminal ให้คุณเห็นผลลัพธ์ทันที)*
