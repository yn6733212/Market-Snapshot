import yfinance as yf
import datetime
import pytz
from num2words import num2words


def number_to_hebrew_words(number):
    parts = str(round(number, 2)).split(".")
    if len(parts) == 1:
        return num2words(int(parts[0]), lang='he')
    else:
        integer_part = num2words(int(parts[0]), lang='he')
        decimal_part = num2words(int(parts[1]), lang='he')
        return f"{integer_part} נֵקוּדָה {decimal_part}"


def get_time_segment(now):
    hour = now.hour
    if 6 <= hour < 12:
        return "בַּבֹּקֶר"
    elif 12 <= hour < 18:
        return "בַּצָּהֳרַיִם"
    elif 18 <= hour < 23:
        return "בָּעֶרֶב"
    else:
        return "בַלַּיְלָה"


def format_time_hebrew(now):
    """שעה 14:05 -> שתיים וחמש דקות, שעה 13:40 -> אחת וארבעים דקות"""
    hour = now.hour
    minute = now.minute

    # המרה לשעון 12 שעות
    if hour == 0:
        hour = 12
    elif hour > 12:
        hour -= 12

    hour_word = number_to_hebrew_words(hour)
    minute_word = number_to_hebrew_words(minute)

    if minute == 0:
        return f"{hour_word} בְּדִיּוּק"
    else:
        return f"{hour_word} וְ{minute_word} דַּקּוֹת"


def get_stock_change(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="5d", interval="1d")
    if len(hist) < 3:
        return None, None, None
    current = hist["Close"].iloc[-1]
    prev = hist["Close"].iloc[-2]
    before_prev = hist["Close"].iloc[-3]

    pct = ((current - prev) / prev) * 100
    trend = None
    if current > prev > before_prev:
        trend = "מַמְשִׁיךְ לַעֲלוֹת"
    elif current < prev < before_prev:
        trend = "מַמְשִׁיךְ לָרֶדֶת"

    return round(pct, 2), round(current, 2), trend


def format_direction(pct, trend, threshold=1.5, is_female=False):
    if pct is None:
        return "לֹא זָמִין"

    if trend:
        base = trend
    else:
        if abs(pct) >= threshold:
            base = "עוֹלֶה בְּצוּרָה דְּרָמָטִית" if pct > 0 else "יוֹרֵד בְּצוּרָה דְּרָמָטִית"
        else:
            base = "עוֹלֶה" if pct > 0 else "יוֹרֵד"

    # התאמה לנקבה
    if is_female:
        base = (
            base.replace("עוֹלֶה", "עוֹלָה")
            .replace("יוֹרֵד", "יוֹרֶדֶת")
            .replace("מַמְשִׁיךְ", "מַמְשִׁיכָה")
        )

    return base


def get_market_report():
    tickers = {
        "תֵּל אָבִיב-125": "^TA125.TA",
        "תֵּל אָבִיב-35": "TA35.TA",
        "SPY": "SPY",  # נשתמש במקום SPX לפני פתיחה
        "QQQ": "QQQ",
        "DIA": "DIA",
        "IWM": "IWM",
        "הַבִּיטְקוֹיְן": "BTC-USD",
        "הָאִיתֵרְיוּם": "ETH-USD",
        "הַזָּהָב": "GC=F",
        "הַנֵּפְט": "CL=F",
        "הַדוֹלָר": "USDILS=X",
        "אַפֵּּל": "AAPL",
        "אֵנְבִּידְיָה": "NVDA",
        "אַמָּזוֹן": "AMZN",
        "טֵסְלָה": "TSLA",
    }

    now = datetime.datetime.now(pytz.timezone("Asia/Jerusalem"))
    hour_str = format_time_hebrew(now)
    segment = get_time_segment(now)

    report = f"הִנֵּה תְּמוּנַת הַשּׁוּק נָכוֹנָה לְשָׁעָה {hour_str} {segment}.\n\n"
    results = {}

    for name, ticker in tickers.items():
        try:
            pct, price, trend = get_stock_change(ticker)
            results[name] = {"pct": pct, "price": price, "trend": trend}
        except:
            results[name] = {"pct": None, "price": None, "trend": None}

    # ---- ישראל ----
    report += "בְּיִשְׂרָאֵל:\n"
    for name in ["תֵּל אָבִיב-125", "תֵּל אָבִיב-35"]:
        d = results[name]
        direction = format_direction(d["pct"], d["trend"])
        report += (
            f"מַדָּד {name} {direction} בְּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז "
            f"וְעוֹמֵד עַל {number_to_hebrew_words(d['price'])} נְקוּדוֹת.\n"
        )

    # ---- עולמי ----
    ny_open = now.replace(hour=16, minute=30)
    ny_close = now.replace(hour=23, minute=0)
    indices = {
        "מַדָּד אֵס-אַנְד-פִּי 500": results["SPY"],
        "נַאסְדָּק": results["QQQ"],
        "דָּאוּ ג'וֹנְס": results["DIA"],
        "רָאסֵל": results["IWM"],
    }

    if now < ny_open or now > ny_close:  # טרום/מאוחר
        report += "\nבְּבּוּרְסוֹת הָעוֹלָם:\n"
        report += "הַנְּתוּנִים מִתְיַחֲסִים לַמִּסְחָר הַמּוּקְדָם/הַמְּאוּחָר.\n"
        for name, d in indices.items():
            direction = "עָלָה" if d["pct"] and d["pct"] > 0 else "יָרַד"
            report += f"{name} {direction} בְּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז.\n"
    else:  # מסחר פתוח
        report += "\nבְּבּוּרְסוֹת הָעוֹלָם:\n"
        for name, d in indices.items():
            direction = format_direction(d["pct"], d["trend"])
            report += (
                f"{name} {direction} בְּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז "
                f"וְעוֹמֵד עַל {number_to_hebrew_words(d['price'])} נְקוּדוֹת.\n"
            )

    # ---- מניות ----
    stocks = ["אַפֵּּל", "אֵנְבִּידְיָה", "אַמָּזוֹן", "טֵסְלָה"]
    report += "\nבְּשׁוּק הַמָּנִיּוֹת:\n"
    for stock in stocks:
        d = results[stock]
        direction = format_direction(d["pct"], d["trend"], threshold=5, is_female=True)
        report += (
            f"מְנִיַּת {stock} {direction} בְּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז "
            f"וְנִסְחֶרֶת בְּשַׁעַר שֶׁל {number_to_hebrew_words(d['price'])} דוֹלָר.\n"
        )

    return report


def generate_market_text():
    return get_market_report()
