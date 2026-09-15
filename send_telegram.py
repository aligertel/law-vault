import os
import sys
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@hajimirzamahmoud")

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    response = requests.post(url, json=payload, timeout=30)
    if not response.ok:
        print(f"خطا: {response.text}")
        sys.exit(1)
    print("پیام با موفقیت ارسال شد.")

if __name__ == "__main__":
    message_text = os.environ.get("MESSAGE_TEXT")
    if not message_text:
        print("متنی برای ارسال داده نشده (MESSAGE_TEXT خالیه).")
        sys.exit(1)
    send_message(message_text)
