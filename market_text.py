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
        # חילוץ ספרה אחת אחרי הנקודה
        frac_digit = int(round(abs(val) * 10)) % 10
        integer_words = num2words(integer_part, lang='he')
        if frac_digit == 0:
            return integer_words
        decimal_words = num2words(frac_digit, lang='he')
        return f"{integer_words} נְקוּדָה {decimal_words}"

    # 1–2 ספרות: כמו קודם (עד שתי ספרות עשרוניות)
    rounded_number = round(number, 2)
    integer_part_str, decimal_pa_
