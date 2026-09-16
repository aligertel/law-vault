import os
import sys
import time
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@hajimirzamahmoud")
QUESTIONS_FILE = "questions_expandable.txt"

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_message(text):
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    response = requests.post(API_URL, json=payload, timeout=30)
    if response.status_code == 429:
        retry = response.json().get("parameters", {}).get("retry_after", 5)
        time.sleep(retry + 1)
        return send_message(text)
    if not response.ok:
        print(f"خطا: {response.text}")
        return False
    return True

def load_questions(filepath):
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
    blocks = []
    current = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("سوال") and any(l.startswith("سوال") for l in current):
            blocks.append("\n".join(current))
            current = []
        current.append(stripped)
    if current:
        blocks.append("\n".join(current))
    return blocks

def format_message(block):
    lines = block.split("\n")
    headers = []
    question = ""
    options = []
    answer = ""
    for line in lines:
        if line.startswith("[") and line.endswith("]"):
            headers.append("#" + line.strip("[]").strip())
        elif line.startswith("سوال"):
            question = line
        elif line.startswith("پاسخ:"):
            answer = line.replace("پاسخ:", "").strip()
        elif any(line.startswith(ch) for ch in ["الف)", "ب)", "ج)", "د)"]):
            options.append(line)
    message = ""
    if headers:
        message += " ".join(headers) + "\n\n"
    message += f"<b>{question}</b>\n\n"
    message += "\n".join(options)
    message += f"\n\n<blockquote expandable>پاسخ: {answer}</blockquote>"
    return message

def main():
    blocks = load_questions(QUESTIONS_FILE)
    print(f"{len(blocks)} سوال پیدا شد.")
    for i, block in enumerate(blocks, 1):
        msg = format_message(block)
        if send_message(msg):
            print(f"سوال {i} ارسال شد ✓")
        else:
            print(f"سوال {i} ناموفق ✗")
        time.sleep(2)

if __name__ == "__main__":
    main()
