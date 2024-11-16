import os
import imaplib
import email
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Credentials from .env file
username = os.getenv("EMAIL")
password = os.getenv("PASSWORD")

def connect_to_mail():
    """
    Connect to the IMAP mail server and select the inbox.
    """
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        mail.select("inbox")
        return mail
    except imaplib.IMAP4.error as e:
        print(f"Failed to connect to the mail server: {e}")
        raise

def extract_links_from_html(html_content):
    """
    Extract unsubscribe links from HTML content using BeautifulSoup.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    links = [
        link["href"]
        for link in soup.find_all("a", href=True)
        if "unsubscribe" in link["href"].lower()
    ]
    return links

def click_link(Link):
    try:
        response = requests.get(Link)
        if response.status_code == 200:
            print("Successfully visited", Link)
        else:
            print("Failed to visit", Link, "error code", response.status_code)
    except Exception as e:
        print("Error with", Link, str(e))

def search_for_email():
    """
    Search for emails containing "unsubscribe" in their body and extract unsubscribe links.
    """
    try:
        mail = connect_to_mail()
        # Search for emails containing "unsubscribe"
        _, search_data = mail.search(None, '(BODY "unsubscribe")')
        email_ids = search_data[0].split()

        links = []

        for num in email_ids:
            try:
                # Fetch the email by ID
                _, fetch_data = mail.fetch(num, "(RFC822)")
                raw_email = fetch_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Process the email content
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            html_content = part.get_payload(decode=True)
                            charset = part.get_content_charset() or "utf-8"
                            try:
                                html_content = html_content.decode(charset)
                            except UnicodeDecodeError:
                                html_content = html_content.decode("latin-1", errors="ignore")
                            links.extend(extract_links_from_html(html_content))
                else:
                    # Handle non-multipart emails
                    content_type = msg.get_content_type()
                    content = msg.get_payload(decode=True)
                    charset = msg.get_content_charset() or "utf-8"
                    try:
                        content = content.decode(charset)
                    except UnicodeDecodeError:
                        content = content.decode("latin-1", errors="ignore")
                    if content_type == "text/html":
                        links.extend(extract_links_from_html(content))

            except Exception as e:
                print(f"Failed to process email {num}: {e}")
                continue

        mail.logout()
        return links

    except imaplib.IMAP4.abort as e:
        print(f"IMAP abort error: {e}")
    except imaplib.IMAP4.error as e:
        print(f"IMAP error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        try:
            mail.logout()
        except Exception:
            pass

def save_links(Links):
    with open("links.txt", "w") as f:
        f.write("\n".join(Links))

links = search_for_email()
for link in links:
    click_link(link)

save_links(links)