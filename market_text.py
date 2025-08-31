import yfinance as yf
import datetime
import pytz
from num2words import num2words
import pandas as pd

def number_to_hebrew_words(number):
    """
    Converts a number (including decimals) to Hebrew words.
    Example: 12.45 -> 'שְׁתֵים עֶשְׂרֵה נְקוּדָה אַרְבָּעִים וֵחָמֵש'
    """
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

def get_time_segment(now):
    """
    Returns the time segment of the day in Hebrew.
    """
    hour = now.hour
    if 6 <= hour < 12:
        return "בָּבּוֹקֵר"
    elif 12 <= hour < 18:
        return "בָּצֹהֹרָיִים"
    elif 18 <= hour < 23:
        return "בָּעֵרֵב"
    else:
        return "בָּלָיְלָה"

def get_stock_change(ticker):
    """
    Fetches stock data and calculates the percentage change and trend.
    Handles both live data and last trading day's data.
    """
    stock = yf.Ticker(ticker)
    try:
        hist = stock.history(period="10d", interval="1d")
    except Exception:
        return None, None, None
    
    if len(hist) < 3:
        return None, None, None

    hist = hist.dropna(subset=['Close'])
    
    now_israel_time = datetime.datetime.now(pytz.timezone("Asia/Jerusalem"))
    
    if hist.empty:
        return None, None, None

    # כאן לא משנים את מנגנון החישוב – נשאר כמו שהיה
    last_data_time = hist.index[-1].tz_localize(pytz.timezone("America/New_York")).astimezone(pytz.timezone("Asia/Jerusalem"))
    is_recent_data = (now_israel_time - last_data_time).total_seconds() < 24 * 3600

    if is_recent_data:
        current = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2]
        before_prev = hist["Close"].iloc[-3]
        pct = ((current - prev) / prev) * 100
        trend = None
        if current > prev > before_prev:
            trend = "מַמְשִׁיךְ לַעֲלוֹת"
        elif current < prev < before_prev:
            trend = "מַמְשִׁיךְ לְרֶדֶת"
        return round(pct, 2), round(current, 2), trend
    else:
        last_close = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2]
        pct = ((last_close - prev_close) / prev_close) * 100
        return round(pct, 2), round(last_close, 2), None

def format_direction(pct, trend, threshold=1.5, is_female=False):
    """
    Formats the direction of change (up/down) in Hebrew.
    """
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

def get_market_report():
    """
    Generates a full market report in Hebrew based on current market status.
    """
    tickers = {
        "תֵל אָבִיב מֵאָה עֵשְׂרִים וֵחָמֵש": "^TA125.TA",
        "תֵל אָבִיב שְׁלוֹשִׁים וֵחָמֵש": "TA35.TA",
        "הָבִּיטְקוֹיְן": "BTC-USD",
        "הָאִיתֵרְיוּם": "ETH-USD",
        "הָזָהָב": "GC=F",
        "הָנֵפְט": "CL=F",
        "הָדוֹלָר": "USDILS=X"
    }

    # מדדי מקור
    us_indices = {
        "מָדָד הָאֵס אֵנְד פִּי חָמֵש מֵאוֹת": "^GSPC",
        "הָנָאסְדָק": "^IXIC",
        "הָדָאוֹ ג'וֹנְס": "^DJI",
        "הָרָאסֵל": "^RUT"
    }
    # תעודות סל שעוקבות
    us_etfs = {
        "מָדָד הָאֵס אֵנְד פִּי חָמֵש מֵאוֹת": "SPY",
        "הָנָאסְדָק": "QQQ",
        "הָדָאוֹ ג'וֹנְס": "DIA",
        "הָרָאסֵל": "IWM"
    }
    us_stocks = {
        "אָפֵּל": "AAPL",
        "אֵנְבִידְיָה": "NVDA",
        "אָמָזוֹן": "AMZN",
        "טֵסְלָה": "TSLA"
    }
    
    now = datetime.datetime.now(pytz.timezone("Asia/Jerusalem"))
    # שבת/ראשון בישראל -> הבורסות בארה"ב סגורות לגמרי
    is_us_market_closed_weekend = now.weekday() in [5, 6]

    hour_24 = now.hour
    hour_12 = hour_24 if hour_24 <= 12 else hour_24 - 12
    minute = now.minute
    hour_str = f"{number_to_hebrew_words(hour_12)} וְ{number_to_hebrew_words(minute)} דַקוֹת"
    segment = get_time_segment(now)

    report = f"הִנֵה תְמוּנַת הַשׁוּק נָכוֹן לֵשָעָה {hour_str} {segment}.\n\n"
    results = {}

    # שעות פתיחה/סגירה ניו-יורק לפי אסיה/ירושלים
    ny_open = now.replace(hour=16, minute=30, second=0, microsecond=0)
    ny_close = now.replace(hour=23, minute=0, second=0, microsecond=0)

    # בחירת מה לשלוף למדדי ארה"ב לפי מצב השוק
    if is_us_market_closed_weekend:
        indices_source = us_indices          # סגור לגמרי → מדדי מקור
    elif now < ny_open or now > ny_close:
        indices_source = us_etfs             # מסחר מוקדם/מאוחר → ETF
    else:
        indices_source = us_indices          # פתוח → מדדי מקור

    # ריכוז טיקרים לשליפה
    all_tickers_to_fetch = {**tickers}
    all_tickers_to_fetch.update(indices_source)
    all_tickers_to_fetch.update(us_stocks)
    
    for name, ticker in all_tickers_to_fetch.items():
        try:
            pct, price, trend = get_stock_change(ticker)
            results[name] = {"pct": pct, "price": price, "trend": trend}
        except Exception:
            results[name] = {"pct": None, "price": None, "trend": None}
            
    # ישראל
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
            f"בּוּרְסָת תֵל אָבִיב טֶרֶם נִפְתְּחָה וּצְפוּיָה לֵהִיפָּתָח בֵּעוֹד "
            f"{number_to_hebrew_words(hours)} שָעוֹת וֵ-{number_to_hebrew_words(minutes)} דָקוֹת.\n"
        )
    elif now > close_time:
        report += "בֵּיִשְׂרָאֵל:\nהָבּוּרְסָה נִסְגֵרָה.\n"
        if ta125.get("price") is not None and ta125.get("pct") is not None:
            verb1 = "עָלָה" if ta125["pct"] > 0 else "יָרָד"
            report += (
                f"מָדָד תֵל אָבִיב מֵאָה עֵשְׂרִים וֵחָמֵש {verb1} בֵּ{number_to_hebrew_words(abs(ta125['pct']))} "
                f"אָחוּז וֵנִנְעָל בֵּרָמָה שֵׁל {number_to_hebrew_words(ta125['price'])} נְקוּדוֹת.\n"
            )
        if ta35.get("price") is not None and ta35.get("pct") is not None:
            verb2 = "עָלָה" if ta35["pct"] > 0 else "יָרָד"
            report += (
                f"מָדָד תֵל אָבִיב שְׁלוֹשִׁים וֵחָמֵש {verb2} בֵּ{number_to_hebrew_words(abs(ta35['pct']))} "
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

    # בורסות העולם (ארה"ב)
    report += "\nבֵּבּוּרְסוֹת הָעוֹלָם:\n"
    if is_us_market_closed_weekend:
        # סגור לגמרי → מדדי מקור + רק רמה
        report += "הַבּוּרְסָה סְגוּרָה, הַנְתוּנִים מִתְיַחֲסִים לְשַׁעַר הַסְּגִירָה הַקּוֹדֵם.\n"
        for name in us_indices.keys():
            d = results.get(name, {})
            if d.get("price") is not None:
                report += f"{name} עוֹמֵד עַכְשָׁו עַל {number_to_hebrew_words(d['price'])} נְקוּדוֹת.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"
    elif now < ny_open:
        # מוקדם → ETF + רק שינוי
        report += "הַבּוּרְסָה סְגוּרָה, הַנְתוּנִים הֵם לְפִי תְעוּדוֹת סַל שֶׁעוֹקְבוֹת אַחֲרֵי הַמַּדָּדִים (מִסְחָר מוּקְדָּם).\n"
        for name in us_etfs.keys():
            d = results.get(name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"))
                report += f"{name} {direction} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"
    elif now > ny_close:
        # מאוחר → ETF + רק שינוי
        report += "הַבּוּרְסָה סְגוּרָה, הַנְתוּנִים הֵם לְפִי תְעוּדוֹת סַל שֶׁעוֹקְבוֹת אַחֲרֵי הַמַּדָּדִים (מִסְחָר מְאוּחָר).\n"
        for name in us_etfs.keys():
            d = results.get(name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"))
                report += f"{name} {direction} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"
    else:
        # פתוח → מדדי מקור + שינוי + רמה
        for name in us_indices.keys():
            d = results.get(name, {})
            if d.get("pct") is not None and d.get("price") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"))
                report += (
                    f"{name} {direction} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז "
                    f"וֵעוֹמֵד כְּעַת עַל {number_to_hebrew_words(d.get('price', 0))} נְקוּדוֹת.\n"
                )
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"

    # מניות ארה"ב
    report += "\nבֵּשוּק הָמֵנָיוֹת:\n"
    if is_us_market_closed_weekend:
        # סגור לגמרי → רק רמה (בלי שינוי)
        report += "הַבּוּרְסָה סְגוּרָה, הַנְתוּנִים מִתְיַחֲסִים לְשַׁעַר הַסְּגִירָה הַקּוֹדֵם.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("price") is not None:
                report += f"מֵנָיָת {stock_name} נִסְגְּרָה בְּשַׁעַר {number_to_hebrew_words(d['price'])} דוֹלָר.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָת {stock_name}.\n"
    elif now < ny_open:
        # מוקדם → רק שינוי
        report += "הַבּוּרְסָה סְגוּרָה, הַנְתוּנִים מִתְיַחֲסִים לַמִסְחָר הַמּוּקְדָּם.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"), threshold=5, is_female=True)
                report += f"מֵנָיָת {stock_name} {direction} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָת {stock_name}.\n"
    elif now > ny_close:
        # מאוחר → רק שינוי
        report += "הַבּוּרְסָה סְגוּרָה, הַנְתוּנִים מִתְיַחֲסִים לַמִסְחָר הַמְאֻחָר.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"), threshold=5, is_female=True)
                report += f"מֵנָיָת {stock_name} {direction} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָת {stock_name}.\n"
    else:
        # פתוח → שינוי + רמה
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("pct") is not None and d.get("price") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"), threshold=5, is_female=True)
                report += (
                    f"מֵנָיָת {stock_name} {direction} בֵּ{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז "
                    f"וֵנִסְחֶרֶת כְּעַת בְּשַׁעַר {number_to_hebrew_words(d.get('price', 0))} דוֹלָר.\n"
                )
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָת {stock_name}.\n"

    # קריפטו – תמיד שינוי + רמה
    report += "\nבֵּגִיזְרָת הָקְרִיפְּטוֹ:\n"
    for name in ["הָבִּיטְקוֹיְן", "הָאִיתֵרְיוּם"]:
        d = results.get(name, {})
        if d.get("pct") is not None and d.get("price") is not None:
            direction = format_direction(d.get("pct"), d.get("trend"), is_female=(name == "הָאִיתֵרְיוּם"))
            report += (
                f"{name} {direction} ב{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז "
                f"וֵנִסְחָר בְּשַׁעַר {number_to_hebrew_words(d.get('price', 0))} דוֹלָר.\n"
            )
        else:
            report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"

    # סחורות/דולר – תמיד שינוי + רמה
    report += "\nעוֹד בָּעוֹלָם:\n"
    for name, unit in [("הָזָהָב", "לֵאוֹנְקִיָה"), ("הָנֵפְט", "לֵחָבִית"), ("הָדוֹלָר", "שְׁקָלִים")]:
        d = results.get(name, {})
        if d.get("pct") is not None and d.get("price") is not None:
            direction = format_direction(d.get("pct"), d.get("trend"))
            report += f"{name} {direction} וֵנִמְצָא עַכְשָׁו עַל {number_to_hebrew_words(d.get('price', 0))} {unit}.\n"
        else:
            report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"

    return report

def generate_market_text():
    return get_market_report()
