#!/usr/bin/env python3
"""Daily motivation email sender for habit breaking."""

import json
import os
import random
import smtplib
import urllib.error
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


def load_quote_history():
    """Load previous Claude quotes from history file."""
    history_path = Path(__file__).parent / "quote_history.json"
    if history_path.exists():
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_quote_to_history(quote):
    """Save a new quote to the history file."""
    history_path = Path(__file__).parent / "quote_history.json"
    history = load_quote_history()
    history.append({
        "text": quote,
        "date": datetime.now().strftime("%Y-%m-%d")
    })
    # Keep only the last 30 quotes to prevent file from growing too large
    history = history[-30:]
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def fetch_claude_quote():
    """Generate an inspirational addiction recovery quote using Claude API."""
    api_key = os.environ["ANTHROPIC_API_KEY"]
    url = "https://api.anthropic.com/v1/messages"

    # Load recent quotes to provide context for variety
    history = load_quote_history()
    recent_quotes = [q["text"] for q in history[-5:]]

    prompt = (
        "Generate a short, original message about overcoming addiction and recovery. "
        "Keep the tone plain-spoken, honest, and grounded - like advice from someone who's been there. "
        "Avoid flowery or poetic language. Be direct and practical. "
        "It can be a few sentences long. "
        "Different angles are fine: showing up on hard days, building new habits, dealing with setbacks, "
        "asking for help, or just getting through today. "
        "Return ONLY the message text itself, nothing else - no attribution, no quotation marks, "
        "no explanation."
    )

    if recent_quotes:
        prompt += (
            "\n\nFor variety, here are the most recent messages that were sent. "
            "Please create something with a different tone, theme, or perspective:\n"
        )
        for i, q in enumerate(recent_quotes, 1):
            prompt += f"\n{i}. \"{q}\""

    request_body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=request_body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            quote_text = data["content"][0]["text"].strip()
            # Save the new quote to history for future reference
            save_quote_to_history(quote_text)
            return quote_text
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Claude API error {e.code}: {error_body}")
        raise


def calculate_days_since_start():
    """Calculate days since the journey started."""
    start_date_str = os.environ.get("START_DATE", "2025-01-15")
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    today = datetime.now()
    return (today - start_date).days


def create_email_body(local_quote, local_category, api_quote, claude_quote, days):
    """Create the email body with all three quotes and progress."""
    category_labels = {
        "general": "Daily Motivation",
        "smoking": "Smoke-Free Journey",
        "alcohol": "Sobriety Strength",
        "gaming": "Real Life Focus"
    }

    local_label = category_labels.get(local_category, "Daily Motivation")

    body = f"""
Good morning!

Day {days} of your journey to a better life.

---

{local_label}:

"{local_quote}"

---

Words of Wisdom:

"{api_quote}"

---

Recovery Insight:

"{claude_quote}"

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
    local_quote, local_category = get_random_quote(local_quotes)
    days = calculate_days_since_start()

    try:
        api_quote, _ = fetch_api_quote()
    except Exception as e:
        print(f"ZenQuotes API fetch failed ({e}), using second local quote")
        api_quote, _ = get_random_quote(local_quotes)

    try:
        claude_quote = fetch_claude_quote()
    except Exception as e:
        print(f"Claude API fetch failed ({e}), using fallback quote")
        claude_quote = "Every step forward, no matter how small, is a victory worth celebrating."

    subject = f"Day {days}: Your Daily Motivation"
    body = create_email_body(local_quote, local_category, api_quote, claude_quote, days)

    send_email(subject, body)


if __name__ == "__main__":
    main()
