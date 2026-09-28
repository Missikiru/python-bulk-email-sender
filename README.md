# Python Bulk Email Sender

A desktop bulk email sender built with Python and Tkinter. The application uses SMTP with STARTTLS to send personalized emails to multiple recipients.

## Features

- Desktop GUI built with Tkinter
- SMTP configuration with STARTTLS
- CSV recipient import
- Email format validation
- Duplicate recipient removal
- `{{name}}` personalization
- Adjustable delay between emails
- Sending progress bar
- Activity log
- Confirmation before sending
- Background sending thread to keep the interface responsive
- Error handling for individual recipients and SMTP failures

## Requirements

- Python 3.9+
- Tkinter (usually included with standard Python installations)

The project uses Python standard-library modules only, so no third-party packages are required.

## How to Run

```bash
python bulk_email_sender.py
```

## CSV Format

The CSV file should contain an `email` or `email_address` column.

Example:

```csv
email
person1@example.com
person2@example.com
```

## Personalization

In the message field, use:

```text
Hello {{name}},

Thank you for your time.
```

If the recipient is `john@example.com`, the application uses `john` as the simple personalization name.

## SMTP Setup

Enter your SMTP host, port, username, password, and sender email in the application.

The application uses STARTTLS before authenticating with the SMTP server.

**Security note:** Never commit passwords, API keys, `.env` files, or other credentials to GitHub. Use test accounts and follow your email provider's sending policies.

## Project Structure

```text
python-bulk-email-sender/
├── bulk_email_sender.py
├── README.md
└── .gitignore
```

## Author

**Farouq Umar Popoola**

GitHub: https://github.com/Missikiru
