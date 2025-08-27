import yfinance as yf
import datetime
import pytz
from num2words import num2words


# --- עזר: המרת מספרים למילים בעברית ---
def number_to_hebrew_words(number):
    """ממיר מספר למילים בעברית, כולל חלק עשרוני פשוט כדיבור נקודה."""
    if number is None:
        return "לא זמין"
    # עיגול לשתי ספרות עשרוניות כדי למנוע זנבות חישוב
    s = f"{float(number):.2f}"
    parts = s.split(".")
    integer_part = int(parts[0])
    frac_part = int(parts[1])
    if frac_part == 0:
        return num2words(integer_part, lang="he")
    return f"{num2words(integer_part, lang='he')} נקודה {num2words(frac_part, lang='he')}"


# --- חלוקת היום ---
def get_time_segment(now):
    h = now.hour
    if 6 <= h < 12:
        return "בבוקר"
    elif 12 <= h < 18:
        return "בצהריים"
    elif 18 <= h < 23:
        return "בערב"
    else:
        return "בלילה"


# --- ניסוח שעה לדיבור: שתים וארבעים דקות, אחת בדיוק ---
def format_time_hebrew(now):
    hour = now.hour
    minute = now.minute
    # שעון שתים עשרה
    if hour == 0:
        hour = 12
    elif hour > 12:
        hour -= 12
    hour_word = number_to_hebrew_words(hour)
    if minute == 0:
        return f"{hour_word} בדיוק"
    minute_word = number_to_hebrew_words(minute)
    return f"{hour_word} ו{minute_word} דקות"


# --- שליפת שינוי יומי ומגמת שלשת הימים האחרונים ---
def get_stock_change(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d", interval="1d")
        if len(hist) < 3:
            return None, None, None
        current = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])
        before_prev = float(hist["Close"].iloc[-3])
        pct = ((current - prev) / prev) * 100.0
        trend = None
        if current > prev > before_prev:
            trend = "ממשיכה לעלות"
        elif current < prev < before_prev:
            trend = "ממשיכה לרדת"
        return round(pct, 2), round(current, 2), trend
    except Exception:
        return None, None, None


# --- ניסוח כיוון תנועה, עם סף דרמטי ואפשרות לנקבה ---
def format_direction(pct, trend, threshold=1.5, is_female=False):
    if pct is None:
        return "לא זמין"
    if trend:
        base = trend  # כבר בנקבה
    else:
        if abs(pct) >= threshold:
            base = "עולה בצורה דרמטית" if pct > 0 else "יורדת בצורה דרמטית"
        else:
            base = "עולה" if pct > 0 else "יורדת"
        if not is_female:
            # למדדים נעדיף זכר
            base = base.replace("עולה", "עולה").replace("יורדת", "יורד")
    return base


# --- בניית טקסט תמונת שוק ---
def get_market_report():
    # שמות קריאים לדיבור, ללא סמלים
    tickers = {
        "מדד תל אביב מאה עשרים וחמש": "^TA125.TA",
        "מדד תל אביב שלושים וחמש": "TA35.TA",

        # תעודות סל למדדים אמריקאיים
        "אס אנד פי חמש מאות תעודת סל": "SPY",
        "נאסדק תעודת סל": "QQQ",
        "דאו גונס תעודת סל": "DIA",
        "ראסל תעודת סל": "IWM",

        # מטבעות דיגיטליים וסחורות
        "ביטקוין": "BTC-USD",
        "אתריום": "ETH-USD",
        "זהב": "GC=F",
        "נפט": "CL=F",
        "דולר": "USDILS=X",

        # מניות
        "אפל": "AAPL",
        "אנבידיה": "NVDA",
        "אמזון": "AMZN",
        "טסלה": "TSLA",
    }

    now = datetime.datetime.now(pytz.timezone("Asia/Jerusalem"))
    hour_str = format_time_hebrew(now)
    segment = get_time_segment(now)

    # פתיח נקי לסינתזה
    report_lines = []
    report_lines.append(f"הנה תמונת השוק נכונה לשעה {hour_str} {segment}.")

    # שליפת נתונים
    results = {}
    for name, t in tickers.items():
        pct, price, trend = get_stock_change(t)
        results[name] = {"pct": pct, "price": price, "trend": trend}

    # ישראל
    open_time_il = now.replace(hour=9, minute=59, second=0, microsecond=0)
    close_time_il = now.replace(hour=17, minute=25, second=0, microsecond=0)
    ta125 = results["מדד תל אביב מאה עשרים וחמש"]
    ta35 = results["מדד תל אביב שלושים וחמש"]

    report_lines.append("")
    report_lines.append("בישראל.")

    if now < open_time_il:
        delta = open_time_il - now
        hours = int(delta.total_seconds()) // 3600
        minutes = (int(delta.total_seconds()) % 3600) // 60
        report_lines.append(
            f"בורסה תל אביב טרם נפתחה, צפויה להיפתח בעוד {number_to_hebrew_words(hours)} שעות ו{number_to_hebrew_words(minutes)} דקות."
        )
    elif now > close_time_il:
        verb1 = "עלה" if (ta125["pct"] or 0) > 0 else "ירד"
        verb2 = "עלה" if (ta35["pct"] or 0) > 0 else "ירד"
        report_lines.append(
            f"הבורסה נסגרה. מדד תל אביב מאה עשרים וחמש {verb1} ב{number_to_hebrew_words(abs(ta125['pct']))} אחוז וננעל ברמה של {number_to_hebrew_words(ta125['price'])} נקודות."
        )
        report_lines.append(
            f"מדד תל אביב שלושים וחמש {verb2} ב{number_to_hebrew_words(abs(ta35['pct']))} אחוז וננעל ברמה של {number_to_hebrew_words(ta35['price'])} נקודות."
        )
    else:
        for name in ["מדד תל אביב מאה עשרים וחמש", "מדד תל אביב שלושים וחמש"]:
            d = results[name]
            direction = format_direction(d["pct"], d["trend"], is_female=False)
            report_lines.append(
                f"{name} {direction} ב{number_to_hebrew_words(abs(d['pct']))} אחוז ועומד על {number_to_hebrew_words(d['price'])} נקודות."
            )

    # מדדים עולמיים
    ny_open = now.replace(hour=16, minute=30, second=0, microsecond=0)
    ny_close = now.replace(hour=23, minute=0, second=0, microsecond=0)

    # תעודות סל תמיד זמינות לפרה או לאחר
    etf_indices = {
        "אס אנד פי חמש מאות": results["אס אנד פי חמש מאות תעודת סל"],
        "נאסדק": results["נאסדק תעודת סל"],
        "דאו גונס": results["דאו גונס תעודת סל"],
        "ראסל": results["ראסל תעודת סל"],
    }

    # אם מסחר פתוח נשלוף גם מדדי אם חיים
    live_indices = {}
    if ny_open <= now <= ny_close:
        live_map = {
            "אס אנד פי חמש מאות": "^GSPC",
            "נאסדק": "^IXIC",
            "דאו גונס": "^DJI",
            "ראסל": "^RUT",
        }
        for name, t in live_map.items():
            pct, price, trend = get_stock_change(t)
            live_indices[name] = {"pct": pct, "price": price, "trend": trend}

    report_lines.append("")
    report_lines.append("בבורסות העולם.")

    if now < ny_open or now > ny_close:
        report_lines.append("הנתונים מתייחסים למסחר המוקדם או למסחר המאוחר.")
        for name, d in etf_indices.items():
            direction = "עלה" if (d["pct"] or 0) > 0 else "ירד"
            report_lines.append(
                f"{name} {direction} ב{number_to_hebrew_words(abs(d['pct']))} אחוז."
            )
    else:
        for name in ["אס אנד פי חמש מאות", "נאסדק", "דאו גונס", "ראסל"]:
            d = live_indices.get(name, {"pct": None, "price": None, "trend": None})
            direction = format_direction(d["pct"], d["trend"], is_female=False)
            report_lines.append(
                f"{name} {direction} ב{number_to_hebrew_words(abs(d['pct']))} אחוז ועומד על {number_to_hebrew_words(d['price'])} נקודות."
            )

    # מניות אמריקאיות מרכזיות, פעלים בנקבה
    report_lines.append("")
    report_lines.append("בשוק המניות.")
    for stock_name in ["אפל", "אנבידיה", "אמזון", "טסלה"]:
        d = results[stock_name]
        direction = format_direction(d["pct"], d["trend"], threshold=5, is_female=True)
        report_lines.append(
            f"מניית {stock_name} {direction} ב{number_to_hebrew_words(abs(d['pct']))} אחוז ונסחרת בשער של {number_to_hebrew_words(d['price'])} דולר."
        )

    # קריפטו
    report_lines.append("")
    report_lines.append("בגזרת הקריפטו.")
    for name in ["ביטקוין", "אתריום"]:
        d = results[name]
        # אתריום נקבה, ביטקוין זכר. נשתמש בכללי ברירת מחדל זכר ונעדכן לאתריום ידנית.
        is_female = (name == "אתריום")
        direction = format_direction(d["pct"], d["trend"], is_female=is_female)
        report_lines.append(
            f"{name} {direction} ב{number_to_hebrew_words(abs(d['pct']))} אחוז ונסחר בשער של {number_to_hebrew_words(d['price'])} דולר."
            if not is_female else
            f"{name} {direction} ב{number_to_hebrew_words(abs(d['pct']))} אחוז ונסחרת בשער של {number_to_hebrew_words(d['price'])} דולר."
        )

    # סחורות ומטבע
    report_lines.append("")
    report_lines.append("עוד בעולם.")
    extras = [("זהב", "לאונקיה"), ("נפט", "לחבית"), ("דולר", "שקלים")]
    for name, unit in extras:
        d = results[name]
        direction = format_direction(d["pct"], d["trend"], is_female=False)
        report_lines.append(
            f"{name} {direction} ונמצא על {number_to_hebrew_words(d['price'])} {unit}."
        )

    # חיבור טקסט סופי עם ירידות שורה. אין נקודתיים או סמלים אחרים מלבד פסיקים ונקודות.
    return "\n".join(report_lines)


def generate_market_text():
    return get_market_report()
