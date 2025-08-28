# -*- coding: utf-8 -*-
import yfinance as yf
import datetime
import pytz
from num2words import num2words

def number_to_hebrew_words(number):
    """
    ממיר מספר למילים בעברית, כולל עבור מספרים עשרוניים.
    לדוגמה, 12.34 הופך ל-'שתיים עשרה נקודה שלוש ארבע'.
    """
    parts = str(round(number, 2)).split(".")
    if len(parts) == 1:
        return num2words(int(parts[0]), lang='he')
    else:
        integer_part = num2words(int(parts[0]), lang='he')
        decimal_part_str = parts[1]
        
        # ממיר כל ספרה בחלק העשרוני למילה
        hebrew_decimal_parts = []
        for digit in decimal_part_str:
            hebrew_decimal_parts.append(num2words(int(digit), lang='he'))
        decimal_part_hebrew = " ".join(hebrew_decimal_parts)

        return f"{integer_part} נקודה {decimal_part_hebrew}"

def get_time_segment(now):
    """
    מחזיר את מקטע הזמן ביום בעברית.
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

def get_ticker_data(ticker):
    """
    מושך נתונים לטיקר מ-Yahoo Finance.
    מטפל בנתוני מסחר מוקדם/מאוחר.
    """
    stock = yf.Ticker(ticker)
    info = stock.info
    
    is_pre_market = False
    is_after_hours = False
    
    try:
        # בודק אם יש מסחר מחוץ לשעות
        if info.get('preMarketPrice') is not None and info.get('regularMarketPrice') is not None and info.get('marketState') == 'PRE':
            current_price = info['preMarketPrice']
            prev_close = info['regularMarketPrice']
            is_pre_market = True
        elif info.get('postMarketPrice') is not None and info.get('regularMarketPrice') is not None and info.get('marketState') == 'POST':
            current_price = info['postMarketPrice']
            prev_close = info['regularMarketPrice']
            is_after_hours = True
        else:
            current_price = info.get('regularMarketPrice')
            prev_close = info.get('previousClose')

        if current_price is None or prev_close is None:
            raise ValueError("Price data not available")

        pct_change = ((current_price - prev_close) / prev_close) * 100
        return round(pct_change, 2), round(current_price, 2), None, is_pre_market, is_after_hours
        
    except (KeyError, IndexError, TypeError, ValueError):
        # אם אין נתוני מסחר בזמן אמת, נשתמש בנתונים היסטוריים
        try:
            hist = stock.history(period="5d", interval="1d")
            if len(hist) < 2:
                return None, None, None, False, False
            
            current_price = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2]
            
            # חישוב טרנד
            trend = None
            if len(hist) >= 3:
                before_prev = hist["Close"].iloc[-3]
                if current_price > prev_close > before_prev:
                    trend = "מַמְשִׁיךְ לַעֲלוֹת"
                elif current_price < prev_close < before_prev:
                    trend = "מַמְשִׁיךְ לְרֶדֶת"
            
            pct_change = ((current_price - prev_close) / prev_close) * 100
            return round(pct_change, 2), round(current_price, 2), trend, False, False
        except:
            return None, None, None, False, False

def format_direction(pct, trend, threshold=1.5, is_female=False):
    """
    מעצב את כיוון השינוי בעברית.
    """
    if pct is None:
        return "לא זמין"
    if trend:
        base = trend
    else:
        if abs(pct) >= threshold:
            base = "עוֹלֶה בְּצוּרָה דְרָמָטִית" if pct > 0 else "יוֹרֵד בְּצוּרָה דְרָמָטִית"
        else:
            base = "עוֹלֶה" if pct > 0 else "יוֹרֵד"
    
    if is_female:
        base = base.replace("עוֹלֶה", "עוֹלָה").replace("יוֹרֵד", "יוֹרֶדֶת").replace("מַמְשִׁיךְ", "מַמְשִׁיכָה")
    return base

def get_market_report():
    """
    מייצר טקסט של דוח שוק מלא.
    """
    # הגדרת הטיקרים למדדים ותעודות סל
    indices_tickers = {
        "מדד האס אנד פי חמש מאות": "^GSPC",
        "הנאסדק": "^IXIC",
        "הדאו ג'ונס": "^DJI",
        "הראסל": "^RUT"
    }
    etf_tickers = {
        "מדד האס אנד פי חמש מאות": "SPY",
        "הנאסדק": "QQQ",
        "הדאו ג'ונס": "DIA",
        "הראסל": "IWM"
    }

    # יצירת מילון עם כל הטיקרים הדרושים
    all_tickers = {
        **indices_tickers,
        **etf_tickers,
        "תֵל אָבִיב-125": "^TA125.TA",
        "תֵל אָבִיב-35": "TA35.TA",
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

    # הגדרת אזורי זמן
    tel_aviv_tz = pytz.timezone("Asia/Jerusalem")
    ny_tz = pytz.timezone("America/New_York")
    now_ta = datetime.datetime.now(tel_aviv_tz)
    now_ny = now_ta.astimezone(ny_tz)

    # זמני פתיחה וסגירה של הבורסה בתל אביב
    ta_open = now_ta.replace(hour=9, minute=59)
    ta_close = now_ta.replace(hour=17, minute=25)
    
    # זמני פתיחה וסגירה של הבורסה בניו יורק
    ny_open = now_ny.replace(hour=9, minute=30)
    ny_close = now_ny.replace(hour=16, minute=0)

    # בדיקה האם הבורסה האמריקאית פתוחה
    is_ny_open = ny_open.date() == now_ny.date() and ny_open <= now_ny <= ny_close

    # בניית הכותרת עם השעה והתאריך
    hour_str = number_to_hebrew_words(now_ta.hour)
    minute_str = number_to_hebrew_words(now_ta.minute)
    time_segment = get_time_segment(now_ta)
    
    # שינוי פורמט הזמן לדוגמה: שבע וחמישים דקות
    report = f"הִנֵה תְמוּנַת הַשׁוּק נָכוֹן לְשָׁעָה {hour_str} וְ{minute_str} דַקוֹת {time_segment}.\n\n"

    results = {}
    for name, ticker in all_tickers.items():
        # עבור מדדים ותעודות סל בארה"ב, נבחר את הטיקר המתאים
        if name in indices_tickers.keys():
            if is_ny_open:
                ticker_to_fetch = indices_tickers[name]
                is_index = True
            else:
                ticker_to_fetch = etf_tickers[name]
                is_index = False
        else:
            ticker_to_fetch = ticker
            is_index = False

        try:
            pct, price, trend, is_pre_market, is_after_hours = get_ticker_data(ticker_to_fetch)
            results[name] = {"pct": pct, "price": price, "trend": trend, "is_pre_market": is_pre_market, "is_after_hours": is_after_hours, "is_index": is_index}
        except:
            results[name] = {"pct": None, "price": None, "trend": None, "is_pre_market": False, "is_after_hours": False, "is_index": is_index}

    # דיווח על בורסת תל אביב
    ta125 = results["תֵל אָבִיב-125"]
    ta35 = results["תֵל אָבִיב-35"]
    
    report += "בְּיִשְׂרָאֵל:\n"
    if now_ta < ta_open:
        delta = ta_open - now_ta
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        report += f"בּוּרְסַת תֵל אָבִיב טֶרֶם נִפְתְּחָה וְצָפוּיָה לְהִיפָּתַח בְּעוֹד {number_to_hebrew_words(hours)} שָׁעוֹת וְ{number_to_hebrew_words(minutes)} דַקוֹת.\n"
    elif now_ta > ta_close:
        verb1 = "עָלָה" if ta125["pct"] > 0 else "יָרָד"
        verb2 = "עָלָה" if ta35["pct"] > 0 else "יָרָד"
        report += f"הַבּוּרְסָה נִסְגְּרָה.\nמַדַּד תֵל אָבִיב-125 {verb1} בְּ{number_to_hebrew_words(abs(ta125['pct']))} אָחוּז וְנִנְעַל בְּרָמָה שֶׁל {number_to_hebrew_words(ta125['price'])} נְקוּדוֹת.\n"
        report += f"מַדַּד תֵל אָבִיב-35 {verb2} בְּ{number_to_hebrew_words(abs(ta35['pct']))} אָחוּז וְנִנְעַל בְּרָמָה שֶׁל {number_to_hebrew_words(ta35['price'])} נְקוּדוֹת.\n"
    else:
        for name in ["תֵל אָבִיב-125", "תֵל אָבִיב-35"]:
            d = results[name]
            direction = format_direction(d["pct"], d["trend"])
            report += f"מַדַּד {name} {direction} בְּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז וְעוֹמֵד עַל {number_to_hebrew_words(d['price'])} נְקוּדוֹת.\n"

    # דיווח על בורסות העולם (ארה"ב)
    report += "\nבְּבּוּרְסוֹת הָעוֹלָם:\n"
    if is_ny_open:
        report += "הַבּוּרְסוֹת פְּתוּחוֹת כָּעֵת לְמִסְחָר.\n"
    elif now_ny < ny_open:
        report += f"הַבּוּרְסוֹת טֶרֶם נִפְתְּחוּ, הַנְּתוּנִים מִתְיַחֲסִים לַמִסְחָר הַמּוּקְדָם לְפִי מָה שֶׁנִּרְשָׁם בְּתְעוּדוֹת הַסַּל שֶׁעוֹקְבוֹת אַחֲרֵי הַמְּדַדִּים.\n"
    else:
        report += "הַבּוּרְסוֹת נִסְגְּרוּ, הַנְּתוּנִים מִתְיַחֲסִים לַמִסְחָר הַמְּאֻחָר לְפִי מָה שֶׁנִּרְשָׁם בְּתְעוּדוֹת הַסַּל שֶׁעוֹקְבוֹת אַחֲרֵי הַמְּדַדִּים.\n"

    for name in indices_tickers.keys():
        d = results[name]
        direction = format_direction(d["pct"], d["trend"])
        if d['is_index']:
            unit = "נְקוּדוֹת"
        else:
            unit = "דוֹלָר"
        report += f"{name} {direction} בְּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז וְעוֹמֵד עַל {number_to_hebrew_words(d['price'])} {unit}.\n"
    
    # דיווח על מניות
    stocks = ["אָפֵּל", "אֵנְבִידְיָה", "אָמָזוֹן", "טֵסְלָה"]
    report += "\nבְּשׁוּק הַמְּנָיוֹת:\n"
    for stock in stocks:
        d = results[stock]
        direction = format_direction(d["pct"], d["trend"], threshold=5, is_female=True)
        report += f"מְנָיַת {stock} {direction} בְּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז וְנִסְחֶרֶת בְּשַׁעַר שֶׁל {number_to_hebrew_words(d['price'])} דוֹלָר.\n"

    # דיווח על קריפטו, זהב, נפט ודולר
    report += "\nבְּגִזְרַת הַקְּרִיפְּטוֹ:\n"
    for name in ["הָבִּיטְקוֹיְן", "הָאִיתֵרְיוּם"]:
        d = results[name]
        direction = format_direction(d["pct"], d["trend"], is_female=(name == "הָאִיתֵרְיוּם"))
        report += f"{name} {direction} בְּ{number_to_hebrew_words(abs(d['pct']))} אָחוּז וְנִסְחָר בְּשַׁעַר שֶׁל {number_to_hebrew_words(d['price'])} דוֹלָר.\n"

    report += "\nעוֹד בָּעוֹלָם:\n"
    for name, unit in [("הָזָהָב", "לְאוֹנְקִיָּה"), ("הָנֵפְט", "לְחָבִית"), ("הָדוֹלָר", "שְׁקָלִים")]:
        d = results[name]
        direction = format_direction(d["pct"], d["trend"])
        report += f"{name} {direction} וְנִמְצָא עַל {number_to_hebrew_words(d['price'])} {unit}.\n"

    return report

def generate_market_text():
    return get_market_report()
