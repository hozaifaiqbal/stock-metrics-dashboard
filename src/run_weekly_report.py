from report_generator import generate_weekly_html_report, convert_html_to_pdf
from email_sender import send_email_with_attachment


def run_weekly_report():
    html_path = generate_weekly_html_report()
    pdf_path = convert_html_to_pdf(html_path)

    email_body = """
Hello,

Your weekly portfolio report is attached as a PDF.

This report includes:
- Portfolio summary
- Benchmark comparison
- Live positions
- Return and allocation metrics

Regards,
Stock Metrics Dashboard
"""

    send_email_with_attachment(
        subject="Weekly Portfolio Report",
        body=email_body,
        attachment_path=pdf_path,
    )

    print(f"Weekly report emailed successfully: {pdf_path}")


if __name__ == "__main__":
    run_weekly_report()
