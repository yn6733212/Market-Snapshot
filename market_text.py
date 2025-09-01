import yfinance as yf
import datetime
import pytz
from num2words import num2words
import pandas as pd

# * המרת מספרים למילים (עברית)
def number_to_hebrew_words(number):
    rounded_number = round(number, 2)
    parts = str(rounded_number).split(".")
    integer_part = int(parts[0])
    if len(parts) > 1 and int(parts[1]) > 0:
        decimal_part = int(parts[1])
        integer_words = num2words(integer_part, lang='he')
        decimal_words = num2words(decimal_part, lang='he')
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
    hour_str = f"{number_to_hebrew_words(hour_12)} וְ{number_to_hebrew_words(minute)} דַּקּוֹת"
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

    # * בורסות העולם (ארה״ב)
    report += "\nבֵּבּוּרְסוֹת הָעוֹלָם:\n"
    if is_us_market_closed_weekend:
        report += "הַבּוּרְסָה בְּאַרְצוֹת הַבְּרִית סְגוּרָה, וְהַנֵתוּנִים מִתְיַחֲסִים לְשַׁעָרֵי הַסְגִירָה הָאַחְרוֹנִים.\n"
        for name in us_indices.keys():
            d = results.get(name, {})
            if d.get("price") is not None:
                report += f"{name} עוֹמֵד כָּעֵת עַל {number_to_hebrew_words(d['price'])} נְקוּדוֹת.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"
    elif now < ny_open:
        report += "הַבּוּרְסָה בְּנְיוּ־יוֹרְק סְגוּרָה וּצְפוּיָה לְהִפָּתֵחַ לְאַחַר מִכֵּן הַנְּתוּנִים מְבוּסָסִים עַל מִסְחָר מוּקְדָם בְּתְעוּדוֹת סַל.\n"
        for name in us_etfs.keys():
            d = results.get(name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"))
                report += f"{name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"
    elif now > ny_close:
        report += "הַבּוּרְסָה בְּנְיוּ־יוֹרְק נִסְגְּרָה הַנְּתוּנִים מְבוּסָסִים עַל מִסְחָר מְאֻחָר בְּתְעוּדוֹת סַל.\n"
        for name in us_etfs.keys():
            d = results.get(name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"))
                report += f"{name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"
    else:
        for name in us_indices.keys():
            d = results.get(name, {})
            if d.get("pct") is not None and d.get("price") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"))
                report += (
                    f"{name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז "
                    f"וְעוֹמֵד כָּעֵת עַל {number_to_hebrew_words(d.get('price', 0))} נְקוּדוֹת.\n"
                )
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"

    # * שוק המניות (נקבה)
    report += "\nשׁוּק הַמֵנָיוֹת:\n"
    if is_us_market_closed_weekend:
        report += "הַבּוּרְסָה סְגוּרָה, וְהַנֵתוּנִים מִתְיַחֲסִים לִשְׁעָרֵי הַסְגִירָה הָאַחֲרוֹנִים.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("price") is not None:
                report += f"מֵנָיָית {stock_name} נִסְגֵרָה בֵּשָׁעַר {number_to_hebrew_words(d['price'])} דוֹלָר.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָית {stock_name}.\n"
    elif now < ny_open:
        report += "הַבּוּרְסָה סְגוּרָה כָּרֶגַע הַנְּתוּנִים הֵם מִמִּסְחָר מוּקְדָם.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"), threshold=5, is_female=True)
                report += f"מֵנָיָית {stock_name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָית {stock_name}.\n"
    elif now > ny_close:
        report += "הַבּוּרְסָה נִסְגְּרָה; הַנְּתוּנִים הֵם מִמִּסְחָר מְאֻחָר.\n"
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("pct") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"), threshold=5, is_female=True)
                report += f"מֵנָיָית {stock_name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז.\n"
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָית {stock_name}.\n"
    else:
        for stock_name in us_stocks.keys():
            d = results.get(stock_name, {})
            if d.get("pct") is not None and d.get("price") is not None:
                direction = format_direction(d.get("pct"), d.get("trend"), threshold=5, is_female=True)
                report += (
                    f"מֵנָיָית {stock_name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז "
                    f"וְנִסְחֶרֶת כָּעֵת בִּשְׁעַר {number_to_hebrew_words(d.get('price', 0))} דוֹלָר.\n"
                )
            else:
                report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר מֵנָיָית {stock_name}.\n"

    # * קריפּטו (זכר) – שינוי + רמה
    report += "\nקְרִיפְּטוֹ:\n"
    for name in ["בִּיטְקוֹיִן", "אִיתֵרְיוּם"]:
        d = results.get(name, {})
        if d.get("pct") is not None and d.get("price") is not None:
            direction = format_direction(d.get("pct"), d.get("trend"), is_female=False)
            report += (
                f"{name} {direction} בְּ-{number_to_hebrew_words(abs(d.get('pct', 0)))} אָחוּז "
                f"וְנִסְחָר בֵּשָׁעָר שֵׁל {number_to_hebrew_words(d.get('price', 0))} דוֹלָר.\n"
            )
        else:
            report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"

    # * סחורות ומט״ח (זכר) – שינוי + רמה
    report += "\nסְחוֹרוֹת וּמָטָח:\n"
    for name, unit in [("זָהָב", "לְאוֹנְקִיָה"), ("נֶפְט", "לְחָבִית"), ("דוֹלָר", "שְׁקָלִים ")]:
        d = results.get(name, {})
        if d.get("pct") is not None and d.get("price") is not None:
            direction = format_direction(d.get("pct"), d.get("trend"), is_female=False)
            report += f"{name} {direction} וְעוֹמֵד כָּעֵת עַל {number_to_hebrew_words(d.get('price', 0))} {unit}.\n"
        else:
            report += f"לֹא נִמְצְאוּ נְתוּנִים עֲבוּר {name}.\n"

    return report

# * עטיפה
def generate_market_text():
    return get_market_report()
