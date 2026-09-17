import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = "@hajimirzamahmoud"

text = """<b>سوال ۱: اگر کسی در نتیجه‌ی اضطراری و برای جلوگیری از ضرر بزرگ‌تر، ناگزیر شود که ضرری به مال غیر وارد کند، کدام گزینه در مورد این فرض صحیح است؟</b>

الف) اگر حسن برای دفع ضرر از خود یا سپیده، ناگزیر شود به کامبیز اضرار کند، در مقابل کامبیز مسئول نیست.
ب) اگر حسن برای دفع ضرر از خود یا سپیده یا کامبیز، ناگزیر شود به کامبیز اضرار کند، در مقابل کامبیز مسئول نیست.
ج) اگر حسن برای دفع ضرر از سپیده یا کامبیز، ناگزیر شود به کامبیز اضرار کند، در مقابل کامبیز مسئول نیست.
د) اگر حسن برای دفع ضرر از کامبیز، ناگزیر شود به کامبیز اضرار کند، در مقابل کامبیز مسئول نیست.

<blockquote expandable>پاسخ: گزینه ۴ صحیح است. اضطرار اصولاً رافع مسئولیت مدنی نیست.</blockquote>"""

resp = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
    timeout=30,
)

with open("debug_output2.txt", "w", encoding="utf-8") as f:
    f.write(f"STATUS: {resp.status_code}\n\n")
    f.write(resp.text)
