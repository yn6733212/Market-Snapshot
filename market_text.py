import yfinance as yf
import datetime
import pytz
from num2words import num2words
import pandas as pd

# * המרת מספרים למילים (עברית)
def number_to_hebrew_words(number):
    """
    כללים:
    - 4 ספרות ומעלה: ללא נקודה עשרונית.
    - 3 ספרות: עם ספרה עשרונית אחת בלבד (אם 0 — לא מוסיפים נקודה).
    - 1–2 ספרות: רגיל (עד שתי ספרות עשרוניות).
    """
    abs_int = int(abs(number))
    digits = len(str(abs_int))

    # 4+ ספרות: רק שלם (מעוגל)
    if digits >= 4:
        integer_words = num2words(int(round(number)), lang='he')
        return integer_words

    # 3 ספרות: ספרה עשרונית אחת
    if digits == 3:
        val = round(number, 1)  # עיגול לעשירית
        integer_part = int(val)
        # ספרה אחת אחרי הנקודה
        frac_digit = int(round(abs(val) * 10)) % 10
        integer_words = num2words(integer_part, lang='he')
        if frac_digit == 0:
            return integer_words
        decimal_words = num2words(frac_digit, lang='he')
        return f"{integer_words} נְקוּדָה {decimal_words}"

    # 1–2 ספרות: עד שתי ספרות עשרוניות
    rounded_number = round(number, 2)
    integer_part_str, decimal_part_str = f"{rounded_number:.2f}".split(".")
    integer_part = int(integer_part_str)
    if int(decimal_part_str) > 0:
        integer_words = num2words(integer_part, lang='he')
        decimal_words = num2words(int(decimal_part_str), lang='he')
        if integer_part == 0:
            return f"אֵפֵס נְקוּדָה {decimal_words}"
        return f"{integer_words} נְקוּדָה {decimal_words}"
    else:
        return num2words(integer_part, lang='he')

# * פלח זמן כללי
def get_time_segment(now):
    hour = now.hour
    if 6 <= hour < 12:
        return "בַּבּוֹקֶר"
    elif 12 <= hour < 18:
        return "בָּצוֹהוֹרָיִם"
    elif 18 <= hour < 23:
        return "בָּעֶרֶב"
    else:
        return "בַּלָיְלָה"

# * שינוי/רמה/טרנד לטיקר
def get_stock_change(ticker):
    stock = yf.Ticker(ticker)
    try:
        hist = stock.history(period="10d", interval="1d")
    except Exception:
        return None, None, None
    if hist is None or hist.empty or "Close" not in hist.columns:
        return None, None, None
    hist = hist.dropna(subset=["Close"])

    # * צריך 2+ נרות
    if len(hist) < 2:
        if len(hist) == 1:
            price_only = float(hist["Close"].iloc[-1])
            return None, round(price_only, 2), None
        return None, None, None

    # * המרת אזור זמן (חסין)
    jerusalem = pytz.timezone("Asia/Jerusalem")
    ts = hist.index[-1]
    try:
        if getattr(ts, "tzinfo", None) is not None:
            _ = ts.tz_convert(jerusalem) if hasattr(ts, "tz_convert") else ts.astimezone(jerusalem)
        else:
            ts_utc = pytz.utc.localize(ts)
            _ = ts_utc.astimezone(jerusalem)
    except Exception:
        pass

    current = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2])
    pct = ((current - prev) / prev) * 100 if prev != 0 else 0.0

    # * טרנד עם 3+ נרות
    trend = None
    if len(hist) >= 3:
        before_prev = float(hist["Close"].iloc[-3])
        if current > prev > before_prev:
            trend = "מַמְשִׁיךְ לַעֲלוֹת"
        elif current < prev < before_prev:
            trend = "מַמְשִׁיךְ לְרֵדֶת"

    return round(pct, 2), round(current, 2), trend

# * ניסוח כיוון (סף דרמטי; זכר/נקבה)
def format_direction(pct, trend, threshold=1.5, is_female=False):
    if pct is None:
        return "לֹא זָמִין"
    if trend:
        base = trend
    else:
        if abs(pct) >= threshold:
            base = "עוֹלֶה בְּחַדוּת" if pct > 0 else "יוֹרֵד בְּחַדוּת"
        else:
            base = "עוֹלֶה" if pct > 0 else "יוֹרֵד"
    if is_female:
        base = base.replace("עוֹלֶה", "עוֹלָה").replace("יוֹרֵד", "יוֹרֶדֶת").replace("מַמְשִׁיךְ", "מַמְשִׁיכָה")
    return base

# * כיוון מיוחד לדולר: "מִתְחַזֵּק/נֶחְלָשׁ" או "מַמְשִׁיךְ לְהִתְחַזֵּק/לְהֵיחָלֵשׁ"
def format_usd_direction(pct, trend, threshold=1.5):
    if pct is None:
        return "לֹא זָמִין"
    if trend:
        return "מַמְשִׁיךְ לְהִתְחַזֵּק" if pct > 0 else "מַמְשִׁיךְ לְהֵיחָלֵשׁ"
    if abs(pct) >= threshold:
        return "מִתְחַזֵּק בְּחַדוּת" if pct > 0 else "נֶחְלָשׁ בְּחַדוּת"
    return "מִתְחַזֵּק" if pct > 0 else "נֶחְלָשׁ"

# * דו״ח תמונת שוק
def get_market_report():
    # * טיקרים: ישראל/קריפּטו/סחורות/דולר
    tickers = {
        "תֵל אָבִיב מֵאָה עֵשְׂרִים וֵחָמֵשׁ": "^TA125.TA",
        "תֵל אָבִיב שְׁלוֹשִׁים וֵחָמֵשׁ": "TA35.TA",
        "בִּיטְקוֹיִן": "BTC-USD",
        "אִיתֵרְיוּם": "ETH-USD",
        "זָהָב": "GC=F",
        "נֶפְט": "CL=F",
        "דוֹלָר": "USDILS=X"
    }

    # * מדדי מקור בארה״ב
    us_indices = {
        "אֵס אֵנְד פִּי חָמֵשׁ מֵאוֹת": "^GSPC",
        "נָאסְדָק": "^IXIC",
        "דָאוֹ ג׳וֹנְס": "^DJI",
        "רַאסֶל אָלְפָּיים": "^RUT"
    }
    # * ETF עוקבים
    us_etfs = {
        "אֵס אֵנְד פִּי חָמֵשׁ מֵאוֹת": "SPY",
        "נָאסְדָק": "QQQ",
        "דָאוֹ ג׳וֹנְס": "DIA",
        "רַאסֶל אָלְפָּיים": "IWM"
    }
    # * מניות בולטות (נקבה)
    us_stocks = {
        "אַפֵּל": "AAPL",
        "אֵנְבִידְיָה": "NVDA",
        "אָמָזוֹן": "AMZN",
        "טֵסְלָה": "TSLA"
    }
    
    now = datetime.datetime.now(pytz.timezone("Asia/Jerusalem"))
    is_us_market_closed_weekend = now.weekday() in [5, 6]  # * שבת/ראשון → ארה״ב סגוּרה

    # * זמן פתיח מנוקד
    hour_24 = now.hour
    hour_12 = hour_24 if hour_24 <= 12 else hour_24 - 12
    minute = now.minute
    hour_str = f"{number_to_hebrew_words(hour_12)} וְ{number_to_hebrew_words(minute)} דַּקוֹת"
    segment = get_time_segment(now)
    report = f"הִנֵה תְמוּנַת הַשׁוּק, נָכוֹן לְשָׁעָה {hour_str} {segment}.\n\n"

    results = {}

    # * שעות מסחר ניו־יורק (שעון ישראל)
    ny_open = now.replace(hour=16, minute=30, second=0, microsecond=0)
    ny_close = now.replace(hour=23, minute=0, second=0, microsecond=0)

    # * מקור נתונים למדדים
    if is_us_market_closed_weekend:
        indices_source = us_indices
    elif now < ny_open or now > ny_close:
        indices_source = us_etfs
    else:
        indices_source = us_indices

    # * ריכוז כל הטיקרים
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
    ta125 = results.get("תֵל אָבִיב מֵאָה עֵשְׂרִים וֵחָמֵשׁ", {})
    ta35 = results.get("תֵל אָבִיב שְׁלוֹשִים וֵחָמֵשׁ", {})

    if now < open_time:
        delta = open_time - now
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        report += (
            "בְּיִשְׂרָאֵל:\n"
            f"הַבּוּרְסָה טֶרֶם נִפְתֵחָה וּצְפוּיָה לְהִפָּתָח בְּעוֹד "
            f"{number_to_hebrew_words(hours)} שָׁעוֹת וְ-{number_to_hebrew_words(minutes)} דָקוֹת.\n"
        )
    elif now > close_time:
        report += "בְּיִשְׂרָאֵל:\nהַבּוּרְסָה נִסְגְּרָה.\n"
        if ta125.get("price") is not None and ta125.get("pct") is not None:
            verb1 = "עָלָה" if ta125["pct"] > 0 else "יָרַד"
            report += (
                f"מַדָד תֵל אָבִיב מֵאָה עֵשְׂרִים וֵחָמֵשׁ {verb1} בְּ-{number_to_hebrew_words(abs(ta125['pct']))} אָחוּז "
                f"וְנִנְעַל בְּרָמָה שֶׁל {number_to_hebrew_words(ta125['price'])} נְקוּדוֹת.\n"
            )
        if ta35.get("price") is not None and ta35.get("pct") is not None:
            verb2 = "עָלָה" if ta35["pct"] > 0 else "יָרַד"
            report += (
                f"מַדָד תֵל אָבִיב שְׁלוֹשִים וֵחָמֵשׁ {verb2} בְּ-{number_to_hebrew_words(abs(ta35['pct']))} אָחוּז "
                f"וְנִנְעַל בְּרָמָה שֶׁל {number_to_hebrew_words(ta35['price'])} נְקוּדוֹת.\n"
            )
    else:
        report += "בְּיִשְׂרָאֵל:\n"
        for name in ["תֵל אָבִיב מֵאָה עֵשְׂרִים וֵחָמֵשׁ", "תֵל אָבִיב שְׁלוֹשִׁים וֵחָמֵשׁ"]:
            d = results.get(name, {})
            if d.get("pct") is None or d.get("price") is None:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מַדָד {name}.\n"
                continue
            direction = format_direction(d.get("pct"), d.get("trend"))
            report += (
                f"מַדָד {name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז "
                f"וְעוֹמֵד כָּעֵת עַל {number_to_hebrew_words(d.get('price', 0))} נְקוּדוֹת.\n"
            )

    # * בורסות העולם (ארה״ב) — הצגה כ"מדד ה..."
    report += "\nבְּבוּרְסוֹת הָעוֹלָם:\n"
    if is_us_market_closed_weekend:
        report += "הַבּוּרְסָה בְּאַרְצוֹת הַבְּרִית סְגוּרָה; הַנְּתוּנִים מִתְיַחֲסִים לְשַׁעֲרֵי הַסְגִירָה הָאַחֲרוֹנִים.\n"
        for name in us_indices.keys():
            d = results.get(name, {})
            if d.get("price") is not None:
                report += f"מַדָד ה{name} עוֹמֵד כָּעֵת עַל {number_to_hebrew_words(d['price'])} נְקוּדוֹת.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מַדָד ה{name}.\n"
    elif now < ny_open:
        report += "וָול סְטְרִיט סְגוּרָה כָּרֶגַע; הַנְּתוּנִים מִמִּסְחָר מוּקְדָם בְּתְעוּדוֹת סַל.\n"
        for name in us_etfs.keys():
            d = results.get(name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"))
                report += f"מַדָד ה{name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מַדָד ה{name}.\n"
    elif now > ny_close:
        report += "נְיוּ־יוֹרְק נִסְגְּרָה; הַנְּתוּנִים מִמִּסְחָר מְאֻחָר בְּתְעוּדוֹת סַל.\n"
        for name in us_etfs.keys():
            d = results.get(name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"))
                report += f"מַדָד ה{name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מַדָד ה{name}.\n"
    else:
        for name in us_indices.keys():
            d = results.get(name, {})
            if d.get("pct") is not None and d.get("price") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"))
                report += (
                    f"מַדָד ה{name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז "
                    f"וְעוֹמֵד כָּעֵת עַל {number_to_hebrew_words(d.get('price', 0))} נְקוּדוֹת.\n"
                )
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מַדָד ה{name}.\n"

    # * שוק המניות — "מניית ..."
    report += "\nשׁוּק הַמְּנָיוֹת:\n"
    if is_us_market_closed_weekend:
        report += "הַבּוּרְסָה סְגוּרָה; הַנְּתוּנִים לִשְׁעָרֵי הַסְגִירָה הָאַחֲרוֹנִים.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("price") is not None:
                report += f"מניית {stock_name} נִסְגְּרָה בְּשַׁעַר {number_to_hebrew_words(d['price'])} דוֹלָר.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מניית {stock_name}.\n"
    elif now < ny_open:
        report += "הַבּוּרְסָה סְגוּרָה כָּרֶגַע; הַנְּתוּנִים הֵם מִמִּסְחָר מוּקְדָם.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"), threshold=5, is_female=True)
                report += f"מניית {stock_name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מניית {stock_name}.\n"
    elif now > ny_close:
        report += "הַבּוּרְסָה נִסְגְּרָה; הַנְּתוּנִים מִמִּסְחָר מְאֻחָר.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"), threshold=5, is_female=True)
                report += f"מניית {stock_name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מניית {stock_name}.\n"
    else:
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("pct") is not None and d.get("price") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"), threshold=5, is_female=True)
                report += (
                    f"מניית {stock_name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז "
                    f"וְנִסְחֶרֶת כָּעֵת בִּשְׁעַר {number_to_hebrew_words(d.get('price', 0))} דוֹלָר.\n"
                )
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מניית {stock_name}.\n"

    # * קְרִיפְּטוֹ — הקדמה + "הַבִּיטְקוֹיִן / הָאִיתֵרְיוּם"
    report += "\nבִּגְּזֶרֶת הַקְרִיפְּטוֹ:\n"
    for internal_name, display_name in [("בִּיטְקוֹיִן", "הַבִּיטְקוֹיִן"), ("אִיתֵרְיוּם", "הָאִיתֵרְיוּם")]:
        d = results.get(internal_name, {})
        if d.get("pct") is not None and d.get("price") is not None:
            direction = format_direction(d.get("pct"), d.get("trend"), is_female=False)
            report += (
                f"{display_name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז "
                f"וְנִסְחָר בִּשְׁעַר שֶׁל {number_to_hebrew_words(d.get('price', 0))} דוֹלָר.\n"
            )
        else:
            report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {display_name}.\n"

    # * עוֹד בָּעוֹלָם — זהב, נפט
    report += "\nעוֹד בָּעוֹלָם:\n"
    for name, unit, display in [("זָהָב", "לְאוֹנְקִיָה", "הַזָּהָב"), ("נֶפְט", "לְחָבִית", "הַנֶּפְט")]:
        d = results.get(name, {})
        if d.get("pct") is not None and d.get("price") is not None:
            direction = format_direction(d.get("pct"), d.get("trend"), is_female=False)
            report += f"{display} {direction} וְעוֹמֵד כָּעֵת עַל {number_to_hebrew_words(d.get('price', 0))} {unit}.\n"
        else:
            report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {display}.\n"

    # * הדולר — בסוף: "מִתְחַזֵּק/נֶחְלָשׁ" או "מַמְשִׁיךְ..."
    d_usd = results.get("דוֹלָר", {})
    report += "\n"
    if d_usd.get("pct") is not None and d_usd.get("price") is not None:
        usd_dir = format_usd_direction(d_usd.get("pct"), d_usd.get("trend"))
        report += (
            f"הַדּוֹלָר {usd_dir} מוּל הַשֶּׁקֶל "
            f"וְנִסְחָר בִּשְׁעַר שֶׁל {number_to_hebrew_words(d_usd.get('price', 0))} שְׁקָלִים.\n"
        )
    else:
        report += "לֹא נִמְצְאוּ נְתוּנִים עֲבוּר הַדּוֹלָר.\n"

    return report

# * עטיפה
def generate_market_text():
    return get_market_report()
