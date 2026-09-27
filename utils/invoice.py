from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def generate_invoice_pdf(
    customer_name,
    email,
    invoice_items,
    subtotal,
    gst_rate,
    gst_amount,
    total,
    notes,
    invoice_number=None
):
    if not invoice_number:
        invoice_number = (
            "INV-" +
            datetime.now().strftime("%Y%m%d%H%M%S")
        )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=8
    )

    right_style = ParagraphStyle(
        "Right",
        parent=styles["Normal"],
        alignment=TA_RIGHT
    )

    story = []

    story.append(
        Paragraph("INVOICEGEN AI", title_style)
    )

    story.append(
        Paragraph(
            f"<b>Invoice Number:</b> {invoice_number}",
            right_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Date:</b> {datetime.now().strftime('%d-%m-%Y')}",
            right_style
        )
    )

    story.append(Spacer(1, 12))

    customer_data = [
        ["Bill To", ""],
        ["Customer", customer_name],
        ["Email", email or "Not provided"]
    ]

    customer_table = Table(
        customer_data,
        colWidths=[35 * mm, 125 * mm]
    )

    customer_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(customer_table)
    story.append(Spacer(1, 15))

    table_data = [
        ["Service", "Qty", "Unit Price", "Amount"]
    ]

    for item in invoice_items:
        amount = (
            item["quantity"] *
            item["unit_price"]
        )

        table_data.append([
            item["service"],
            str(item["quantity"]),
            f"Rs. {item['unit_price']:,.2f}",
            f"Rs. {amount:,.2f}"
        ])

    item_table = Table(
        table_data,
        colWidths=[85 * mm, 20 * mm, 35 * mm, 35 * mm]
    )

    item_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EAF6")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(item_table)
    story.append(Spacer(1, 15))

    totals_data = [
        ["Subtotal", f"Rs. {subtotal:,.2f}"],
        [f"GST ({gst_rate:g}%)", f"Rs. {gst_amount:,.2f}"],
        ["TOTAL", f"Rs. {total:,.2f}"]
    ]

    totals_table = Table(
        totals_data,
        colWidths=[120 * mm, 55 * mm],
        hAlign="RIGHT"
    )

    totals_table.setStyle(
        TableStyle([
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
            ("LINEABOVE", (0, 2), (-1, 2), 1, colors.black),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(totals_table)
    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            f"<b>Notes:</b> {notes or 'No additional notes.'}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "This invoice was generated using InvoiceGen AI.",
            ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                alignment=TA_CENTER,
                fontSize=8
            )
        )
    )

    document.build(story)

    buffer.seek(0)
    return buffer.getvalue()
