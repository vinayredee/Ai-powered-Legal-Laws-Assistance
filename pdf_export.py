from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile


def generate_pdf_from_log(interaction_log) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf_path = tmpfile.name
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, "Legal Laws Assistant - Chat History")
        y_position = 720
        for _, row in interaction_log.iterrows():
            user_query = row["user_query"]
            assistant_response = row["assistant_response"]
            c.drawString(80, y_position, f"👤 User: {user_query}")
            y_position -= 20
            c.drawString(100, y_position, f"🤖 Assistant: {assistant_response}")
            y_position -= 30
            if y_position < 50:
                c.showPage()
                c.setFont("Helvetica", 12)
                y_position = 750
        c.save()
        return pdf_path


