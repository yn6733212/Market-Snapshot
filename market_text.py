import yfinance as yf
import datetime
import pytz
from num2words import num2words
import pandas as pd

# * המרת מספרים למילים בעברית
def number_to_hebrew_words(number):
    rounded_number = round(number, 2)
    parts = str(rounded_number).split(".")
    integer_part = int(parts[0])
    if len(parts) > 1 and int(parts[1]) > 0:
        decimal_part = int(parts[1])
        integer_words = num2words(integer_part, lang='he')
        decimal_words = num2words(decimal_part, lang='he')
        if integer_part == 0:
            return f"אֵפֶס נְקוּדָה {decimal_words}"
        return f"{integer_words} נְקוּדָה {decimal_words}"
    else:
        return num2words(integer_part, lang='he')

# * פלח זמן (בוקר/צהריים/ערב/לילה)
def get_time_segment(now):
    hour = now.hour
    if 6 <= hour < 12:
        return "בָּבּוֹקֵר"
    elif 12 <= hour < 18:
        return "בָּצֹהֹרָיִים"
    elif 18 <= hour < 23:
        return "בָּעֵרֵב"
    else:
        return "בָּלָיְלָה"

# * שינוי/רמה/טרנד לטיקר (אחוז, מחיר, טרנד)
def get_stock_change(ticker):
    stock = yf.Ticker(ticker)
    try:
        hist = stock.history(period="10d", interval="1d")
    except Exception:
        return None, None, None
    if hist is None or hist.empty or "Close" not in hist.columns:
        return None, None, None
    hist = hist.dropna(subset=["Close"])

    # * צריך לפחות 2 נרות
    if len(hist) < 2:
        if len(hist) == 1:
            price_only = float(hist["Close"].iloc[-1])
            return None, round(price_only, 2), None
        return None, None, None

    # * המרת אזור זמן לישראל (חסין)
    jerusalem = pytz.timezone("Asia/Jerusalem")
    ts = hist.index[-1]
    try:
        if getattr(ts, "tzinfo", None) is not None:
            last_data_time = ts.tz_convert(jerusalem) if hasattr(ts, "tz_convert") else ts.astimezone(jerusalem)
        else:
            ts_utc = pytz.utc.localize(ts)
            last_data_time = ts_utc.astimezone(jerusalem)
    except Exception:
        last_data_time = None

    current = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2])
    pct = ((current - prev) / prev) * 100 if prev != 0 else 0.0

    # * טרנד רק עם 3+ נרות
    trend = None
    if len(hist) >= 3:
        before_prev = float(hist["Close"].iloc[-3])
        if current > prev > before_prev:
            trend = "מַמְשִׁיךְ לַעֲלוֹת"
        elif current < prev < before_prev:
            trend = "מַמְשִׁיךְ לְרֶדֶת"

    return round(pct, 2), round(current, 2), trend

# * ניסוח כיוון: זכר/נקבה, סף דרמטי
def format_direction(pct, trend, threshold=1.5, is_female=False):
    if pct is None:
        return "לֹא זָמִין"
    if trend:
        base = trend
    else:
        if abs(pct) >= threshold:
            base = "עוֹלֶה בֵּצוּרָה דְרָמָטִית" if pct > 0 else "יוֹרֵד בְּצוּרָה דְרָמָטִית"
        else:
            base = "עוֹלֶה" if pct > 0 else "יוֹרֵד"
    if is_female:
        base = base.replace("עוֹלֶה", "עוֹלָה").replace("יוֹרֵד", "יוֹרֶדֶת").replace("מַמְשִׁיךְ", "מַמְשִׁיכָה")
    return base

# * דוח תמונת שוק
def get_market_report():
    # * טיקרים: ישראל/קריפטו/סחורות/דולר
    tickers = {
        "תֵל אָבִיב מֵאָה עֵשְׂרִים וֵחָמֵש": "^TA125.TA",
        "תֵל אָבִיב שְׁלוֹשִׁים וֵחָמֵש": "TA35.TA",
        "הָבִּיטְקוֹיְן": "BTC-USD",
        "הָאִיתֵרְיוּם": "ETH-USD",
        "הָזָהָב": "GC=F",
        "הָנֵפְט": "CL=F",
        "הָדוֹלָר": "USDILS=X"
    }

    # * מדדי מקור בארה"ב
    us_indices = {
        "מָדָד הָאֵס אֵנְד פִּי חָמֵש מֵאוֹת": "^GSPC",
        "הָנָאסְדָק": "^IXIC",
        "הָדָאוֹ ג'וֹנְס": "^DJI",
        "הָרָאסֵל": "^RUT"
    }
    # * ETF עוקבים
    us_etfs = {
        "מָדָד הָאֵס אֵנְד פִּי חָמֵש מֵאוֹת": "SPY",
        "הָנָאסְדָק": "QQQ",
        "הָדָאוֹ ג'וֹנְס": "DIA",
        "הָרָאסֵל": "IWM"
    }
    # * מניות בולטות
    us_stocks = {
        "אָפֵּל": "AAPL",
        "אֵנְבִידְיָה": "NVDA",
        "אָמָזוֹן": "AMZN",
        "טֵסְלָה": "TSLA"
    }
    
    now = datetime.datetime.now(pytz.timezone("Asia/Jerusalem"))
    # * שבת/ראשון בישראל → ארה"ב סגור
    is_us_market_closed_weekend = now.weekday() in [5, 6]

    hour_24 = now.hour
    hour_12 = hour_24 if hour_24 <= 12 else hour_24 - 12
    minute = now.minute
    hour_str = f"{number_to_hebrew_words(hour_12)} וְ{number_to_hebrew_words(minute)} דַקוֹת"
    segment = get_time_segment(now)

    report = f"הִנֵה תְמוּנַת הַשׁוּק נָכוֹן לֵשָעָה {hour_str} {segment}.\n\n"
    results = {}

    # * שעות מסחר ניו-יורק (שעון ישראל)
    ny_open = now.replace(hour=16, minute=30, second=0, microsecond=0)
    ny_close = now.replace(hour=23, minute=0, second=0, microsecond=0)

    # * בחירת מקור נתונים למדדים (פתוח/מוקדם-מאוחר/סגור)
    if is_us_market_closed_weekend:
        indices_source = us_indices
    elif now < ny_open or now > ny_close:
        indices_source = us_etfs
    else:
        indices_source = us_indices

    # * ריכוז כל הטיקרים לשליפה
    all_tickers_to_fetch = {**tickers}
    all_tickers_to_fetch.update(indices_source)
    all_tickers_to_fetch.update(us_stocks)
    
    # * שליפה
    for name, ticker in all_tickers_to_fetch.items():
        try:
            pct, price, trend = get_stock_change(ticker)
            results[name] = {"pct": pct, "price": price, "trend": trend}
        except Exception:
            results[name] = {"pct": None, "price": None, "trend": None}

    # * ישראל
    open_time = now.replace(hour=9, minute=59, second=0, microsecond=0)
    close_time = now.replace(hour=17, minute=25, second=0, microsecond=0)
    ta125 = results.get("תֵל אָבִיב מֵאָה עֵשְׂרִים וֵחָמֵש", {})
    ta35 = results.get("תֵל אָבִיב שְׁלוֹשִׁים וֵחָמֵש", {})

    if now < open_time:
        delta = open_time - now
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        report += (
            "בֵּּיִשְׂרָאֵל:\n"
            f"בּוּרְסָת תֵל אָבִיב טֶרֶם נִפְתְּחָה; תִּפָּתַח בֵּעוֹד "
            f"{number_to_hebrew_words(hours)} שָעוֹת וֵ-{number_to_hebrew_words(minutes)} דָקוֹת.\n"
        )
    elif now > close_time:
        report += "בֵּיִשְׂרָאֵל:\nהָבּוּרְסָה נִסְגֵרָה.\n"
        if ta125.get("price") is not None and ta125.get("pct") is not None:
            verb1 = "עָלָה" if ta125["pct"] > 0 else "יָרָד"
            report += (
                f"מָדָד ת״א-125 {verb1} בֵּ{number_to_hebrew_words(abs(ta125['pct']))} "
                f"אָחוּז וֵנִנְעָל בֵּרָמָה שֵׁל {number_to_hebrew_words(ta125['price'])} נְקוּדוֹת.\n"
            )
        if ta35.get("price") is not None and ta35.get("pct") is not None:
            verb2 = "עָלָה" if ta35["pct"] > 0 else "יָרָד"
            report += (
                f"מָדָד ת״א-35 {verb2} בֵּ{number_to_hebrew_words(abs(ta35['pct']))} "
                f"אָחוּז וֵנִנְעָל בֵּרָמָה שֵׁל {number_to_hebrew_words(ta35['price'])} נְקוּדוֹת.\n"
            )
    else:
        report += "בֵּיִשְׂרָאֵל:\n"
        for name in ["תֵל אָבִיב מֵאָה עֵשְׂרִים וֵחָמֵש", "תֵל אָבִיב שְׁלוֹשִׁים וֵחָמֵש"]:
            d = results.get(name, {})
            if d.get("pct") is None or d.get("price") is None:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מָדָד {name}.\n"
                continue
            direction = format_direction(d.get("pct"), d.get("trend"))
            report += (
                f"מָדָד {name} {direction} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} "
                f"אָחוּז וֵעוֹמֵד כְּעַת עַל {number_to_hebrew_words(d.get('price', 0))} נְקוּדוֹת.\n"
            )

    # * בורסות העולם (ארה"ב)
    report += "\nבֵּבּוּרְסוֹת הָעוֹלָם:\n"
    if is_us_market_closed_weekend:
        report += "הַבּוּרְסָה סְגוּרָה; נִתּוּנֵי סְגִירָה קוֹדֶמֶת.\n"
        for name in us_indices.keys():
            d = results.get(name, {})
            report += f"{name} עוֹמֵד כָּעֵת עַל {number_to_hebrew_words(d['price'])} נ׳.\n" if d.get("price") is not None else f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"
    elif now < ny_open:
        report += "הַבּוּרְסָה סְגוּרָה; נִתּוּנֵי ETF (מֻקְדָּם).\n"
        for name in us_etfs.keys():
            d = results.get(name, {})
            report += f"{name} {format_direction(d.get('pct'), d.get('trend'))} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n" if d.get("pct") is not None else f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"
    elif now > ny_close:
        report += "הַבּוּרְסָה סְגוּרָה; נִתּוּנֵי ETF (מְאוּחָר).\n"
        for name in us_etfs.keys():
            d = results.get(name, {})
            report += f"{name} {format_direction(d.get('pct'), d.get('trend'))} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n" if d.get("pct") is not None else f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"
    else:
        for name in us_indices.keys():
            d = results.get(name, {})
            if d.get("pct") is not None and d.get("price") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"))
                report += f"{name} {direction} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז וֵעוֹמֵד עַל {number_to_hebrew_words(d.get('price', 0))} נ׳.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"

    # * מניות ארה"ב (נקבה)
    report += "\nבֵּשוּק הָמֵנָיוֹת:\n"
    if is_us_market_closed_weekend:
        report += "הַבּוּרְסָה סְגוּרָה; נִתּוּנֵי סְגִירָה.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            report += f"מֵנָיָת {stock_name} נִסְגְּרָה בֵּ{number_to_hebrew_words(d['price'])} דוֹלָר.\n" if d.get("price") is not None else f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָת {stock_name}.\n"
    elif now < ny_open:
        report += "נִתּוּנֵי מִסְחָר מֻקְדָּם.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            report += f"מֵנָיָת {stock_name} {format_direction(d.get('pct'), d.get('trend'), threshold=5, is_female=True)} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n" if d.get("pct") is not None else f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָת {stock_name}.\n"
    elif now > ny_close:
        report += "נִתּוּנֵי מִסְחָר מְאוּחָר.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            report += f"מֵנָיָת {stock_name} {format_direction(d.get('pct'), d.get('trend'), threshold=5, is_female=True)} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n" if d.get("pct") is not None else f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָת {stock_name}.\n"
    else:
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("pct") is not None and d.get("price") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"), threshold=5, is_female=True)
                report += f"מֵנָיָת {stock_name} {direction} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז וֵנִסְחֶרֶת בְּ{number_to_hebrew_words(d.get('price', 0))} דוֹלָר.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָת {stock_name}.\n"

    # * קריפטו (זכר) – תמיד שינוי + רמה
    report += "\nבֵּגִיזְרָת הָקְרִיפְּטוֹ:\n"
    for name in ["הָבִּיטְקוֹיְן", "הָאִיתֵרְיוּם"]:
        d = results.get(name, {})
        if d.get("pct") is not None and d.get("price") is not None:
            direction = format_direction(d.get("pct"), d.get("trend"), is_female=False)
            report += f"{name} {direction} ב{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז וֵנִסְחָר בְּ{number_to_hebrew_words(d.get('price', 0))} דוֹלָר.\n"
        else:
            report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"

    # * סחורות/דולר (זכר) – תמיד שינוי + רמה
    report += "\nעוֹד בָּעוֹלָם:\n"
    for name, unit in [("הָזָהָב", "לֵאוֹנְקִיָה"), ("הָנֵפְט", "לֵחָבִית"), ("הָדוֹלָר", "שְׁקָלִים")]:
        d = results.get(name, {})
        if d.get("pct") is not None and d.get("price") is not None:
            direction = format_direction(d.get("pct"), d.get("trend"), is_female=False)
            report += f"{name} {direction} וֵעוֹמֵד עַל {number_to_hebrew_words(d.get('price', 0))} {unit}.\n"
        else:
            report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"

    return report

# * עטיפה חיצונית
def generate_market_text():
    return get_market_report()
