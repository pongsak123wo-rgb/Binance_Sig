import logging
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from config import (
    BINANCE_FUTURES_BASE_URL,
    EMA_DAILY_PERIOD,
    EMA_SHORT_PERIOD,
    EMA_LONG_PERIOD,
    BB_LENGTH,
    BB_STD,
    BB_SQUEEZE_THRESHOLD,
    MIN_24H_VOLUME_USDT
)
from indicators import (
    calculate_ema,
    calculate_bollinger_bands,
    check_bb_squeeze,
    check_ema_crossover,
    detect_market_structure
)

logger = logging.getLogger(__name__)

# ใช้ Session เพื่อ Reuse SSL Connection เพิ่มความเร็ว
http_session = requests.Session()
http_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})


def fetch_usdt_futures_symbols() -> List[str]:
    """ดึงรายชื่อคู่เทรด USDT-M Futures ที่เปิดให้เทรดและมีวอลุ่มตามที่กำหนด"""
    url = f"{BINANCE_FUTURES_BASE_URL}/fapi/v1/ticker/24hr"
    try:
        resp = http_session.get(url, timeout=10)
        data = resp.json()
        
        valid_symbols = []
        for ticker in data:
            symbol = ticker.get('symbol', '')
            quote_volume = float(ticker.get('quoteVolume', 0))
            
            # กรองเฉพาะคู่เทรด USDT และวอลุ่ม 24h เกินที่ตั้งไว้
            if symbol.endswith("USDT") and quote_volume >= MIN_24H_VOLUME_USDT:
                valid_symbols.append(symbol)
                
        logger.info(f"📊 พบคู่เทรด USDT Futures ที่ผ่านเกณฑ์วอลุ่ม: {len(valid_symbols)} เหรียญ")
        return valid_symbols
    except Exception as e:
        logger.error(f"❌ ดึงรายชื่อคู่เทรด Binance Futures ล้มเหลว: {e}")
        return []


def fetch_klines(symbol: str, interval: str, limit: int = 100) -> Optional[pd.DataFrame]:
    """ดึงข้อมูลแท่งเทียน Klines จาก Binance Futures API"""
    url = f"{BINANCE_FUTURES_BASE_URL}/fapi/v1/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    try:
        resp = http_session.get(url, params=params, timeout=8)
        data = resp.json()
        if not isinstance(data, list) or len(data) < limit // 2:
            return None
        
        cols = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore']
        df = pd.DataFrame(data, columns=cols)
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        return df
    except Exception as e:
        logger.debug(f"ไม่สามารถดึง klines ของ {symbol} ({interval}): {e}")
        return None


def analyze_symbol(symbol: str) -> Optional[Dict[str, Any]]:
    """วิเคราะห์สัญญาณ BUY/SELL ตามเงื่อนไขของเหรียญ 1 เหรียญ"""
    
    # ดึงข้อมูล 1D Klines และ 1H Klines
    df_1d = fetch_klines(symbol, "1d", limit=120)
    df_1h = fetch_klines(symbol, "1h", limit=100)
    
    if df_1d is None or df_1h is None:
        return None
    
    # ----------------------------------------------------
    # เงื่อนไขที่ 1: ตรวจสอบเทรนด์ใหญ่บน 1D (EMA 89 Day)
    # ----------------------------------------------------
    ema_89_1d = calculate_ema(df_1d['close'], EMA_DAILY_PERIOD)
    if len(ema_89_1d) == 0 or pd.isna(ema_89_1d.iloc[-1]):
        return None
    
    current_price = df_1h['close'].iloc[-1]
    daily_ema_val = ema_89_1d.iloc[-1]
    
    is_above_daily_ema = current_price > daily_ema_val
    is_below_daily_ema = current_price < daily_ema_val
    
    # ----------------------------------------------------
    # เงื่อนไขที่ 2: ตรวจสอบการตัดกันของ EMA 9 และ EMA 21 ใน 1H
    # ----------------------------------------------------
    ema_9_1h = calculate_ema(df_1h['close'], EMA_SHORT_PERIOD)
    ema_21_1h = calculate_ema(df_1h['close'], EMA_LONG_PERIOD)
    
    ema_cross_signal = check_ema_crossover(ema_9_1h, ema_21_1h)
    if ema_cross_signal == 'NONE':
        return None  # ถ้าไม่มีการตัดกันของ EMA ข้ามได้เลย
    
    # ----------------------------------------------------
    # เงื่อนไขที่ 3: ตรวจสอบ Bollinger Bands Squeeze ใน 1H
    # ----------------------------------------------------
    _, _, _, bandwidth_1h = calculate_bollinger_bands(df_1h, length=BB_LENGTH, std_multiplier=BB_STD)
    is_bb_squeezing, bw_percentage = check_bb_squeeze(bandwidth_1h, threshold=BB_SQUEEZE_THRESHOLD)
    
    if not is_bb_squeezing:
        return None  # ถ้า Bollinger Bands ไม่บีบตัว ข้ามได้เลย
    
    # ----------------------------------------------------
    # เงื่อนไขที่ 4: ตรวจสอบโครงสร้างราคา (Higher High/Low หรือ Lower High/Low)
    # ----------------------------------------------------
    structure_info = detect_market_structure(df_1h, window=2)
    
    # ----------------------------------------------------
    # สรุปผลการประเมินสัญญาณ
    # ----------------------------------------------------
    signal_type = None
    
    # 🟢 เงื่อนไข BUY (LONG)
    if is_above_daily_ema and ema_cross_signal == 'BULLISH' and structure_info['is_bullish_structure']:
        signal_type = 'LONG'
        
    # 🔴 เงื่อนไข SELL (SHORT)
    elif is_below_daily_ema and ema_cross_signal == 'BEARISH' and structure_info['is_bearish_structure']:
        signal_type = 'SHORT'

    if signal_type:
        return {
            "symbol": symbol,
            "signal_type": signal_type,
            "current_price": current_price,
            "daily_ema": daily_ema_val,
            "bb_bandwidth_pct": bw_percentage,
            "structure_info": structure_info
        }
        
    return None


def scan_market() -> List[Dict[str, Any]]:
    """สแกนตลาด Binance Futures ทั้งหมดด้วย ThreadPoolExecutor เพื่อความรวดเร็วและเสถียร"""
    symbols = fetch_usdt_futures_symbols()
    if not symbols:
        return []
    
    logger.info(f"🔍 กำลังเริ่มสแกนเหรียญ {len(symbols)} เหรียญ...")
    
    # รันพร้อมกันผ่าน 20 Workers ThreadPool
    matched_signals = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(analyze_symbol, symbols)
        for res in results:
            if res is not None:
                matched_signals.append(res)
                
    logger.info(f"✨ สแกนเสร็จสิ้น! พบเหรียญที่ตรงเงื่อนไขทั้งหมด: {len(matched_signals)} เหรียญ")
    return matched_signals
