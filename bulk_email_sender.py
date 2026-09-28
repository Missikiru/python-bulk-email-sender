import csv
import os
import re
import ssl
import smtplib
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from email.message import EmailMessage


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class BulkEmailSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Bulk Email Sender")
        self.root.geometry("900x720")
        self.root.minsize(760, 600)

        self.smtp_host = tk.StringVar()
        self.smtp_port = tk.StringVar(value="587")
        self.smtp_username = tk.StringVar()
        self.smtp_password = tk.StringVar()
        self.sender_email = tk.StringVar()

        self.subject = tk.StringVar()
        self.delay = tk.StringVar(value="1")

        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text="Python Bulk Email Sender",
            font=("TkDefaultFont", 18, "bold"),
        )
        title.pack(anchor="w", pady=(0, 15))

        smtp_frame = ttk.LabelFrame(main, text="SMTP Configuration", padding=10)
        smtp_frame.pack(fill="x", pady=(0, 10))

        self.add_field(smtp_frame, "SMTP Host:", self.smtp_host, 0)
        self.add_field(smtp_frame, "SMTP Port:", self.smtp_port, 1)
        self.add_field(smtp_frame, "Username:", self.smtp_username, 2)
        self.add_field(smtp_frame, "Password:", self.smtp_password, 3, password=True)
        self.add_field(smtp_frame, "From Email:", self.sender_email, 4)

        receiver_frame = ttk.LabelFrame(
            main,
            text="Recipients",
            padding=10,
        )
        receiver_frame.pack(fill="both", expand=False, pady=(0, 10))

        ttk.Label(
            receiver_frame,
            text="Enter one email per line, or load a CSV file:",
        ).pack(anchor="w")

        receiver_controls = ttk.Frame(receiver_frame)
        receiver_controls.pack(fill="x", pady=6)

        ttk.Button(
            receiver_controls,
            text="Load Recipients from CSV",
            command=self.load_csv,
        ).pack(side="left")

        ttk.Button(
            receiver_controls,
            text="Clear",
            command=self.clear_recipients,
        ).pack(side="left", padx=5)

        self.recipient_text = tk.Text(
            receiver_frame,
            height=7,
            wrap="word",
        )
        self.recipient_text.pack(fill="both", expand=True)

        compose_frame = ttk.LabelFrame(main, text="Message", padding=10)
        compose_frame.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Label(compose_frame, text="Subject:").pack(anchor="w")
        ttk.Entry(
            compose_frame,
            textvariable=self.subject,
        ).pack(fill="x", pady=(2, 8))

        ttk.Label(
            compose_frame,
            text="Message (use {{name}} for personalization):",
        ).pack(anchor="w")

        self.message_text = tk.Text(
            compose_frame,
            height=8,
            wrap="word",
        )
        self.message_text.pack(fill="both", expand=True)

        options = ttk.Frame(main)
        options.pack(fill="x", pady=(0, 10))

        ttk.Label(options, text="Delay between emails (seconds):").pack(side="left")
        ttk.Entry(
            options,
            textvariable=self.delay,
            width=8,
        ).pack(side="left", padx=6)

        self.send_button = ttk.Button(
            options,
            text="Send Emails",
            command=self.start_sending,
        )
        self.send_button.pack(side="right")

        self.progress = ttk.Progressbar(
            main,
            mode="determinate",
        )
        self.progress.pack(fill="x", pady=(0, 6))

        self.status_label = ttk.Label(
            main,
            text="Ready",
        )
        self.status_label.pack(anchor="w")

        log_frame = ttk.LabelFrame(main, text="Activity Log", padding=5)
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame,
            height=7,
            state="disabled",
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True)

    def add_field(self, parent, label, variable, row, password=False):
        ttk.Label(parent, text=label).grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=3,
        )

        entry = ttk.Entry(
            parent,
            textvariable=variable,
            show="*" if password else "",
        )
        entry.grid(
            row=row,
            column=1,
            sticky="ew",
            pady=3,
        )

        parent.columnconfigure(1, weight=1)

    def log(self, message):
        def write():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        self.root.after(0, write)

    def load_csv(self):
        filename = filedialog.askopenfilename(
            title="Select recipient CSV",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )

        if not filename:
            return

        try:
            emails = []

            with open(filename, "r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)

                if not reader.fieldnames:
                    raise ValueError("The CSV file has no header.")

                email_column = next(
                    (
                        column
                        for column in reader.fieldnames
                        if column.lower().strip() in {"email", "email_address"}
                    ),
                    None,
                )

                if not email_column:
                    raise ValueError(
                        "CSV must contain an 'email' or 'email_address' column."
                    )

                for row in reader:
                    email = row.get(email_column, "").strip()
                    if email:
                        emails.append(email)

            self.recipient_text.delete("1.0", "end")
            self.recipient_text.insert("1.0", "\n".join(emails))

            self.log(f"Loaded {len(emails)} recipient(s) from CSV.")

        except Exception as error:
            messagebox.showerror("CSV Error", str(error))

    def clear_recipients(self):
        self.recipient_text.delete("1.0", "end")

    def get_recipients(self):
        raw = self.recipient_text.get("1.0", "end")

        recipients = []
        seen = set()

        for line in raw.splitlines():
            email = line.strip()

            if not email:
                continue

            if not EMAIL_PATTERN.match(email):
                self.log(f"[SKIPPED] Invalid email: {email}")
                continue

            if email.lower() not in seen:
                recipients.append(email)
                seen.add(email.lower())

        return recipients

    def validate_configuration(self):
        required = {
            "SMTP Host": self.smtp_host.get().strip(),
            "SMTP Username": self.smtp_username.get().strip(),
            "SMTP Password": self.smtp_password.get(),
            "From Email": self.sender_email.get().strip(),
            "Subject": self.subject.get().strip(),
        }

        for field, value in required.items():
            if not value:
                messagebox.showwarning(
                    "Missing Information",
                    f"Please enter {field}.",
                )
                return False

        try:
            port = int(self.smtp_port.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Invalid Port",
                "SMTP port must be a number between 1 and 65535.",
            )
            return False

        try:
            delay = float(self.delay.get())
            if delay < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Invalid Delay",
                "Delay must be zero or a positive number.",
            )
            return False

        if not self.get_recipients():
            messagebox.showwarning(
                "No Recipients",
                "Add at least one valid recipient.",
            )
            return False

        return True

    def start_sending(self):
        if not self.validate_configuration():
            return

        recipients = self.get_recipients()

        confirm = messagebox.askyesno(
            "Confirm Sending",
            f"Send this email to {len(recipients)} recipient(s)?",
        )

        if not confirm:
            return

        self.send_button.configure(state="disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = len(recipients)

        thread = threading.Thread(
            target=self.send_bulk_email,
            args=(recipients,),
            daemon=True,
        )
        thread.start()

    def send_bulk_email(self, recipients):
        host = self.smtp_host.get().strip()
        port = int(self.smtp_port.get())
        username = self.smtp_username.get().strip()
        password = self.smtp_password.get()
        sender = self.sender_email.get().strip()
        subject = self.subject.get().strip()
        body_template = self.message_text.get("1.0", "end").strip()
        delay = float(self.delay.get())

        sent = 0
        failed = 0

        try:
            self.log(f"Connecting to {host}:{port}...")

            context = ssl.create_default_context()

            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(username, password)

                self.log("[CONNECTED] SMTP authentication successful.")

                for index, recipient in enumerate(recipients, start=1):
                    try:
                        # If the input is just an email address, use its
                        # local part as a simple personalization name.
                        name = recipient.split("@")[0]

                        body = body_template.replace("{{name}}", name)

                        message = EmailMessage()
                        message["From"] = sender
                        message["To"] = recipient
                        message["Subject"] = subject

                        message.set_content(body)

                        server.send_message(message)

                        sent += 1
                        self.log(
                            f"[{index}/{len(recipients)}] [SENT] {recipient}"
                        )

                    except Exception as error:
                        failed += 1
                        self.log(
                            f"[{index}/{len(recipients)}] "
                            f"[FAILED] {recipient}: {error}"
                        )

                    self.root.after(
                        0,
                        lambda value=index: self.progress.configure(value=value),
                    )

                    self.root.after(
                        0,
                        lambda s=sent, f=failed: self.status_label.configure(
                            text=f"Sent: {s} | Failed: {f}"
                        ),
                    )

                    if delay > 0 and index < len(recipients):
                        import time
                        time.sleep(delay)

            self.log(
                f"Finished. Sent: {sent} | Failed: {failed} | "
                f"Total: {len(recipients)}"
            )

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Complete",
                    f"Sending complete.\n\nSent: {sent}\nFailed: {failed}",
                ),
            )

        except Exception as error:
            self.log(f"[SMTP ERROR] {error}")

            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "SMTP Error",
                    str(error),
                ),
            )

        finally:
            self.root.after(
                0,
                lambda: self.send_button.configure(state="normal"),
            )


def main():
    root = tk.Tk()
    BulkEmailSenderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
