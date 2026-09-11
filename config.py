import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

# Binance API Configuration (Public Endpoints - ไม่ต้องใช้ API Key)
BINANCE_FUTURES_BASE_URL = "https://fapi.binance.com"

# Telegram Notification Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Technical Indicator Settings
TIMEFRAME_DAILY = "1d"
TIMEFRAME_1H = "1h"

# EMA Periods
EMA_DAILY_PERIOD = 89
EMA_SHORT_PERIOD = 9
EMA_LONG_PERIOD = 21

# Bollinger Bands Settings
BB_LENGTH = 20
BB_STD = 2.0
# BB Bandwidth (< 4% ถือว่าบีบแคบ หรืออยู่ในเกณฑ์ 25% ต่ำสุด)
BB_SQUEEZE_THRESHOLD = 0.045

# Volume Filter (กรองเฉพาะเหรียญที่มี วอลุ่มเทรด 24h มากกว่า 5 ล้าน USDT)
MIN_24H_VOLUME_USDT = 5_000_000

# Scanner Loop Interval (วินาที)
SCAN_INTERVAL_SECONDS = 180  # สแกนทุกๆ 3 นาที

# Cooldown แจ้งเตือนเหรียญเดิม (นาที) เพื่อไม่ให้ยิงเตือนซ้ำๆ
ALERT_COOLDOWN_MINUTES = 60
