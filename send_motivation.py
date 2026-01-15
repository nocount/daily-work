#!/usr/bin/env python3
"""Daily motivation email sender for habit breaking."""

import json
import os
import random
import smtplib
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
    """Select a random quote."""
    quote = random.choice(quotes)
    return quote["text"], quote["category"]


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
        "gaming": "Real Life Focus"
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
    quotes = load_quotes()
    quote, category = get_random_quote(quotes)
    days = calculate_days_since_start()

    subject = f"Day {days}: Your Daily Motivation"
    body = create_email_body(quote, category, days)

    send_email(subject, body)


if __name__ == "__main__":
    main()
