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
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ماده‌های قانونی رو به‌صورت خودکار به شکل «چیپ» مونواسپیس درمی‌آوریم
CITATION_RE = re.compile(r"(ماده\s+[۰-۹\d]+\s+ق\.[آاٱ]\.د\.[مک]\.?)")
OPTION_RE = re.compile(r"^(۱|۲|۳|۴|الف|ب|ج|د)\)\s*(.*)$", re.S)
SOURCE_YEAR_RE = re.compile(r"^\(([^)]+)\)$")

# سلسله‌مراتب توافق‌شده: نوع‌محتوا ← حوزه‌ی حقوقی (درس) ← منبع/مؤلف ← زیربخش
# اختصاصیِ همون منبع (برای دادآفرین: سال و شماره‌آزمون؛ برای عمروانی و
# مشابه: فصل کتاب، مثل «کلیات» - این‌ها چون از پیش مشخص نیستن، در انتهای
# صف (رتبه‌ی پیش‌فرض) قرار می‌گیرن).
# نوعِ آزمون (وکالت/قضاوت/ارشد/...) دیگه هشتگ نمی‌شه؛ چون محتوای درسی
# مستقل از بازارِ هدفِ مؤسسه‌ست. اگر جایی همچین تگی باقی مونده باشه، به
# انتهای صف می‌ره (بدون رتبه‌ی ویژه).
SOURCES = {"دادآفرین", "چتردانش", "عمروانی", "قربانی"}
SUBJECTS = {"مدنی", "تجارت", "جزا", "آیین_دادرسی_مدنی", "آیین_دادرسی_کیفری", "حقوق_اساسی"}
CONTENT_TYPES = {"تست", "تشریحی", "مقاله", "نمودار"}
YEAR_RE = re.compile(r"^(سال)?[۰-۹\d]{4}$")
EXAM_NUM_RE = re.compile(r"^آزمون[۰-۹\d]+$")


def category_rank(tag_name: str) -> int:
    if tag_name in CONTENT_TYPES:
        return 0
    if tag_name in SUBJECTS:
        return 1
    if tag_name in SOURCES:
        return 2
    if YEAR_RE.match(tag_name) or EXAM_NUM_RE.match(tag_name):
        return 3
    return 4


def order_headers(headers):
    return sorted(headers, key=lambda h: category_rank(h.lstrip("#")))


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
    """
    کل فایل رو خط به خط می‌خونه، نه با split ساده. هر بار که یک یا چند خط
    هشتگ/دسته‌بندی به شکل [برچسب] دیده بشه، آن دسته‌بندی برای تمام سوالات
    بعدی فعال می‌ماند تا دسته‌بندی جدیدی ظاهر شود. این کار باگ قدیمی
    (اختصاص هشتگ‌های اشتباه یا از‌دست‌رفتن هشتگ سوال اول/تنها) را رفع می‌کند
    و برای فایلی با هر تعداد سوال (یک تا صدها) درست کار می‌کند.
    برمی‌گرداند: لیستی از (headers, question_text) برای هر سوال.
    """
    with open(filepath, encoding="utf-8") as f:
        lines = f.read().split("\n")

    blocks = []
    header_buffer = []
    active_headers = []
    current_lines = []
    # وقتی True است یعنی اولین خط هشتگ بعدی باید شروع یک دسته‌ی تازه باشد
    # (نه ادامه‌ی دسته‌ی سوال قبلی) — این پرچم دقیقاً همان چیزی است که باگ
    # «تجمیع نامحدود هشتگ‌ها روی هم» را رفع می‌کند.
    expect_new_batch = True

    def flush():
        if current_lines and any("سوال" in ln for ln in current_lines):
            blocks.append((active_headers[:], "\n".join(current_lines).strip()))

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and "]" in stripped:
            flush()
            current_lines = []
            if expect_new_batch:
                header_buffer = []
                expect_new_batch = False
            header_buffer.extend(
                "#" + m.strip() for m in re.findall(r"\[([^\[\]]+)\]", stripped)
            )
            active_headers = header_buffer[:]
        elif re.match(r"^سوال\s", stripped):
            flush()
            current_lines = [line]
            expect_new_batch = True
        else:
            current_lines.append(line)
    flush()
    return blocks


def format_message(question_text, headers):
    lines = question_text.split("\n")
    question_parts = []
    question_number = ""
    options = []
    answer_parts = []
    source_year_line = None
    in_question = False
    in_answer = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("سوال"):
            match = re.match(r'سوال\s+([\u06F0-\u06F9\d]+)\s*[:\-ـ]?\s*(.*)', stripped)
            if match:
                question_number = match.group(1)
                question_parts.append(match.group(2).strip())
            else:
                question_parts.append(stripped.replace("سوال", "", 1).strip())
            in_question, in_answer = True, False
        elif SOURCE_YEAR_RE.match(stripped):
            # خط منبع/سال آزمون، مثل «(قضاوت - ۱۳۸۰)» — می‌تواند قبل یا بعد
            # از گزینه‌ها بیاید؛ جزو متن سؤال نیست، همون‌جوری زیر سؤال
            # داخل پرانتز نمایش داده می‌شود (هشتگ نمی‌شود).
            source_year_line = stripped
            in_question, in_answer = False, False
        elif stripped.startswith("پاسخ:"):
            answer_parts.append(stripped.replace("پاسخ:", "").strip())
            in_question, in_answer = False, True
        elif any(stripped.startswith(ch) for ch in ["۱)", "۲)", "۳)", "۴)", "الف)", "ب)", "ج)", "د)"]):
            options.append(stripped)
            in_question, in_answer = False, False
        elif in_question and stripped:
            question_parts.append(stripped)
        elif in_answer and stripped:
            # خطوط بعدیِ پاسخ چندخطی هم حفظ می‌شوند، نه فقط خط اول
            answer_parts.append(stripped)

    question = highlight_citations(html.escape(" ".join(question_parts)))
    answer = highlight_citations(html.escape(" ".join(answer_parts)))

    message = ""
    if headers:
        message += f"{RLM}│ " + " ".join(order_headers(headers)) + "\n\n"

    message += f"{RLM}│ <b>سوال {question_number}</b>\n"
    message += f"{RLM}<blockquote>{question}</blockquote>\n"
    if source_year_line:
        message += f"{RLM}<code>{html.escape(source_year_line)}</code>\n"
    message += f"\n{RLM}➖➖➖\n\n"

    option_lines = []
    for opt in options:
        m = OPTION_RE.match(opt)
        if m:
            label, body = m.group(1), highlight_citations(html.escape(m.group(2)))
            option_lines.append(f"{RLM}<code>{label})</code> {body}")
        else:
            option_lines.append(f"{RLM}{highlight_citations(html.escape(opt))}")
    message += "\n\n".join(option_lines)
    message += "\n\n"

    # فاصله‌ی خالی قبل از متن پاسخ داخل بلاک‌کوت تاشو، تا در حالت بسته
    # هیچ بخشی از پاسخ بیرون نماند و کاربر مجبور شود برای دیدن آن باز کند.
    fold_padding = "\n" * 3
    short_match = re.match(r"(گزینه\s+(?:[۰-۹\d]+|الف|ب|ج|د)\s+صحیح\s+است\.?)\s*(.*)", answer, re.S)
    if short_match:
        short_answer, rest_answer = short_match.group(1), short_match.group(2).strip()
        # لایه‌ی اول: پاسخ کوتاه به‌شکل اسپویلر (با یک تپ سریع دیده می‌شود)
        message += f"{RLM}│ <b>پاسخ کوتاه:</b> <span class=\"tg-spoiler\">{short_answer}</span>\n"
        # لایه‌ی دوم: استدلال کامل داخل بلاک‌کوت تاشو
        message += (
            f"{RLM}<blockquote expandable>{fold_padding}{rest_answer}</blockquote>"
        )
    else:
        message += (
            f"{RLM}<blockquote expandable>{fold_padding}"
            f"│ <b>پاسخ</b>\n\n{answer}</blockquote>"
        )

    return message


def main():
    if not os.path.exists(QUESTIONS_FILE):
        print(f"فایل {QUESTIONS_FILE} پیدا نشد.")
        sys.exit(1)

    blocks = load_questions(QUESTIONS_FILE)
    print(f"{len(blocks)} سوال پیدا شد.")

    failures = 0
    for i, (headers, text) in enumerate(blocks, 1):
        msg = format_message(text, headers)
        if send_message(msg):
            print(f"سوال {i} ارسال شد ✓")
        else:
            print(f"سوال {i} ناموفق ✗")
            failures += 1
        time.sleep(5)

    if failures:
        print(f"{failures} سوال ناموفق بود.")
        sys.exit(1)


if __name__ == "__main__":
    main()
