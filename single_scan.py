import sys
import io
import logging
from datetime import datetime

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("BinanceScannerCloud")

from scanner import scan_market
from telegram_bot import send_telegram_message, format_signal_message

def main():
    logger.info("🚀 เริ่มต้นการสแกน Binance Futures บน Cloud...")
    time_str = datetime.now().strftime("%H:%M:%S (%d/%m/%Y)")
    
    try:
        signals = scan_market()
        if not signals:
            logger.info("✨ สแกนเสร็จสิ้น: ไม่พบเหรียญที่ตรงเงื่อนไขในรอบนี้")
            return
            
        logger.info(f"🟢 พบสัญญาณทั้งหมด {len(signals)} เหรียญ กำลังส่งเข้า Telegram...")
        for sig in signals:
            msg = format_signal_message(
                signal_type=sig['signal_type'],
                symbol=sig['symbol'],
                price=sig['current_price'],
                daily_ema=sig['daily_ema'],
                bb_bw=sig['bb_bandwidth_pct'],
                structure_info=sig['structure_info'],
                timestamp_str=time_str
            )
            send_telegram_message(msg)
            
    except Exception as e:
        logger.error(f"❌ เกิดข้อผิดพลาดในการสแกน: {e}", exc_info=True)

if __name__ == "__main__":
    main()
