import sys
import io
import time
import logging
from datetime import datetime, timedelta

# ป้องกัน UnicodeEncodeError บน Windows Console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config import (
    SCAN_INTERVAL_SECONDS,
    ALERT_COOLDOWN_MINUTES
)
from scanner import scan_market
from telegram_bot import send_telegram_message, format_signal_message

# ตั้งค่า Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("BinanceScannerBot")

# ระบบ Cooldown ป้องกันยิงเตือนเหรียญเดิมซ้ำซ้อน {symbol_signal: datetime}
alert_cooldowns = {}


def is_in_cooldown(symbol: str, signal_type: str) -> bool:
    key = f"{symbol}_{signal_type}"
    now = datetime.now()
    if key in alert_cooldowns:
        last_alert_time = alert_cooldowns[key]
        if now - last_alert_time < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
            return True
    return False


def set_cooldown(symbol: str, signal_type: str):
    key = f"{symbol}_{signal_type}"
    alert_cooldowns[key] = datetime.now()


def run_bot_loop():
    logger.info("🚀 เริ่มต้นระบบบอทสแกนคริปโต Binance Futures (USDT-M)")
    logger.info(f"⏱ รอบการสแกนทุกๆ {SCAN_INTERVAL_SECONDS} วินาที | Cooldown แจ้งเตือน: {ALERT_COOLDOWN_MINUTES} นาที")
    
    while True:
        scan_start_time = datetime.now()
        time_str = scan_start_time.strftime("%H:%M:%S (%d/%m/%Y)")
        logger.info(f"🔄 เริ่มรอบสแกนเวลา: {time_str}")
        
        try:
            signals = scan_market()
            
            for sig in signals:
                symbol = sig['symbol']
                signal_type = sig['signal_type']
                
                if is_in_cooldown(symbol, signal_type):
                    logger.info(f"⏳ เหรียญ {symbol} [{signal_type}] อยู่ในระยะ Cooldown (ข้ามการแจ้งเตือน)")
                    continue
                
                # จัดรูปแบบข้อความแจ้งเตือนภาษาไทย
                message_text = format_signal_message(
                    signal_type=signal_type,
                    symbol=symbol,
                    price=sig['current_price'],
                    daily_ema=sig['daily_ema'],
                    bb_bw=sig['bb_bandwidth_pct'],
                    structure_info=sig['structure_info'],
                    timestamp_str=time_str
                )
                
                # ส่งข้อความเข้า Telegram
                sent_ok = send_telegram_message(message_text)
                if sent_ok or True:
                    set_cooldown(symbol, signal_type)

        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในรอบการสแกน: {e}", exc_info=True)

        # คำนวณเวลารอสำหรับรอบถัดไป
        elapsed = (datetime.now() - scan_start_time).total_seconds()
        sleep_time = max(1, SCAN_INTERVAL_SECONDS - elapsed)
        logger.info(f"😴 พักรอรอบถัดไปอีก {int(sleep_time)} วินาที...\n")
        time.sleep(sleep_time)


def main():
    try:
        run_bot_loop()
    except KeyboardInterrupt:
        logger.info("\n🛑 ปิดการทำงานของบอทเรียบร้อยแล้ว")


if __name__ == "__main__":
    main()
