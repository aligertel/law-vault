import os
import sys
import time
import re
import html
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@hajimirzamahmoud")
QUESTIONS_FILE = os.environ.get("QUESTIONS_FILE", "questions.txt")

RLM = "\u200F"
DIVIDER = "──────────"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ماده‌های قانونی رو به‌صورت خودکار به شکل «چیپ» مونواسپیس درمی‌آوریم
CITATION_RE = re.compile(r"(ماده\s+[۰-۹\d]+\s+ق\.[آاٱ]\.د\.[مک]\.?)")


def highlight_citations(text: str) -> str:
    return CITATION_RE.sub(r"<code>\1</code>", text)


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
            print(f"تلاش {attempt + 1} ناموفق: {e}")
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
    answer_parts = []
    in_question = False
    in_answer = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            headers.append("#" + stripped.strip("[]").strip())
            in_question = in_answer = False
        elif stripped.startswith("سوال"):
            match = re.match(r'سوال\s+([\u06F0-\u06F9\d]+)\s*[:\-ـ]?\s*(.*)', stripped)
            if match:
                question_number = match.group(1)
                question_parts.append(match.group(2).strip())
            else:
                question_parts.append(stripped.replace("سوال", "", 1).strip())
            in_question, in_answer = True, False
        elif stripped.startswith("پاسخ:"):
            answer_parts.append(stripped.replace("پاسخ:", "").strip())
            in_question, in_answer = False, True
        elif any(stripped.startswith(ch) for ch in ["الف)", "ب)", "ج)", "د)"]):
            options.append(stripped)
            in_question, in_answer = False, False
        elif in_question and stripped:
            question_parts.append(stripped)
        elif in_answer and stripped:
            # رفع باگ: خطوط بعدیِ پاسخ چندخطی هم حفظ می‌شوند، نه فقط خط اول
            answer_parts.append(stripped)

    if not headers and last_headers:
        headers = last_headers

    question = html.escape(" ".join(question_parts))
    answer = html.escape(" ".join(answer_parts))
    options_escaped = [html.escape(opt) for opt in options]

    question = highlight_citations(question)
    answer = highlight_citations(answer)

    message = ""
    if headers:
        message += " ".join(headers) + "\n\n"

    message += f"{RLM}❓ <code>سوال {question_number}</code>\n"
    message += f"{RLM}<b>{question}</b>\n\n"
    message += "\n".join([RLM + opt for opt in options_escaped])
    message += f"\n\n{RLM}{DIVIDER}\n"
    message += f"{RLM}<blockquote expandable>✅ <b>پاسخ</b>\n\n{answer}</blockquote>"

    return message, headers


def main():
    if not os.path.exists(QUESTIONS_FILE):
        print(f"فایل {QUESTIONS_FILE} پیدا نشد.")
        sys.exit(1)

    blocks = load_questions(QUESTIONS_FILE)
    print(f"{len(blocks)} سوال پیدا شد.")

    last_headers = None
    failures = 0
    for i, block in enumerate(blocks, 1):
        msg, headers = format_message(block, last_headers)
        if headers:
            last_headers = headers
        if send_message(msg):
            print(f"سوال {i} ارسال شد ✓")
        else:
            print(f"سوال {i} ناموفق ✗")
            failures += 1
        time.sleep(5)

    if failures:
        print(f"{failures} سوال ناموفق بود.")
        sys.exit(1)  # رفع باگ: حالا شکست واقعاً به CI گزارش می‌شود


if __name__ == "__main__":
    main()
