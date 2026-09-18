import os
import sys
import time
import re
import html
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@hajimirzamahmoud")
QUESTIONS_FILE = os.environ.get("QUESTIONS_FILE", "test_questions.txt")

RLM = "\u200F"
SEND_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
POLL_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"

CITATION_RE = re.compile(r"(ماده\s+[۰-۹\d]+\s+ق\.[آاٱ]\.د\.[مک]\.?)")
OPTION_RE = re.compile(r"^([۱۲۳۴])\)\s*(.*)$", re.S)


def highlight_citations(text, wrap="code"):
    if wrap == "clip":
        return CITATION_RE.sub(r"📎 <code>\1</code>", text)
    return CITATION_RE.sub(r"<code>\1</code>", text)


def send_message(text):
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(SEND_URL, json=payload, timeout=30)
        if not r.ok:
            print("خطا:", r.text)
        return r.ok
    except requests.exceptions.RequestException as e:
        print("خطای شبکه (send_message):", e)
        return False


def send_label(text):
    """یه پیام برچسب ساده قبل از هر نمونه، تا تو تلگرام از هم جدا باشن."""
    send_message(f"{RLM}<b>—  {text}  —</b>")


def send_quiz_poll(question, options, correct_index):
    payload = {
        "chat_id": CHANNEL_ID,
        "question": question[:290],
        "options": [o[:100] for o in options],
        "type": "quiz",
        "correct_option_id": correct_index,
        "is_anonymous": True,
    }
    try:
        r = requests.post(POLL_URL, json=payload, timeout=30)
        if not r.ok:
            print("خطا (poll):", r.text)
        return r.ok
    except requests.exceptions.RequestException as e:
        print("خطای شبکه (poll):", e)
        return False


def load_one_question(filepath):
    """اولین سؤال فایل تستی رو پارس می‌کنه و اجزاش رو برمی‌گردونه."""
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    headers = ["#" + m.strip() for m in re.findall(r"\[([^\[\]]+)\]", text)]
    lines = text.split("\n")

    question_parts, options, answer_parts = [], [], []
    question_number = ""
    in_question = in_answer = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            continue
        if stripped.startswith("سوال"):
            m = re.match(r'سوال\s+([\u06F0-\u06F9\d]+)\s*[:\-ـ]?\s*(.*)', stripped)
            if m:
                question_number = m.group(1)
                question_parts.append(m.group(2).strip())
            in_question, in_answer = True, False
        elif stripped.startswith("پاسخ:"):
            answer_parts.append(stripped.replace("پاسخ:", "").strip())
            in_question, in_answer = False, True
        elif any(stripped.startswith(ch) for ch in ["۱)", "۲)", "۳)", "۴)"]):
            options.append(stripped)
            in_question, in_answer = False, False
        elif in_question and stripped:
            question_parts.append(stripped)
        elif in_answer and stripped:
            answer_parts.append(stripped)

    question = " ".join(question_parts)
    answer = " ".join(answer_parts)
    return headers, question_number, question, options, answer


# ---------------------------------------------------------------------------
# نسخه‌ی الف: خط جداکننده‌ی ➖➖➖ + برچسب سطح سختی 🔰/▪️/🔺 + ارجاع با 📎
# ---------------------------------------------------------------------------
def variant_a(headers, number, question, options, answer):
    q = highlight_citations(html.escape(question), wrap="clip")
    msg = f"{RLM}🔺 " + " ".join(headers) + "\n\n"
    msg += f"{RLM}<b>سوال {number}</b>\n"
    msg += f"{RLM}<blockquote>{q}</blockquote>\n\n"
    msg += f"{RLM}➖➖➖\n\n"
    for opt in options:
        m = OPTION_RE.match(opt)
        label, body = m.group(1), highlight_citations(html.escape(m.group(2)), wrap="clip")
        msg += f"{RLM}<code>{label})</code> {body}\n\n"
    short_match = re.match(r"(گزینه\s+[۰-۹\d]+\s+صحیح\s+است\.?)\s*(.*)", answer, re.S)
    short, rest = (short_match.group(1), short_match.group(2).strip()) if short_match else (answer, "")
    msg += f"{RLM}پاسخ: <span class=\"tg-spoiler\">{highlight_citations(html.escape(short), wrap='clip')}</span>\n"
    if rest:
        msg += f"{RLM}<blockquote expandable>\n\n\n{highlight_citations(html.escape(rest), wrap='clip')}</blockquote>"
    return msg


# ---------------------------------------------------------------------------
# نسخه‌ی ب: پاسخ سه‌لایه — اسپویلر کوتاه ← اکسپندبل «راهنما» ← اکسپندبل «استدلال کامل»
# ---------------------------------------------------------------------------
def variant_b(headers, number, question, options, answer):
    q = highlight_citations(html.escape(question))
    msg = f"{RLM}│ " + " ".join(headers) + "\n\n"
    msg += f"{RLM}│ <b>سوال {number}</b>\n"
    msg += f"{RLM}<blockquote>{q}</blockquote>\n\n"
    for opt in options:
        m = OPTION_RE.match(opt)
        label, body = m.group(1), highlight_citations(html.escape(m.group(2)))
        msg += f"{RLM}<code>{label})</code> {body}\n\n"

    short_match = re.match(r"(گزینه\s+[۰-۹\d]+\s+صحیح\s+است\.?)\s*(.*)", answer, re.S)
    short, rest = (short_match.group(1), short_match.group(2).strip()) if short_match else (answer, "")
    hint = rest.split("۔")[0][:70] + "…" if len(rest) > 70 else rest
    msg += f"{RLM}│ <b>پاسخ کوتاه:</b> <span class=\"tg-spoiler\">{highlight_citations(html.escape(short))}</span>\n\n"
    msg += f"{RLM}<blockquote expandable>{RLM}<b>راهنما</b>\n{highlight_citations(html.escape(hint))}</blockquote>\n\n"
    msg += f"{RLM}<blockquote expandable>\n\n\n<b>استدلال کامل</b>\n\n{highlight_citations(html.escape(rest))}</blockquote>"
    return msg


# ---------------------------------------------------------------------------
# نسخه‌ی ج: پست معرفیِ 📂 قبل از سؤال (شبیه باز کردن یه پرونده‌ی جدید)
# ---------------------------------------------------------------------------
def variant_c_intro(headers):
    msg = f"{RLM}📂 <b>شروع مجموعه</b>\n"
    msg += f"{RLM}" + " ".join(headers) + "\n"
    msg += f"{RLM}<i>سؤالات این بخش از همین‌جا شروع می‌شود.</i>"
    return msg


def main():
    headers, number, question, options, answer = load_one_question(QUESTIONS_FILE)

    try:
        send_label("نسخه‌ی الف: جداکننده ➖ + 🔺 + ارجاع با 📎")
        send_message(variant_a(headers, number, question, options, answer))
        time.sleep(3)
    except Exception as e:
        print("خطا در نسخه‌ی الف:", e)

    try:
        send_label("نسخه‌ی ب: پاسخ سه‌لایه (کوتاه ← راهنما ← استدلال کامل)")
        send_message(variant_b(headers, number, question, options, answer))
        time.sleep(3)
    except Exception as e:
        print("خطا در نسخه‌ی ب:", e)

    try:
        send_label("نسخه‌ی ج: پست معرفیِ 📂 قبل از شروع یک بخش")
        send_message(variant_c_intro(headers))
        time.sleep(3)
    except Exception as e:
        print("خطا در نسخه‌ی ج:", e)

    try:
        send_label("نسخه‌ی د: همون سؤال به شکل Quiz Poll واقعی تلگرام")
        opt_bodies = [OPTION_RE.match(opt).group(2).strip() for opt in options]
        persian_to_latin = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
        correct_num_match = re.search(r"گزینه\s+([۰-۹\d])\s+صحیح", answer)
        correct_index = 0
        if correct_num_match:
            correct_index = int(correct_num_match.group(1).translate(persian_to_latin)) - 1
        send_quiz_poll(f"سوال {number}: {question}", opt_bodies, correct_index)
    except Exception as e:
        print("خطا در نسخه‌ی د:", e)


if __name__ == "__main__":
    main()
