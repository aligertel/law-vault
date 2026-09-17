import os
import html
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@hajimirzamahmoud")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

RLM = "\u200F"

columns = {
    "لازم": [
        "عقد موجد حق انتفاع (به‌جز حق ارتفاق)",
        "عقد موجد حق ارتفاق",
        "وقف", "بیع", "معاوضه", "اجاره", "مزارعه", "مساقات", "صلح",
        "اشاعه", "تقسیم مال مشاع", "ضمان نقل", "حواله", "مهایات",
        "کفالت نسبت به کفیل", "رهن نسبت به راهن",
        "ضمان ضم نسبت به ضامن", "جعاله بعد از اتمام عمل",
        "وصیت تملیکی بعد از قبض مال توسط موصی‌له",
    ],
    "جایز": [
        "حبس مطلق", "عاریه", "ودیعه", "وکالت", "اداره شرکت", "مضاربه",
        "جعاله قبل از اتمام عمل", "رهن نسبت به مرتهن",
        "کفالت نسبت به مکفول‌له", "ضمان ضم نسبت به مضمون‌له",
        "وصیت تملیکی تا قبل از قبض مال",
    ],
    "معوض": [
        "بیع", "معاوضه", "اجاره", "مزارعه", "مساقات", "ضمان نقل",
        "حواله", "جعاله", "صلح در مقام دعوا",
        "صلح در مقام اعمال حقوقی معوض",
    ],
    "غیرمعوض": [
        "وقف", "عاریه", "ودیعه", "وصیت", "هبه", "کفالت", "ضمان ضم",
        "صلح در مقام اعمال حقوقی غیرمعوض", "رهن",
    ],
}

order = ["لازم", "جایز", "معوض", "غیرمعوض"]
widths = {c: max(len(c), max((len(x) for x in columns[c]), default=0)) for c in order}
max_rows = max(len(v) for v in columns.values())


def row(cells):
    return " | ".join(cells[c].ljust(widths[c]) for c in order)


lines = [row({c: c for c in order})]
lines.append(row({c: "-" * widths[c] for c in order}))
for i in range(max_rows):
    lines.append(row({c: (columns[c][i] if i < len(columns[c]) else "") for c in order}))

table_text = "\n".join(lines)

message = (
    f"{RLM}<b>جمع‌بندی عقود از نظر لزوم و عوض</b>\n\n"
    f"{RLM}<pre>{html.escape(table_text)}</pre>"
)

resp = requests.post(API_URL, json={"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}, timeout=30)
print(resp.status_code, resp.text[:300])
