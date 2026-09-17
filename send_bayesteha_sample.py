import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = "@hajimirzamahmoud"

with open("bayesteha_sample_payload.txt", encoding="utf-8") as f:
    text = f.read()

resp = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
    timeout=30,
)

with open("debug_output3.txt", "w", encoding="utf-8") as f:
    f.write(f"STATUS: {resp.status_code}\n\n{resp.text}")
