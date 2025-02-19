from django.core.mail import EmailMessage
from sesar_api.models import SesarUser
from typing import List

def generate_html(subject: str, subject_detail: str, text: str, button: object = None) -> str:
    if button is not None:
        button_html = f'<a class="button" href={button["href"]}>{button["text"]}</a>'
    else:
        button_html = ""

    return f"""
    <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="format-detection" content="telephone=no">
            <title>{subject}</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    width: 100% !important;
                    height: 100% !important;
                    background-color: #F0F0F0;
                    color: #000000;
                    font-family: sans-serif;
                    text-align: center;
                }}
                .container {{
                    max-width: 560px;
                    margin: 20px auto;
                    background: #FFFFFF;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                }}
                .logo-container {{
                    margin-bottom: 20px;
                }}
                .logo {{
                    width: 100%;
                    max-width: 300px;
                    height: auto;
                }}
                .header {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .subheader {{
                    font-size: 18px;
                    font-weight: 300;
                    margin-bottom: 20px;
                }}
                .content {{
                    font-size: 17px;
                    line-height: 1.6;
                    margin-bottom: 25px;
                }}
                .button {{
                    display: inline-block;
                    background: #7fc5d3;
                    color: #FFFFFF !important;
                    padding: 12px 24px;
                    border-radius: 4px;
                    text-decoration: none !important;
                    font-size: 17px;
                }}
                .line {{
                    border-top: 1px solid #E0E0E0;
                    margin: 25px 0;
                }}
                .footer {{
                    font-size: 17px;
                }}
                .footer a {{
                    color: #127DB3;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo-container">
                    <a href="https://geosamples.org">
                        <img class="logo" src="https://www.geosamples.org/wp-content/uploads/2023/11/sesar2_full_logo_website_bnw-1.png" alt="Logo" title="Logo">
                    </a>
                </div>
                <div class="header">{subject}</div>
                <div class="subheader">{subject_detail if subject_detail is not None else ""}</div>
                <div class="content">{text if text is not None else ""}</div>
                {button_html}
                <div class="line"></div>
                <div class="footer">Have a question? <a href="mailto:info@geosamples.org">info@geosamples.org</a></div>
            </div>
        </body>
        </html>
    """


def sesar_email(recipients: List[SesarUser], subject: str, subject_detail: str, text: str, button: object = None):
    to_emails = [recipient.email for recipient in recipients]
    email = EmailMessage(
        subject=subject,
        body=generate_html(subject, subject_detail, text, button),
        from_email=None,
        to=to_emails,
    )
    email.content_subtype = "html"
    email.send()