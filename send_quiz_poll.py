import os
import sys
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@hajimirzamahmoud")

def main():
    question = os.environ["QUESTION"]
    options = [os.environ[f"OPTION_{l}"] for l in ["A", "B", "C", "D"] if os.environ.get(f"OPTION_{l}")]
    correct_index = int(os.environ["CORRECT_INDEX"])

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    payload = {
        "chat_id": CHANNEL_ID,
        "question": question,
        "options": options,
        "type": "quiz",
        "correct_option_id": correct_index,
        "is_anonymous": True,
    }
    response = requests.post(url, json=payload, timeout=30)
    if not response.ok:
        print(f"خطا: {response.text}")
        sys.exit(1)
    print("کوئیز با موفقیت ارسال شد.")

if __name__ == "__main__":
    main()
