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
        return f"{hour_word} וְ{minute_word} ד
