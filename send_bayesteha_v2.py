import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = "@hajimirzamahmoud"

with open("bayesteha_sample_v2_payload.txt", encoding="utf-8") as f:
    text = f.read()

payload = {
    "chat_id": CHAT_ID,
    "text": text,
    "parse_mode": "HTML",
    "reply_markup": {
        "inline_keyboard": [
            [{"text": "📖 مشاهده کامل در دفترچه", "url": "https://aligertel.github.io/law-vault/"}]
        ]
    },
}

resp = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json=payload,
    timeout=30,
)

with open("debug_output4.txt", "w", encoding="utf-8") as f:
    f.write(f"STATUS: {resp.status_code}\n\n{resp.text}")
