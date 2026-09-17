import os
from playwright.sync_api import sync_playwright
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@hajimirzamahmoud")

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
max_rows = max(len(v) for v in columns.values())

header_cells = "".join(f"<th>{c}</th>" for c in order)
body_rows = ""
for i in range(max_rows):
    cells = "".join(
        f"<td>{columns[c][i] if i < len(columns[c]) else ''}</td>" for c in order
    )
    body_rows += f"<tr>{cells}</tr>\n"

html_content = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap');
  body {{
    font-family: 'Vazirmatn', Tahoma, sans-serif;
    margin: 0; padding: 24px; background: #ffffff;
  }}
  table {{ border-collapse: collapse; direction: rtl; }}
  caption {{
    font-size: 20px; font-weight: 700; padding: 10px 0;
    border: 1px solid #222; border-bottom: none; background: #fff;
  }}
  th, td {{
    border: 1px solid #222; padding: 9px 14px;
    font-size: 14px; text-align: center; vertical-align: middle;
    max-width: 220px; line-height: 1.5;
  }}
  th {{ font-weight: 700; background: #f2f2f2; font-size: 15px; }}
</style>
</head>
<body>
<table>
<caption>جمع‌بندی عقود از نظر لزوم و عوض</caption>
<tr>{header_cells}</tr>
{body_rows}
</table>
</body>
</html>
"""

with open("table.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(device_scale_factor=2)
    page.goto("file://" + os.path.abspath("table.html"))
    page.wait_for_timeout(700)
    page.locator("table").screenshot(path="table.png")
    browser.close()

with open("table.png", "rb") as f:
    resp = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data={"chat_id": CHANNEL_ID, "caption": "جمع‌بندی عقود از نظر لزوم و عوض"},
        files={"photo": ("table.png", f, "image/png")},
        timeout=60,
    )
print(resp.status_code, resp.text[:400])
