import os
import re
import sys
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@hajimirzamahmoud")

# تلگرام فقط وقتی فلش «تاشو» رو روی <blockquote expandable> نشون میده که
# محتوا بیشتر از حدود ۳ خط نمایشی باشه. برای پاسخ‌های کوتاه (که تاشو لازم
# دارن ولی طولشون کمه)، چند خط خالی قبل از متن اضافه می‌کنیم تا خط‌های
# نمایشی از حد بگذره و فلش تاشو ظاهر بشه.
def ensure_foldable(text, min_lines=4, pad_lines=3, chars_per_line=40):
    def pad_match(m):
        inner = m.group(1)
        approx_lines = inner.count("\n") + 1 + len(inner) // chars_per_line
        if approx_lines < min_lines:
            inner = ("\n" * pad_lines) + inner
        return f"<blockquote expandable>{inner}</blockquote>"

    return re.sub(
        r"<blockquote expandable>(.*?)</blockquote>",
        pad_match,
        text,
        flags=re.S,
    )

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    response = requests.post(url, json=payload, timeout=30)
    if not response.ok:
        err = response.text.replace("\n", " ")[:500]
        print(f"::error::Telegram API error: {err}")
        sys.exit(1)
    print("پیام با موفقیت ارسال شد.")

if __name__ == "__main__":
    message_text = os.environ.get("MESSAGE_TEXT")
    if not message_text:
        print("::error::متنی برای ارسال داده نشده (MESSAGE_TEXT خالیه).")
        sys.exit(1)
    message_text = ensure_foldable(message_text)
    send_message(message_text)
