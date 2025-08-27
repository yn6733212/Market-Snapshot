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
        return "בָּבּוֹקֵר"
    elif 12 <= hour < 18:
        return "בָּצֹהֹרָיִים"
    elif 18 <= hour < 23:
        return "בָּעֵרֵב"
    else:
        return "בָּלָיְלָה"

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
        trend = "מַמְשִׁיךְ לְרֶדֶת"
    return round(pct, 2), round(current, 2), trend

def format_direction(pct, trend, threshold=1.5, is_female=False):
    if pct is None:
        return "לא זמין"
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
    tickers = {
        "תֵל אָבִיב-125": "^TA125.TA",
        "תֵל אָבִיב-35": "TA35.TA",
        "SPX": "^GSPC",
        "QQQ": "QQQ",
        "DIA": "DIA",
        "IWM": "IWM",
        "הָבִּיטְקוֹיְן": "BTC-USD",
        "הָאִיתֵרְיוּם": "ETH-USD",
        "הָזָהָב": "GC=F",
        "הָנֵפְט": "CL=F",
        "הָדוֹלָר": "USDILS=X",
        "אָפֵּל": "AAPL",
        "אֵנְבִידְיָה": "NVDA",
        "אָמָזוֹן": "AMZN",
        "טֵסְלָה": "TSLA"
    }

    now = datetime.datetime.now(pytz.timezone("Asia/Jerusalem"))

    hour_24 = now.hour
    hour_12 = hour_24 if hour_24 <= 12 else hour_24 - 12
    minute = now.minute
    hour_str = f"{number_to_hebrew_words(hour_12)} וְ{number_to_hebrew_words(minute)} דַקוֹת"

    segment = get_time_segment(now)

    report = f"הִנֵה תְמוּנַת הַשׁוּק נָכוֹן לֵשָעָה {hour_str} {segment}.\n\n"
    results = {}

    for name, ticker in tickers.items():
        try:
            pct, price, trend = get_stock_change(ticker)
            results[name] = {"pct": pct, "price": price, "trend": trend}
        except:
            results[name] = {"pct": None, "price": None, "trend": None}

    open_time = now.replace(hour=9, minute=59)
    close_time = now.replace(hour=17, minute=25)
    ta125 = results["תֵל אָבִיב-125"]
    ta35 = results["תֵל אָבִיב-35"]

    if now < open_time:
        delta = open_time - now
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        report += f"בֵּּיִשְׂרָאֵל:\nבּוּרְסָת תֵל אָבִיב טֶרֶם נִפְתְּחָה וְצָפוּיָה לֵהִיפָּתָח בֵּעוֹד {number_to_hebrew_words(hours)} שָעוֹת וֵ-{number_to_hebrew_words(minutes)} דָקוֹת.\n"
    elif now > close_time:
        verb1 = "עָלָה" if ta125["pct"] > 0 else "יָרָד"
        verb2 = "עָלָה" if ta35["pct"] > 0 else "יָרָד"
        report += f"בֵּיִשְׂרָאֵל:\nהָבּוּרְסָה נִסְגֵרָה.\nמָדָד תֵל אָבִיב-125 {verb1} בֵּ{number_to_hebrew_words(abs(ta125['pct']))} אָחוּז וֵנִנְעָל בֵּרָמָה שֵׁל {number_to_hebrew_words(ta125['price'])} נְקוּדוֹת.\n"
        report += f"מָדָד תֵל אָבִיב-35 {verb2} בֵּ{number_to_hebrew_words(abs(ta35['pct']))} אָחוּז וֵנִנְעָל בֵּרָמָה שֵׁל {number_to_hebrew_words(ta35['price'])} נְקוּדוֹת.\n"
    else:
        report += f"בֵּיִשְׂרָאֵל:\n"
        for name in ["תֵל אָבִיב-125", "תֵל אָבִיב-35"]:
            d = results[name]
            direction = format_direction(d["pct"], d["trend"])
            report += f"מָדָד {name} {direction} בֵּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז וֵעוֹמֵד עָל {number_to_hebrew_words(d['price'])} נְקוּדוֹת.\n"

    ny_open = now.replace(hour=16, minute=30)
    ny_close = now.replace(hour=23, minute=0)
    
    spy_data = results["SPX"]
    qqq_data = results["QQQ"]
    dia_data = results["DIA"]
    iwm_data = results["IWM"]

    indices = {
        "מָדָד הָאֵס אֵנְד פִּי חָמֵש מֵאוֹת": spy_data,
        "הָנָאסְדָק": qqq_data,
        "הָדָאוֹ ג'וֹנְס": dia_data,
        "הָרָאסֵל": iwm_data
    }

    if now < ny_open:
        report += "\nבֵּבּוּרְסוֹת הָעוֹלָם:\nהַבּוּרְסוֹת טֶרֶם נִפְתֵחוּ, הַנְתוּנִים מִתְיַחֲסִים לַמִסְחָר הַמוּקְדָם.\n"
        for name, d in indices.items():
            if d and d["pct"] is not None:
                direction = format_direction(d["pct"], d["trend"])
                report += f"{name} {direction} בֵּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז.\n"
    elif now > ny_close:
        report += "\nבֵּבּוּרְסוֹת הָעוֹלָם:\nהַבּוּרְסוֹת סְגוּרוֹת, הַנְתוּנִים מִתְיַחֲסִים לָמִסְחָר הָמֵאוּחָר.\n"
        for name, d in indices.items():
            if d and d["pct"] is not None:
                direction = format_direction(d["pct"], d["trend"])
                report += f"{name} {direction} בֵּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז.\n"
    else:
        report += "\nבֵּבּוּרְסוֹת הָעוֹלָם:\n"
        for name, d in indices.items():
            if d and d["pct"] is not None and d["price"] is not None:
                direction = format_direction(d["pct"], d["trend"])
                report += f"{name} {direction} בֵּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז וֵעוֹמֵד עָל {number_to_hebrew_words(d['price'])} נְקוּדוֹת.\n"

    # מניות
    stocks = ["אָפֵּל", "אֵנְבִידְיָה", "אָמָזוֹן", "טֵסְלָה"]
    
    report += "\nבֵּשוּק הָמֵנָיוֹת:\n"
    if now < ny_open:
        report += "הָבּוּרְסָה טֵרֵם נִפְתֵחָה, הָנֵתוּנִים מִתְיָחָסִים לָמִסְחָר הָמוּקְדָם.\n"
        for stock in stocks:
            d = results.get(stock)
            if d and d["pct"] is not None:
                direction = format_direction(d["pct"], d["trend"], threshold=5, is_female=True)
                report += f"מֵנָיָת {stock} {direction} בֵּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז.\n"
    elif now > ny_close:
        report += "הָבּוּרְסָה סְגוּרָה, הָנֵתוּנִים מִתְיָחָסִים לָמִסְחָר הָמֵאוּחָר.\n"
        for stock in stocks:
            d = results.get(stock)
            if d and d["pct"] is not None:
                direction = format_direction(d["pct"], d["trend"], threshold=5, is_female=True)
                report += f"מֵנָיָת {stock} {direction} בֵּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז.\n"
    else:
        for stock in stocks:
            d = results.get(stock)
            if d and d["pct"] is not None and d["price"] is not None:
                direction = format_direction(d["pct"], d["trend"], threshold=5, is_female=True)
                report += f"מֵנָיָת {stock} {direction} בֵּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז וֵנִסְחֵרֵת בֵּשָׁעָר שֵׁל {number_to_hebrew_words(d['price'])} דוֹלָר.\n"
                
    # קריפטו וזהב
    report += "\nבֵּגִיזְרָת הָקְרִיפְּטוֹ:\n"
    for name in ["הָבִּיטְקוֹיְן", "הָאִיתֵרְיוּם"]:
        d = results.get(name)
        if d and d["pct"] is not None and d["price"] is not None:
            direction = format_direction(d["pct"], d["trend"], is_female=(name == "הָאִיתֵרְיוּם"))
            report += f"{name} {direction} ב{number_to_hebrew_words(abs(d['pct']))} אָחוּז וֵנִסְחָר בֵּשָׁעָר שֵׁל {number_to_hebrew_words(d['price'])} דוֹלָר.\n"

    report += "\nעוֹד בָּעוֹלָם:\n"
    for name, unit in [("הָזָהָב", "לֵאוֹנְקִיָה"), ("הָנֵפְט", "לֵחָבִית"), ("הָדוֹלָר", "שְׁקָלִים")]:
        d = results.get(name)
        if d and d["pct"] is not None and d["price"] is not None:
            direction = format_direction(d["pct"], d["trend"])
            report += f"{name} {direction} וֵנִמְצָא עָל {number_to_hebrew_words(d['price'])} {unit}.\n"

    return report

def generate_market_text():
    return get_market_report()
