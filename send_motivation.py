#!/usr/bin/env python3
"""Daily motivation email sender for habit breaking."""

import json
import os
import random
import smtplib
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path


def load_quotes():
    """Load quotes from the JSON file."""
    quotes_path = Path(__file__).parent / "quotes.json"
    with open(quotes_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_random_quote(quotes):
    """Select a random quote from local collection."""
    quote = random.choice(quotes)
    return quote["text"], quote["category"]


def fetch_api_quote():
    """Fetch a random quote from ZenQuotes API."""
    url = "https://zenquotes.io/api/random"
    req = urllib.request.Request(url, headers={"User-Agent": "DailyMotivation/1.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        quote_text = data[0]["q"]
        author = data[0]["a"]
        return f"{quote_text} - {author}", "api"


def get_quote(local_quotes):
    """Get a quote from either local collection or API (50/50 chance)."""
    use_api = random.choice([True, False])

    if use_api:
        try:
            return fetch_api_quote()
        except Exception as e:
            print(f"API fetch failed ({e}), using local quote")
            return get_random_quote(local_quotes)
    else:
        return get_random_quote(local_quotes)


def calculate_days_since_start():
    """Calculate days since the journey started."""
    start_date_str = os.environ.get("START_DATE", "2025-01-15")
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    today = datetime.now()
    return (today - start_date).days


def create_email_body(quote, category, days):
    """Create the email body with the quote and progress."""
    category_labels = {
        "general": "Daily Motivation",
        "smoking": "Smoke-Free Journey",
        "alcohol": "Sobriety Strength",
        "gaming": "Real Life Focus",
        "api": "Words of Wisdom"
    }

    label = category_labels.get(category, "Daily Motivation")

    body = f"""
Good morning!

Day {days} of your journey to a better life.

---

{label}:

"{quote}"

---

You're doing great. Every day counts. Keep going!

- Your Daily Motivation App
"""
    return body.strip()


def send_email(subject, body):
    """Send the email via Gmail SMTP."""
    gmail_address = os.environ["GMAIL_ADDRESS"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ["EMAIL_RECIPIENT"]

    msg = MIMEMultipart()
    msg["From"] = gmail_address
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_password)
        server.sendmail(gmail_address, recipient, msg.as_string())

    print(f"Email sent successfully to {recipient}")


def main():
    local_quotes = load_quotes()
    quote, category = get_quote(local_quotes)
    days = calculate_days_since_start()

    subject = f"Day {days}: Your Daily Motivation"
    body = create_email_body(quote, category, days)

    send_email(subject, body)


if __name__ == "__main__":
    main()
