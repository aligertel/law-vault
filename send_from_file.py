import os
import time
import requests
import re

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@hajimirzamahmoud")
QUESTIONS_FILE = "questions.txt"

RLM = "\u200F"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

EXPLANATION_TEXT = "بریم پاسخ رو با هم ببینیم."

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

def send_poll(question, options, correct_index):
    url = f"{API_URL}/sendPoll"
    payload = {
        "chat_id": CHANNEL_ID,
        "question": question[:300],
        "options": [opt[:100] for opt in options],
        "type": "quiz",
        "correct_option_id": correct_index,
        "explanation": EXPLANATION_TEXT[:200],
        "is_anonymous": True,
    }
    response = requests.post(url, json=payload, timeout=30)
    if not response.ok:
        print(f"خطای پُل: {response.text}")
        return None
    return response.json().get("result", {}).get("message_id")

def send_reply(text, reply_to_message_id, retries=3):
    text = ensure_foldable(text)
    url = f"{API_URL}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_parameters": {"message_id": reply_to_message_id},
    }
    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 429:
                retry = response.json().get("parameters", {}).get("retry_after", 5)
                time.sleep(retry + 1)
                continue
            if not response.ok:
                print(f"خطای ریپلای: {response.text}")
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

def format_poll_data(block):
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
            opt_text = re.sub(r'^(الف|ب|ج|د)\)\s*', '', line)
            options.append(opt_text)
            in_question = False
        elif in_question and line.strip():
            question_parts.append(line.strip())

    question = " ".join(question_parts)

    return headers, question_number, question, options, answer

def find_correct_index(answer):
    match = re.search(r'گزینه\s+([۱-۴1-4])', answer)
    if match:
        num = match.group(1)
        mapping = {"۱": 0, "۲": 1, "۳": 2, "۴": 3,
                   "1": 0, "2": 1, "3": 2, "4": 3}
        return mapping.get(num, 0)
    return 0

def main():
    blocks = load_questions(QUESTIONS_FILE)
    print(f"{len(blocks)} سوال پیدا شد.")
    last_headers = None
    for i, block in enumerate(blocks, 1):
        headers, q_num, question, options, answer = format_poll_data(block)
        if not headers and last_headers:
            headers = last_headers
        if headers:
            last_headers = headers

        poll_question = f"{q_num}: {question}"

        if len(options) != 4:
            print(f"سوال {i}: تعداد گزینه‌ها {len(options)} است — رد شد.")
            continue

        correct_index = find_correct_index(answer)

        poll_msg_id = send_poll(poll_question, options, correct_index)
        if poll_msg_id:
            print(f"سوال {i}: پُل ارسال شد ✓")
            time.sleep(3)

            hashtag_text = " ".join(headers) if headers else ""
            reply_text = f"{hashtag_text}\n\n<blockquote expandable>{answer}</blockquote>"

            if send_reply(reply_text, poll_msg_id):
                print(f"سوال {i}: پاسخ تاشو ارسال شد ✓")
            else:
                print(f"سوال {i}: پاسخ تاشو ناموفق ✗")
        else:
            print(f"سوال {i}: پُل ناموفق ✗")
        time.sleep(5)

if __name__ == "__main__":
    main()
