import json
import requests
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

EMAIL_FROM = "digant.jain1993@gmail.com"
EMAIL_TO = "digant.jain1993@gmail.com"

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def fetch_page(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text

def is_in_stock(html):
    return "Sold out online" not in html

def extract_price(html):
    match = re.search(r"\$([0-9]{2})", html)
    if not match:
        return None
    return int(match.group(1))

def send_email(subject, body, gmail_password):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, gmail_password)
        server.send_message(msg)

def main():
    urls = load_json("urls.json")
    state = load_json("state.json")

    current_S1 = set()
    current_S2 = set()

    for item in urls:
        html = fetch_page(item["url"])

        if not is_in_stock(html):
            continue

        price = extract_price(html)
        if price is None:
            continue

        if price < 50:
            current_S1.add(item["url"])
        elif 50 <= price < 60:
            current_S2.add(item["url"])

    old_S1 = set(state["S1"])
    old_S2 = set(state["S2"])

    new_S1 = current_S1 - old_S1
    new_S2 = current_S2 - (old_S1 | old_S2)

    gmail_password = load_json("secrets.json")["gmail_app_password"]

    if new_S1:
        send_email(
            "Best lululemon deal",
            "\n".join(new_S1),
            gmail_password
        )

    if new_S2:
        send_email(
            "Great lululemon deal",
            "\n".join(new_S2),
            gmail_password
        )

    save_json("state.json", {
        "S1": list(current_S1),
        "S2": list(current_S2)
    })

if __name__ == "__main__":
    main()
