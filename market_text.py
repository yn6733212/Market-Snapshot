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
        return "בָּבּוֹקֵר"
    elif 12 <= hour < 18:
        return "בָּצֹהֹרָיִים"
    elif 18 <= hour < 23:
        return "בָּעֵרֵב"
    else:
        return "בָּלָיְלָה"

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
        trend = "מַמְשִׁיךְ לַעֲלוֹת"
    elif current < prev < before_prev:
        trend = "מַמְשִׁיךְ לְרֶדֶת"
    return round(pct, 2), round(current, 2), trend

def format_direction(pct, trend, threshold=1.5, is_female=False):
    if pct is None:
        return "לא זמין"
    if trend:
        base = trend
    else:
        if abs(pct) >= threshold:
            base = "עוֹלֶה בֵּצוּרָה דְרָמָטִית" if pct > 0 else "יוֹרֵד בְּצוּרָה דְרָמָטִית"
        else:
            base = "עוֹלֵה" if pct > 0 else "יוֹרֵד"
    if is_female:
        base = base.replace("עוֹלֶה", "עוֹלָה").replace("יוֹרֵד", "יוֹרֶדֶת").replace("מַמְשִׁיךְ", "מַמְשִׁיכָה")
    return base

def get_market_report():
    tickers = {
        "תֵל אָבִיב-125": "^TA125.TA",
        "תֵל אָבִיב-35": "TA35.TA",
        "SPY": "SPY",
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
    hour_str = now.strftime("%H:%M")
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

    if now < open_time
