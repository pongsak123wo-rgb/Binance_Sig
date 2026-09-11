import os
import sys
import io
import json
import logging
from datetime import datetime, timedelta

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("BinanceScannerCloud")

from config import ALERT_COOLDOWN_MINUTES
from scanner import scan_market
from telegram_bot import send_telegram_message, format_signal_message

CACHE_FILE = "sent_alerts.json"


def load_sent_alerts() -> dict:
    """โหลดประวัติการส่งสัญญาณจากไฟล์ JSON"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"ไม่สามารถโหลดไฟล์ประวัติสัญญาณได้: {e}")
    return {}


def save_sent_alerts(alerts: dict):
    """บันทึกประวัติการส่งสัญญาณลงไฟล์ JSON"""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(alerts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"ไม่สามารถบันทึกไฟล์ประวัติสัญญาณได้: {e}")


def is_in_cooldown(alerts: dict, symbol: str, signal_type: str) -> bool:
    """เช็คว่าเหรียญ + สัญญาณนี้ เคยส่งไปแล้วภายใน 4 ชั่วโมง (240 นาที) หรือไม่"""
    key = f"{symbol}_{signal_type}"
    if key in alerts:
        try:
            last_sent_time = datetime.fromisoformat(alerts[key])
            if datetime.now() - last_sent_time < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                return True
        except Exception:
            pass
    return False


def main():
    logger.info(f"🚀 เริ่มต้นการสแกน Binance Futures บน Cloud (Cooldown {ALERT_COOLDOWN_MINUTES // 60} ชั่วโมง)...")
    time_str = datetime.now().strftime("%H:%M:%S (%d/%m/%Y)")
    
    sent_alerts = load_sent_alerts()
    
    try:
        signals = scan_market()
        if not signals:
            logger.info("✨ สแกนเสร็จสิ้น: ไม่พบเหรียญที่ตรงเงื่อนไขในรอบนี้")
            return
            
        logger.info(f"🔍 พบสัญญาณตรงเงื่อนไขทั้งหมด {len(signals)} เหรียญ ตรวจสอบการซ้ำซ้อนใน 4 ชม....")
        
        sent_count = 0
        for sig in signals:
            symbol = sig['symbol']
            signal_type = sig['signal_type']
            
            # เช็คว่าอยู่ใน Cooldown 4 ชั่วโมงหรือไม่
            if is_in_cooldown(sent_alerts, symbol, signal_type):
                logger.info(f"⏳ เหรียญ {symbol} [{signal_type}] เคยแจ้งเตือนไปแล้วภายใน 4 ชม. (ข้าม)")
                continue
            
            msg = format_signal_message(
                signal_type=signal_type,
                symbol=symbol,
                price=sig['current_price'],
                daily_ema=sig['daily_ema'],
                bb_bw=sig['bb_bandwidth_pct'],
                structure_info=sig['structure_info'],
                timestamp_str=time_str
            )
            
            sent_ok = send_telegram_message(msg)
            if sent_ok or True:
                # บันทึกเวลาที่ส่งล่าสุด
                key = f"{symbol}_{signal_type}"
                sent_alerts[key] = datetime.now().isoformat()
                sent_count += 1
                
        # บันทึกแคชกลับลงไฟล์ JSON
        save_sent_alerts(sent_alerts)
        logger.info(f"✅ ดำเนินการเสร็จสิ้น! ส่งข้อความใหม่ทั้งหมด {sent_count} เหรียญ")
            
    except Exception as e:
        logger.error(f"❌ เกิดข้อผิดพลาดในการสแกน: {e}", exc_info=True)


if __name__ == "__main__":
    main()
