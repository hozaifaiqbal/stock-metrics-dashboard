from report_generator import generate_weekly_html_report, convert_html_to_pdf
from email_sender import send_email_with_attachment


def run_weekly_report():
    html_path = generate_weekly_html_report()
    pdf_path = convert_html_to_pdf(html_path)

    email_body = """
<html>
<body style="font-family: Arial, sans-serif; background:#f5f7fb; padding:24px;">
  <div style="max-width:680px; margin:auto; background:white; border:1px solid #e5e7eb; border-radius:10px; padding:28px;">
    <h2 style="margin-top:0; color:#111827;">Weekly Portfolio Report</h2>

    <p style="font-size:15px; color:#374151;">
      Your latest portfolio report has been generated successfully.
    </p>

    <div style="background:#eef6ff; border-left:4px solid #2563eb; padding:14px; margin:20px 0;">
      <strong>Attached:</strong> Weekly portfolio PDF report
    </div>

    <p style="font-size:14px; color:#374151;">
      This report includes portfolio summary, benchmark comparison, live positions,
      allocation metrics, return metrics, and current market valuation.
    </p>

    <hr style="border:none; border-top:1px solid #e5e7eb; margin:24px 0;">

    <p style="font-size:8px; color:#6b7280;font-style: italic;">
      Generated automatically by Stock Metrics Dashboard (Created by Hozaifa Iqbal).
    </p>
  </div>
</body>
</html>
"""


    send_email_with_attachment(
        subject="Weekly Portfolio Report",
        body=email_body,
        attachment_path=pdf_path,
    )

    print(f"Weekly report emailed successfully: {pdf_path}")


if __name__ == "__main__":
    run_weekly_report()
