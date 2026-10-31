import io
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class PDFService:
    @staticmethod
    def generate_invoice_pdf(invoice) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1e293b"),
        )
        subtitle_style = ParagraphStyle(
            "SubtitleStyle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b"),
        )
        normal_style = styles["Normal"]
        bold_style = ParagraphStyle(
            "BoldStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
        )

        elements = []

        # Header
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(
            Paragraph(f"Invoice #{invoice.invoice_number}", subtitle_style)
        )
        elements.append(Spacer(1, 15))

        # Meta info table
        customer_name = (
            invoice.customer.name if invoice.customer else "Valued Customer"
        )
        customer_email = (
            invoice.customer.email if invoice.customer else ""
        )
        customer_address = (
            invoice.customer.billing_address
            if invoice.customer and invoice.customer.billing_address
            else ""
        )

        meta_data = [
            [
                Paragraph("<b>Billed To:</b>", normal_style),
                Paragraph("<b>Invoice Details:</b>", normal_style),
            ],
            [
                Paragraph(f"{customer_name}<br/>{customer_email}<br/>{customer_address}", normal_style),
                Paragraph(
                    f"Status: <b>{invoice.status.upper()}</b><br/>"
                    f"Issue Date: {invoice.issue_date}<br/>"
                    f"Due Date: {invoice.due_date}<br/>"
                    f"Period: {invoice.billing_period_start} to {invoice.billing_period_end}",
                    normal_style,
                ),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(meta_table)
        elements.append(Spacer(1, 20))

        # Line items table
        headers = [
            Paragraph("<b>Description</b>", bold_style),
            Paragraph("<b>Qty</b>", bold_style),
            Paragraph("<b>Unit Price</b>", bold_style),
            Paragraph("<b>Discount</b>", bold_style),
            Paragraph("<b>Tax</b>", bold_style),
            Paragraph("<b>Total</b>", bold_style),
        ]
        items_data = [headers]

        for line in invoice.lines:
            desc = line.description or (line.product.name if line.product else "Item")
            if line.variant:
                desc += f" ({line.variant.name})"
            items_data.append(
                [
                    Paragraph(desc, normal_style),
                    str(line.quantity),
                    f"${float(line.unit_price + line.variant_price):.2f}",
                    f"${float(line.discount_amount):.2f}",
                    f"${float(line.tax_amount):.2f}",
                    f"${float(line.line_total):.2f}",
                ]
            )

        items_table = Table(
            items_data, colWidths=[200, 40, 75, 75, 75, 75]
        )
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ]
            )
        )
        elements.append(items_table)
        elements.append(Spacer(1, 15))

        # Summary table
        subtotal = float(invoice.subtotal)
        discount = float(invoice.discount_amount)
        tax = float(invoice.tax_amount)
        total = float(invoice.total)
        paid = float(invoice.amount_paid)
        balance = max(0.0, total - paid)

        summary_data = [
            ["Subtotal:", f"${subtotal:.2f}"],
            ["Discount:", f"-${discount:.2f}"],
            ["Tax:", f"${tax:.2f}"],
            ["Total:", f"${total:.2f}"],
            ["Amount Paid:", f"${paid:.2f}"],
            ["Balance Due:", f"${balance:.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[120, 100])
        summary_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
                    ("FONTNAME", (0, 5), (-1, 5), "Helvetica-Bold"),
                    ("TEXTCOLOR", (0, 5), (-1, 5), colors.HexColor("#b91c1c") if balance > 0 else colors.HexColor("#15803d")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        wrapper_data = [["", summary_table]]
        wrapper_table = Table(wrapper_data, colWidths=[320, 220])
        wrapper_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(wrapper_table)

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

