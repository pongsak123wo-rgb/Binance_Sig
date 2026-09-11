import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

def send_telegram_message(text: str) -> bool:
    """ส่งข้อความเข้า Telegram ผ่าน Telegram Bot API"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ ไม่ได้ตั้งค่า TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID (จะพิมพ์ลง Console แทน)")
        print("\n--- [TELEGRAM PREVIEW] ---")
        print(text)
        print("--------------------------\n")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        res_json = response.json()
        if res_json.get("ok"):
            logger.info("✅ ส่งการแจ้งเตือนเข้า Telegram เรียบร้อยแล้ว")
            return True
        else:
            logger.error(f"❌ Telegram API Error: {res_json}")
            return False
    except Exception as e:
        logger.error(f"❌ เกิดข้อผิดพลาดในการส่ง Telegram: {e}")
        return False


def format_signal_message(signal_type: str, symbol: str, price: float, daily_ema: float, bb_bw: float, structure_info: dict, timestamp_str: str) -> str:
    """จัดรูปแบบข้อความแจ้งเตือนภาษาไทยเข้า Telegram"""
    
    clean_symbol = symbol.replace("USDT", "/USDT")
    price_fmt = f"{price:,.4f}" if price < 1 else f"{price:,.2f}"
    daily_ema_fmt = f"{daily_ema:,.4f}" if daily_ema < 1 else f"{daily_ema:,.2f}"
    
    if signal_type == "LONG":
        header = f"🟢 **[ สัญญาณซื้อ / BUY LONG ]** `#{symbol}`"
        trend_msg = f"📈 **เทรนด์ 1D:** ราคา ({price_fmt}) **อยู่เหนือ EMA 89** ({daily_ema_fmt})"
        cross_msg = "⚡ **สัญญาณ 1H:** EMA 9 ตัดขึ้น EMA 21"
        bb_msg = f"📦 **สถานะ BB 1H:** บีบตัวแน่น (Bandwidth: {bb_bw}%)"
        
        struct_details = []
        if structure_info.get("has_higher_low"):
            struct_details.append("ยก Low สูงขึ้น")
        if structure_info.get("has_higher_high"):
            struct_details.append("ยก High สูงขึ้น")
        struct_str = " & ".join(struct_details) if struct_details else "กำลังสร้างฐาน Sideway ยกตัว"
        
        struct_msg = f"📐 **โครงสร้างราคา:** {struct_str} (เตรียม Breakout!)"
        action_msg = "💡 **คำแนะนำ:** พิจารณาเปิดสถานะ LONG หรือรอราคาย่อแล้วกด"

    else:
        header = f"🔴 **[ สัญญาณขาย / SELL SHORT ]** `#{symbol}`"
        trend_msg = f"📉 **เทรนด์ 1D:** ราคา ({price_fmt}) **อยู่ใต้ EMA 89** ({daily_ema_fmt})"
        cross_msg = "⚡ **สัญญาณ 1H:** EMA 9 ตัดลง EMA 21"
        bb_msg = f"📦 **สถานะ BB 1H:** บีบตัวแน่น (Bandwidth: {bb_bw}%)"
        
        struct_details = []
        if structure_info.get("has_lower_high"):
            struct_details.append("High ต่ำลง")
        if structure_info.get("has_lower_low"):
            struct_details.append("Low ต่ำลง")
        struct_str = " & ".join(struct_details) if struct_details else "กำลังสร้างฐาน Sideway ปรับตัวลง"
        
        struct_msg = f"📐 **โครงสร้างราคา:** {struct_str} (เตรียม Breakdown!)"
        action_msg = "💡 **คำแนะนำ:** พิจารณาเปิดสถานะ SHORT หรือรอรีบาวด์แล้วกด"

    message = (
        f"{header}\n\n"
        f"🪙 **คู่เทรด:** {clean_symbol}\n"
        f"💵 **ราคาปัจจุบัน:** {price_fmt} USDT\n"
        f"{trend_msg}\n"
        f"{cross_msg}\n"
        f"{bb_msg}\n"
        f"{struct_msg}\n\n"
        f"{action_msg}\n"
        f"⏱ **เวลาสแกน:** {timestamp_str}"
    )
    return message
