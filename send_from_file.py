import os
import time
import requests
import re

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@hajimirzamahmoud")
QUESTIONS_FILE = "questions.txt"

RLM = "\u200F"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_message(text, retries=3):
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    for attempt in range(retries):
        try:
            response = requests.post(API_URL, json=payload, timeout=30)
            if response.status_code == 429:
                retry = response.json().get("parameters", {}).get("retry_after", 5)
                time.sleep(retry + 1)
                continue
            if not response.ok:
                print(f"خطا: {response.text}")
                return False
            return True
        except requests.exceptions.RequestException as e:
            print(f"تلاش {attempt+1} ناموفق: {e}")
            time.sleep(5)
    return False

def load_questions(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    parts = re.split(r'\n(?=سوال\s)', content)
    blocks = []
    for p in parts:
        p = p.strip()
        if p and "سوال" in p:
            blocks.append(p)
    return blocks

def format_message(block, last_headers=None):
    lines = block.split("\n")
    headers = []
    question = ""
    question_number = ""
    options = []
    answer = ""
    for line in lines:
        if line.startswith("[") and line.endswith("]"):
            headers.append("#" + line.strip("[]").strip())
        elif line.startswith("سوال"):
            match = re.match(r'سوال\s+([\u06F0-\u06F9\d]+)\s*:\s*(.*)', line)
            if match:
                question_number = match.group(1)
                question = match.group(2).strip()
            else:
                question = line.replace("سوال", "", 1).strip()
        elif line.startswith("پاسخ:"):
            answer = line.replace("پاسخ:", "").strip()
        elif any(line.startswith(ch) for ch in ["الف)", "ب)", "ج)", "د)"]):
            options.append(line)

    if not headers and last_headers:
        headers = last_headers

    message = ""
    if headers:
        message += " ".join(headers) + "\n\n"

    message += f"{RLM}<b>{question_number}</b>: {question}\n\n"
    message += "\n\n".join([RLM + opt for opt in options])
    message += f"\n\n{RLM}<blockquote expandable><b>{question_number}</b>: {answer}</blockquote>"

    return message, headers

def main():
    blocks = load_questions(QUESTIONS_FILE)
    print(f"{len(blocks)} سوال پیدا شد.")
    last_headers = None
    for i, block in enumerate(blocks, 1):
        msg, headers = format_message(block, last_headers)
        if headers:
            last_headers = headers
        if send_message(msg):
            print(f"سوال {i} ارسال شد ✓")
        else:
            print(f"سوال {i} ناموفق ✗")
        time.sleep(5)

if __name__ == "__main__":
    main()
