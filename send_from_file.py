import os
import time
import requests
import re

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@hajimirzamahmoud")
QUESTIONS_FILE = "questions.txt"

RLM = "\u200F"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def ensure_foldable(text, pad_lines=3):
    def pad_match(m):
        inner = m.group(1)
        inner = ("\n" * pad_lines) + inner
        return f"<blockquote expandable>{inner}</blockquote>"
    return re.sub(
        r"<blockquote expandable>(.*?)</blockquote>",
        pad_match,
        text,
        flags=re.S,
    )

def send_message(text, retries=3):
    text = ensure_foldable(text)
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    for attempt in range(retries):
        try:
            response = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=30)
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
    blocks = [p.strip() for p in parts if p.strip() and "سوال" in p]
    return blocks

def format_message(block, last_headers=None):
    lines = block.split("\n")
    headers = []
    question_parts = []
    question_number = ""
    options = []
    answer = ""
    in_question = False

    for line in lines:
        if line.startswith("[") and line.endswith("]"):
            headers.append("#" + line.strip("[]").strip())
        elif line.startswith("سوال"):
            match = re.match(r'سوال\s+([\u06F0-\u06F9\d]+)\s*:\s*(.*)', line)
            if match:
                question_number = match.group(1)
                question_parts.append(match.group(2).strip())
            else:
                question_parts.append(line.replace("سوال", "", 1).strip())
            in_question = True
        elif line.startswith("پاسخ:"):
            answer = line.replace("پاسخ:", "").strip()
            in_question = False
        elif any(line.startswith(ch) for ch in ["الف)", "ب)", "ج)", "د)"]):
            options.append(line)
            in_question = False
        elif in_question and line.strip():
            question_parts.append(line.strip())

    question = " ".join(question_parts)

    if not headers and last_headers:
        headers = last_headers

    message = ""
    if headers:
        message += " ".join(headers) + "\n\n"

    message += f"{RLM}<b>{question_number}</b>: {question}\n\n"
    message += "\n\n".join([RLM + opt for opt in options])
    message += f"\n\n{RLM}<blockquote expandable>{question_number}: {answer}</blockquote>"

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
