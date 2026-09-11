import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """คำนวณ Exponential Moving Average (EMA)"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_bollinger_bands(
    df: pd.DataFrame, length: int = 20, std_multiplier: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    คำนวณ Bollinger Bands และ Bandwidth
    Returns: (Upper Band, Middle Band, Lower Band, Bandwidth)
    """
    close = df['close']
    middle = close.rolling(window=length).mean()
    std = close.rolling(window=length).std()
    upper = middle + (std_multiplier * std)
    lower = middle - (std_multiplier * std)
    
    # Bandwidth = (Upper - Lower) / Middle
    bandwidth = (upper - lower) / middle
    return upper, middle, lower, bandwidth


def check_bb_squeeze(bandwidth: pd.Series, threshold: float = 0.045, lookback: int = 40) -> Tuple[bool, float]:
    """
    ตรวจสอบว่า Bollinger Bands กำลังบีบตัว (Squeeze) หรือไม่
    เทียบจากค่า Threshold หรือค่า 25th percentile ของ lookback แท่งล่าสุด
    """
    if len(bandwidth) < lookback:
        return False, 0.0
    
    current_bw = bandwidth.iloc[-1]
    quantile_25 = bandwidth.tail(lookback).quantile(0.25)
    
    # บีบตัวเมื่อ Bandwidth น้อยกว่า Threshold หรืออยู่ในระดับ 25% ที่แคบที่สุด
    is_squeezing = current_bw <= threshold or current_bw <= quantile_25
    return is_squeezing, round(float(current_bw * 100), 2)


def check_ema_crossover(ema_short: pd.Series, ema_long: pd.Series) -> str:
    """
    ตรวจสอบการตัดกันของ EMA 9 และ EMA 21 ในแท่งล่าสุด (ย้อนหลัง 2 แท่ง)
    Returns: 'BULLISH', 'BEARISH', หรือ 'NONE'
    """
    if len(ema_short) < 3 or len(ema_long) < 3:
        return 'NONE'
    
    # เช็คแท่งปัจจุบันและแท่งก่อนหน้า
    prev_short = ema_short.iloc[-2]
    prev_long = ema_long.iloc[-2]
    curr_short = ema_short.iloc[-1]
    curr_long = ema_long.iloc[-1]
    
    # เช็คตัดขึ้น (Bullish Cross)
    if prev_short <= prev_long and curr_short > curr_long:
        return 'BULLISH'
    
    # เช็คตัดลง (Bearish Cross)
    if prev_short >= prev_long and curr_short < curr_long:
        return 'BEARISH'
    
    # แถม: กรณีเพิ่งตัดขึ้นในแท่งก่อนหน้า (ย้อนหลัง 3 แท่ง)
    prev2_short = ema_short.iloc[-3]
    prev2_long = ema_long.iloc[-3]
    if prev2_short <= prev2_long and prev_short > prev_long and curr_short > curr_long:
        return 'BULLISH'
    if prev2_short >= prev2_long and prev_short < prev_long and curr_short < curr_long:
        return 'BEARISH'

    return 'NONE'


def detect_market_structure(df: pd.DataFrame, window: int = 2) -> Dict[str, Any]:
    """
    วิเคราะห์โครงสร้างราคาหา Swing High และ Swing Low ย้อนหลัง
    เพื่อเช็คการ ยก Low ยก High (Bullish) หรือ High ต่ำลง Low ต่ำลง (Bearish)
    """
    highs = df['high'].values
    lows = df['low'].values
    n = len(df)
    
    swing_highs = []
    swing_lows = []
    
    for i in range(window, n - window):
        # Local High
        if all(highs[i] > highs[i - j] for j in range(1, window + 1)) and \
           all(highs[i] >= highs[i + j] for j in range(1, window + 1)):
            swing_highs.append((i, highs[i]))
            
        # Local Low
        if all(lows[i] < lows[i - j] for j in range(1, window + 1)) and \
           all(lows[i] <= lows[i + j] for j in range(1, window + 1)):
            swing_lows.append((i, lows[i]))
            
    has_higher_low = False
    has_higher_high = False
    has_lower_high = False
    has_lower_low = False
    
    recent_sh = [h[1] for h in swing_highs[-2:]]
    recent_sl = [l[1] for l in swing_lows[-2:]]
    
    if len(recent_sl) >= 2:
        if recent_sl[-1] > recent_sl[-2]:
            has_higher_low = True
        elif recent_sl[-1] < recent_sl[-2]:
            has_lower_low = True
            
    if len(recent_sh) >= 2:
        if recent_sh[-1] > recent_sh[-2]:
            has_higher_high = True
        elif recent_sh[-1] < recent_sh[-2]:
            has_lower_high = True
            
    return {
        "is_bullish_structure": has_higher_low or (has_higher_low and has_higher_high),
        "is_bearish_structure": has_lower_high or (has_lower_high and has_lower_low),
        "has_higher_low": has_higher_low,
        "has_higher_high": has_higher_high,
        "has_lower_high": has_lower_high,
        "has_lower_low": has_lower_low,
        "recent_swing_lows": recent_sl,
        "recent_swing_highs": recent_sh
    }
