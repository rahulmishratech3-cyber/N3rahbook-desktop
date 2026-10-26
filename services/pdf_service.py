"""
ReportLab PDF Generator for GST Tax Invoices
Matches the exact user proforma layout: Full A4 page, vertical-only column lines (no horizontal row lines),
2-level HSN summary table, and clean Tally/Busy style formatting.
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from config import INVOICES_DIR, COMPANY_PROFILE
from services.num2words_service import number_to_words_indian


def _resolve_tax_invoice_copies(copy_type):
    """Resolves copy_type string or sequence into a list of copies to render."""
    if isinstance(copy_type, (list, tuple)):
        return list(copy_type)
    c_str = str(copy_type or '').strip()
    if "4 COPIES" in c_str.upper():
        return [
            "ORIGINAL FOR RECIPIENT",
            "DUPLICATE FOR TRANSPORTER",
            "TRIPLICATE FOR SUPPLIER",
            "EXTRA COPY"
        ]
    if not c_str or "ALL" in c_str.upper() or "3 COPIES" in c_str.upper() or "TEENO" in c_str.upper():
        return [
            "ORIGINAL FOR RECIPIENT",
            "DUPLICATE FOR TRANSPORTER",
            "TRIPLICATE FOR SUPPLIER"
        ]
    return [c_str]


def _build_tax_invoice_page_story(order, customer, items, company, printable_width, copy_title, styles):
    """Builds the story elements for a single page copy of the Tax Invoice."""
    story = []

    style_title = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=15,
        textColor=colors.HexColor("#0F172A")
    )

    style_badge = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        alignment=2,
        textColor=colors.HexColor("#475569")
    )

    style_body = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )

    style_body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_cell_right = ParagraphStyle(
        'TableCellRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=2,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_cell_right_bold = ParagraphStyle(
        'TableCellRightBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        alignment=2,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#0F172A")
    )

    # 1. HEADER SECTION
    is_cancelled = str(order.get('status', '')).lower() == 'cancelled' or str(order.get('payment_status', '')).lower() == 'cancelled'
    copy_label = "<font color='#ef4444'><b>[ CANCELLED INVOICE ]</b></font>" if is_cancelled else f"<font color='#475569'><b>{copy_title.upper()}</b></font>"

    header_table = Table([
        [
            Paragraph("<b>TAX INVOICE</b>", style_title),
            Paragraph(copy_label, style_badge)
        ]
    ], colWidths=[printable_width * 0.5, printable_width * 0.5])

    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)

    # ==========================================
    # 2. COMPANY PROFILE & INVOICE META GRID
    # ==========================================
    comp_name = company.get('name', '')
    comp_addr = company.get('address', '')
    comp_gst = company.get('gstin', '')
    comp_mob = company.get('mobile', '')
    comp_pan = company.get('pan', '')
    comp_email = company.get('email', '')
    comp_udyam = company.get('udyam_reg_no', 'UDYAM-UP-18-0048627') or 'UDYAM-UP-18-0048627'

    udyam_line = f"<b>UDYAM REG. NO.:</b> {comp_udyam}<br/>" if comp_udyam else ""

    comp_text = f"""
    <font size='10'><b>{comp_name}</b></font><br/>
    {comp_addr}<br/>
    <b>GSTIN:</b> {comp_gst} &nbsp;&nbsp; <b>Mobile:</b> {comp_mob}<br/>
    <b>PAN:</b> {comp_pan} &nbsp;&nbsp; <b>Email:</b> {comp_email}<br/>
    {udyam_line}
    """

    inv_no = order.get('invoice_number', '')
    inv_date = order.get('invoice_date', '')
    due_date = order.get('due_date', 'N/A')
    po_no = order.get('po_number', '')
    po_date = order.get('po_date', '')
    veh_no = order.get('vehicle_no', 'N/A')
    eway_no = order.get('eway_bill_no', 'N/A')
    pos = order.get('place_of_supply', 'Uttar Pradesh')

    meta_text_1 = f"<b>Invoice No.</b><br/>{inv_no}"
    meta_text_2 = f"<b>Invoice Date</b><br/>{inv_date}"
    meta_text_3 = f"<b>Due Date</b><br/>{due_date if due_date else 'N/A'}"
    meta_text_4 = f"<b>Buyer's PO No.:</b> {po_no if po_no else 'N/A'}"
    meta_text_5 = f"<b>PO Date:</b> {po_date if po_date else 'N/A'}"
    meta_text_6 = f"<b>Vehicle No.:</b> {veh_no if veh_no else 'N/A'}"
    meta_text_7 = f"<b>E-Way Bill:</b> {eway_no if eway_no else 'N/A'}"
    meta_text_8 = f"<b>Place of Supply:</b> {pos}"

    t_meta_right = Table([
        [Paragraph(meta_text_1, style_table_cell_center), Paragraph(meta_text_2, style_table_cell_center), Paragraph(meta_text_3, style_table_cell_center)],
        [Paragraph(meta_text_4, style_body_bold), "", Paragraph(meta_text_5, style_body_bold)],
        [Paragraph(meta_text_6, style_body_bold), "", Paragraph(meta_text_7, style_body_bold)],
        [Paragraph(meta_text_8, style_body_bold), "", ""]
    ], colWidths=[printable_width * 0.17, printable_width * 0.16, printable_width * 0.17])

    t_meta_right.setStyle(TableStyle([
        ('SPAN', (0, 1), (1, 1)),
        ('SPAN', (0, 2), (1, 2)),
        ('SPAN', (0, 3), (2, 3)),
        ('INNERGRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    t_company_grid = Table([
        [Paragraph(comp_text, style_body), t_meta_right]
    ], colWidths=[printable_width * 0.5, printable_width * 0.5])

    t_company_grid.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (0, 0), 4),
        ('BOTTOMPADDING', (0, 0), (0, 0), 4),
        ('LEFTPADDING', (0, 0), (0, 0), 5),
        ('RIGHTPADDING', (0, 0), (0, 0), 5),
        # Flush zero padding for meta grid cell so lines never stick out past border
        ('TOPPADDING', (1, 0), (1, 0), 0),
        ('BOTTOMPADDING', (1, 0), (1, 0), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 0),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
    ]))
    story.append(t_company_grid)

    # ==========================================
    # 3. BILL TO & SHIP TO SECTION
    # ==========================================
    cust_name = str(customer.get('name', '')).strip()
    cust_comp = str(customer.get('company_name', '')).strip()
    
    if cust_comp and cust_name and cust_comp.lower() != cust_name.lower():
        cust_bill_display = f"<b>{cust_comp}</b><br/>Kind Attn: {cust_name}"
        cust_ship_display = f"<b>{cust_comp}</b>"
    else:
        cust_display_name = cust_comp or cust_name or "N/A"
        cust_bill_display = f"<b>{cust_display_name}</b>"
        cust_ship_display = f"<b>{cust_display_name}</b>"

    cust_addr = customer.get('address', 'N/A')
    cust_gst = customer.get('gstin', 'N/A')
    cust_phone = customer.get('phone', '')
    cust_pan = customer.get('pan', '')

    extra_contact_info = ""
    if cust_phone:
        extra_contact_info += f"<b>Mobile:</b> {cust_phone} &nbsp;&nbsp;"
    if cust_pan:
        extra_contact_info += f"<b>PAN Number:</b> {cust_pan}"

    bill_to_text = f"""
    <font color='#475569'><b>BILL TO</b></font><br/>
    {cust_bill_display}<br/>
    <b>Address:</b> {cust_addr}<br/>
    <b>GSTIN:</b> {cust_gst} &nbsp;&nbsp;&nbsp;&nbsp; <b>Place of Supply:</b> {pos}<br/>
    {extra_contact_info}
    """

    ship_to_text = f"""
    <font color='#475569'><b>SHIP TO</b></font><br/>
    {cust_ship_display}<br/>
    <b>Address:</b> {cust_addr}
    """

    t_billing = Table([
        [Paragraph(bill_to_text, style_body), Paragraph(ship_to_text, style_body)]
    ], colWidths=[printable_width * 0.5, printable_width * 0.5])

    t_billing.setStyle(TableStyle([
        ('LINEBEFORE', (0, 0), (-1, -1), 1, colors.black),
        ('LINEAFTER', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_billing)

    # ==========================================
    # 4. MAIN ITEMS TABLE (NO HORIZONTAL ROW LINES)
    # ==========================================
    col_w = [
        35,                   # S.NO.
        225,                  # ITEMS
        70,                   # HSN
        70,                   # QTY.
        80,                   # RATE
        printable_width - 480 # AMOUNT (91.27pt)
    ]

    items_data = [
        [
            Paragraph("<b>S.NO.</b>", style_table_header),
            Paragraph("<b>ITEMS</b>", style_table_header),
            Paragraph("<b>HSN</b>", style_table_header),
            Paragraph("<b>QTY.</b>", style_table_header),
            Paragraph("<b>RATE</b>", style_table_header),
            Paragraph("<b>AMOUNT</b>", style_table_header)
        ]
    ]

    # Format item lines as HTML paragraphs inside a single tall body cell per column
    sno_lines = []
    item_lines = []
    hsn_lines = []
    qty_lines = []
    rate_lines = []
    amt_lines = []

    total_qty = 0.0
    hsn_tax_summary = {}

    cgst_total = float(order.get('cgst_amount', 0.0) or 0.0)
    sgst_total = float(order.get('sgst_amount', 0.0) or 0.0)
    igst_total = float(order.get('igst_amount', 0.0) or 0.0)
    round_off = float(order.get('round_off', 0.0) or 0.0)
    grand_total = float(order.get('total_amount', 0.0) or 0.0)

    # Auto-detect IGST if total is 0 but item rates have igst_rate
    if igst_total == 0.0 and cgst_total == 0.0:
        for itm in items:
            if float(itm.get('igst_rate', 0.0) or 0.0) > 0:
                igst_total = sum(float(i.get('amount', 0)) * float(i.get('igst_rate', 0))/100 for i in items)
                break

    for idx, item in enumerate(items, start=1):
        qty = float(item.get('quantity', 0))
        rate = float(item.get('unit_price', 0))
        amt = float(item.get('amount', qty * rate))
        unit_str = item.get('unit', 'PCS')
        hsn = str(item.get('hsn_code', '00000000'))

        total_qty += qty

        if igst_total > 0:
            cgst_r = 0.0
            sgst_r = 0.0
            igst_r = float(item.get('igst_rate', 18.0) or 18.0)
            cgst_amt = 0.0
            sgst_amt = 0.0
            igst_amt = round(amt * (igst_r / 100.0), 2)
        else:
            cgst_r = float(item.get('cgst_rate', 9.0) if cgst_total > 0 else 0.0)
            sgst_r = float(item.get('sgst_rate', 9.0) if sgst_total > 0 else 0.0)
            igst_r = 0.0
            cgst_amt = round(amt * (cgst_r / 100.0), 2)
            sgst_amt = round(amt * (sgst_r / 100.0), 2)
            igst_amt = 0.0

        if hsn not in hsn_tax_summary:
            hsn_tax_summary[hsn] = {
                'taxable': 0.0,
                'cgst_rate': cgst_r,
                'cgst_amt': 0.0,
                'sgst_rate': sgst_r,
                'sgst_amt': 0.0,
                'igst_rate': igst_r,
                'igst_amt': 0.0,
            }
        hsn_tax_summary[hsn]['taxable'] += amt
        hsn_tax_summary[hsn]['cgst_amt'] += cgst_amt
        hsn_tax_summary[hsn]['sgst_amt'] += sgst_amt
        hsn_tax_summary[hsn]['igst_amt'] += igst_amt

        sno_lines.append(str(idx))
        item_lines.append(f"<b>{item.get('item_name', '')}</b>")
        hsn_lines.append(hsn)
        qty_lines.append(f"{qty:g} {unit_str}")
        rate_lines.append(f"{rate:,.2f}")
        amt_lines.append(f"{amt:,.2f}")

    items_data.append([
        Paragraph("<br/>".join(sno_lines), style_table_cell_center),
        Paragraph("<br/>".join(item_lines), style_table_cell),
        Paragraph("<br/>".join(hsn_lines), style_table_cell_center),
        Paragraph("<br/>".join(qty_lines), style_table_cell_center),
        Paragraph("<br/>".join(rate_lines), style_table_cell_right),
        Paragraph("<br/>".join(amt_lines), style_table_cell_right)
    ])

    # Optional Freight / Fare Line if present
    freight_val = float(order.get('freight', 0.0) or 0.0)
    if freight_val > 0:
        sac_code = "9965"
        if sac_code not in hsn_tax_summary:
            hsn_tax_summary[sac_code] = {
                'taxable': 0.0,
                'cgst_rate': 9.0 if cgst_total > 0 else 0.0,
                'cgst_amt': 0.0,
                'sgst_rate': 9.0 if sgst_total > 0 else 0.0,
                'sgst_amt': 0.0,
                'igst_rate': 18.0 if igst_total > 0 else 0.0,
                'igst_amt': 0.0,
            }
        hsn_tax_summary[sac_code]['taxable'] += freight_val
        if igst_total > 0:
            hsn_tax_summary[sac_code]['igst_amt'] += round(freight_val * 0.18, 2)
        else:
            hsn_tax_summary[sac_code]['cgst_amt'] += round(freight_val * 0.09, 2)
            hsn_tax_summary[sac_code]['sgst_amt'] += round(freight_val * 0.09, 2)

        items_data.append([
            Paragraph("<i>Freight / Fare (excl GST)</i>", style_table_cell_right),
            "", "", "",
            Paragraph("-", style_table_cell_center),
            Paragraph(f"Rs. {freight_val:,.2f}", style_table_cell_right)
        ])

    # Tax Calculation Lines
    if igst_total > 0:
        items_data.append([
            Paragraph("<i>IGST @ 18%</i>", style_table_cell_right),
            "", "", "",
            Paragraph("-", style_table_cell_center),
            Paragraph(f"Rs. {igst_total:,.2f}", style_table_cell_right)
        ])
    else:
        if cgst_total > 0:
            items_data.append([
                Paragraph("<i>CGST @ 9%</i>", style_table_cell_right),
                "", "", "",
                Paragraph("-", style_table_cell_center),
                Paragraph(f"Rs. {cgst_total:,.2f}", style_table_cell_right)
            ])
        if sgst_total > 0:
            items_data.append([
                Paragraph("<i>SGST @ 9%</i>", style_table_cell_right),
                "", "", "",
                Paragraph("-", style_table_cell_center),
                Paragraph(f"Rs. {sgst_total:,.2f}", style_table_cell_right)
            ])

    if round_off != 0.0:
        items_data.append([
            Paragraph("<i>Round Off</i>", style_table_cell_right),
            "", "", "",
            Paragraph("-", style_table_cell_center),
            Paragraph(f"{round_off:,.2f}", style_table_cell_right)
        ])

    # TOTAL Row
    items_data.append([
        Paragraph("<b>TOTAL</b>", style_table_header),
        "", "",
        Paragraph(f"<b>{total_qty:g}</b>", style_table_cell_center),
        "",
        Paragraph(f"<b>Rs. {grand_total:,.2f}</b>", style_table_cell_right_bold)
    ])

    # Dynamic items area height to land footer right at the bottom margin
    num_tax_rows = len(items_data) - 2 # excluding header & item body
    item_body_height = 370 - (num_tax_rows * 16)
    if item_body_height < 150:
        item_body_height = 150

    row_heights = [20, item_body_height] + [16] * (len(items_data) - 3) + [20]

    t_items = Table(items_data, colWidths=col_w, rowHeights=row_heights)

    items_table_styles = [
        ('LINEBEFORE', (0,0), (-1,-1), 1, colors.black),
        ('LINEAFTER', (0,0), (-1,-1), 1, colors.black),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.black),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        
        # Vertical column lines running all the way down
        ('LINEBEFORE', (1,0), (1,-1), 0.75, colors.black),
        ('LINEBEFORE', (2,0), (2,-1), 0.75, colors.black),
        ('LINEBEFORE', (3,0), (3,-1), 0.75, colors.black),
        ('LINEBEFORE', (4,0), (4,-1), 0.75, colors.black),
        ('LINEBEFORE', (5,0), (5,-1), 0.75, colors.black),
        
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('VALIGN', (0,-1), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]

    # Spanning for tax calculation rows near bottom
    tax_start_idx = 2
    for r_idx in range(tax_start_idx, len(items_data) - 1):
        items_table_styles.append(('SPAN', (0, r_idx), (3, r_idx)))

    # Line above tax calculation area
    items_table_styles.append(('LINEABOVE', (0, tax_start_idx), (-1, tax_start_idx), 0.75, colors.black))
    
    # Line above TOTAL row & background
    items_table_styles.append(('SPAN', (0, -1), (2, -1)))
    items_table_styles.append(('LINEABOVE', (0, -1), (-1, -1), 1, colors.black))
    items_table_styles.append(('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F8FAFC")))

    t_items.setStyle(TableStyle(items_table_styles))
    story.append(t_items)

    # ==========================================
    # 5. HSN/SAC SUMMARY TABLE (2-LEVEL HEADERS)
    # ==========================================
    if igst_total > 0:
        gst_summary_data = [
            [
                Paragraph("<b>HSN/SAC</b>", style_table_header),
                Paragraph("<b>Taxable Value</b>", style_table_header),
                Paragraph("<b>Integrated Tax (IGST)</b>", style_table_header),
                "",
                Paragraph("<b>Total Tax Amount</b>", style_table_header)
            ],
            [
                "", "",
                Paragraph("<b>Rate</b>", style_table_header),
                Paragraph("<b>Amount</b>", style_table_header),
                ""
            ]
        ]

        tot_taxable = 0.0
        tot_igst_sum = 0.0

        for hsn_code, vals in hsn_tax_summary.items():
            taxable = vals['taxable']
            i_amt = vals.get('igst_amt', 0.0)
            tot_taxable += taxable
            tot_igst_sum += i_amt

            gst_summary_data.append([
                Paragraph(hsn_code, style_table_cell_center),
                Paragraph(f"{taxable:,.2f}", style_table_cell_right),
                Paragraph(f"{vals.get('igst_rate', 18.0):g}%", style_table_cell_center),
                Paragraph(f"{i_amt:,.2f}", style_table_cell_right),
                Paragraph(f"Rs. {i_amt:,.2f}", style_table_cell_right)
            ])

        gst_summary_data.append([
            Paragraph("<b>Total</b>", style_table_header),
            Paragraph(f"<b>{tot_taxable:,.2f}</b>", style_table_cell_right_bold),
            "",
            Paragraph(f"<b>{tot_igst_sum:,.2f}</b>", style_table_cell_right_bold),
            Paragraph(f"<b>Rs. {tot_igst_sum:,.2f}</b>", style_table_cell_right_bold)
        ])

        hsn_col_w = [
            printable_width * 0.22,
            printable_width * 0.24,
            printable_width * 0.16,
            printable_width * 0.18,
            printable_width * 0.20
        ]

        t_gst = Table(gst_summary_data, colWidths=hsn_col_w)
        t_gst.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (1, 1)),
            ('SPAN', (2, 0), (3, 0)),
            ('SPAN', (4, 0), (4, 1)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor("#F1F5F9")),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F8FAFC")),
        ]))
        story.append(t_gst)
    else:
        gst_summary_data = [
            [
                Paragraph("<b>HSN/SAC</b>", style_table_header),
                Paragraph("<b>Taxable Value</b>", style_table_header),
                Paragraph("<b>CGST</b>", style_table_header),
                "",
                Paragraph("<b>SGST</b>", style_table_header),
                "",
                Paragraph("<b>Total Tax Amount</b>", style_table_header)
            ],
            [
                "", "",
                Paragraph("<b>Rate</b>", style_table_header),
                Paragraph("<b>Amount</b>", style_table_header),
                Paragraph("<b>Rate</b>", style_table_header),
                Paragraph("<b>Amount</b>", style_table_header),
                ""
            ]
        ]

        tot_taxable = 0.0
        tot_cgst_sum = 0.0
        tot_sgst_sum = 0.0

        for hsn_code, vals in hsn_tax_summary.items():
            taxable = vals['taxable']
            c_amt = vals['cgst_amt']
            s_amt = vals['sgst_amt']
            tot_tax = c_amt + s_amt

            tot_taxable += taxable
            tot_cgst_sum += c_amt
            tot_sgst_sum += s_amt

            gst_summary_data.append([
                Paragraph(hsn_code, style_table_cell_center),
                Paragraph(f"{taxable:,.2f}", style_table_cell_right),
                Paragraph(f"{vals['cgst_rate']:g}%", style_table_cell_center),
                Paragraph(f"{c_amt:,.2f}", style_table_cell_right),
                Paragraph(f"{vals['sgst_rate']:g}%", style_table_cell_center),
                Paragraph(f"{s_amt:,.2f}", style_table_cell_right),
                Paragraph(f"Rs. {tot_tax:,.2f}", style_table_cell_right)
            ])

        gst_summary_data.append([
            Paragraph("<b>Total</b>", style_table_header),
            Paragraph(f"<b>{tot_taxable:,.2f}</b>", style_table_cell_right_bold),
            "",
            Paragraph(f"<b>{tot_cgst_sum:,.2f}</b>", style_table_cell_right_bold),
            "",
            Paragraph(f"<b>{tot_sgst_sum:,.2f}</b>", style_table_cell_right_bold),
            Paragraph(f"<b>Rs. {(tot_cgst_sum + tot_sgst_sum):,.2f}</b>", style_table_cell_right_bold)
        ])

        hsn_col_w = [
            printable_width * 0.18, # HSN
            printable_width * 0.18, # Taxable
            printable_width * 0.10, # CGST Rate
            printable_width * 0.14, # CGST Amt
            printable_width * 0.10, # SGST Rate
            printable_width * 0.14, # SGST Amt
            printable_width * 0.16  # Total Tax
        ]

        t_gst = Table(gst_summary_data, colWidths=hsn_col_w)
        t_gst.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('SPAN', (0, 0), (0, 1)), # HSN/SAC
            ('SPAN', (1, 0), (1, 1)), # Taxable Value
            ('SPAN', (2, 0), (3, 0)), # CGST Header
            ('SPAN', (4, 0), (5, 0)), # SGST Header
            ('SPAN', (6, 0), (6, 1)), # Total Tax Header
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor("#F1F5F9")),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F8FAFC")),
        ]))
        story.append(t_gst)

    # ==========================================
    # 6. TOTAL AMOUNT IN WORDS BOX
    # ==========================================
    words_str = number_to_words_indian(grand_total)
    words_text = f"<b>Total Amount (in words)</b><br/>{words_str}"

    t_words = Table([[Paragraph(words_text, style_body)]], colWidths=[printable_width])
    t_words.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_words)

    # ==========================================
    # 7. FOOTER (BANK, TERMS & SIGNATORY)
    # ==========================================
    bank_name = company.get('bank_name', '')
    bank_branch = company.get('bank_branch', '')
    if bank_branch:
        full_bank_str = f"{bank_name}, {bank_branch}"
    else:
        full_bank_str = bank_name

    bank_text = f"""
    <b>Bank Details</b><br/>
    <b>Name:</b> {comp_name}<br/>
    <b>IFSC Code:</b> {company.get('ifsc_code', '')}<br/>
    <b>Account No:</b> {company.get('account_no', '')}<br/>
    <b>Bank:</b> {full_bank_str}
    """

    terms_list = company.get('terms', [])
    terms_body = "<br/>".join(terms_list) if isinstance(terms_list, list) else str(terms_list)
    terms_text = f"""
    <b>Terms and Conditions</b><br/>
    {terms_body}
    """

    sign_text = f"""
    <br/><br/>
    <b>Authorised Signatory For</b><br/>
    {comp_name}
    """

    t_footer = Table([
        [
            Paragraph(bank_text, style_body),
            Paragraph(terms_text, style_body),
            Paragraph(sign_text, style_table_cell_center)
        ]
    ], colWidths=[printable_width * 0.36, printable_width * 0.36, printable_width * 0.28])

    t_footer.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_footer)

    return story


def generate_tax_invoice_pdf(order, customer, items, company=None, page_size="A4", copy_type="4 COPIES (ORIGINAL + DUPLICATE + TRIPLICATE + EXTRA COPY)", filename=None):
    """
    Generates a professional GST Tax Invoice matching exact user proforma layout:
    - Full A4 Page height
    - No horizontal lines between item rows (only vertical column dividers)
    - 2-level HSN/SAC summary table (CGST Rate|Amount, SGST Rate|Amount)
    - Bank details, Terms & Conditions, and Signatory footer
    - Supports single copies or exporting all 3 copies (Original, Duplicate, Triplicate) together in a single PDF.
    """
    if company is None:
        try:
            from models.company import CompanyModel
            company = CompanyModel.get_profile()
        except Exception:
            company = COMPANY_PROFILE

    page_dim = A4 if page_size.upper() == "A4" else LETTER
    width, height = page_dim

    if filename is None:
        inv_num_clean = str(order.get('invoice_number', 'INV-001')).replace('/', '_')
        filename = INVOICES_DIR / f"Tax_Invoice_{inv_num_clean}_{page_size.upper()}.pdf"
    else:
        filename = Path(filename)

    # 12pt Margins around page (Printable Width = width - 24 = 571.27pt for A4)
    margin = 12
    printable_width = width - (margin * 2)

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=page_dim,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    styles = getSampleStyleSheet()
    copies_list = _resolve_tax_invoice_copies(copy_type)

    # Ensure watermark is prepared with transparency
    watermark_jpg = Path("assets/watermark.jpg")
    watermark_png = Path("assets/watermark_transparent.png")
    
    if watermark_jpg.exists() and not watermark_png.exists():
        try:
            from PIL import Image
            img = Image.open(str(watermark_jpg)).convert("RGBA")
            alpha = img.split()[3]
            alpha = alpha.point(lambda p: p * 0.12) # 12% opacity
            img.putalpha(alpha)
            img.save(str(watermark_png), "PNG")
        except Exception as ex:
            print("Failed to process watermark:", ex)

    def _add_watermark(canvas, doc_obj):
        if watermark_png.exists():
            try:
                from reportlab.lib.utils import ImageReader
                reader = ImageReader(str(watermark_png))
                iw, ih = reader.getSize()
                aspect = ih / float(iw)
                w = 300  # Reduced size
                h = 300 * aspect
                page_w, page_h = doc_obj.pagesize
                x = (page_w - w) / 2.0
                y = (page_h - h) / 2.0
                canvas.saveState()
                canvas.drawImage(reader, x, y, width=w, height=h, mask='auto')
                canvas.restoreState()
            except Exception as e:
                pass

    story = []
    for idx, c_label in enumerate(copies_list):
        if idx > 0:
            story.append(PageBreak())
        page_elements = _build_tax_invoice_page_story(
            order=order,
            customer=customer,
            items=items,
            company=company,
            printable_width=printable_width,
            copy_title=c_label,
            styles=styles
        )
        story.extend(page_elements)

    doc.build(
        story,
        onFirstPage=_add_watermark,
        onLaterPages=_add_watermark
    )
    return str(filename)


def generate_bulk_tax_invoices_pdf(orders_data, company=None, page_size="A4", copy_type="TRIPLICATE FOR SUPPLIER", filename=None):
    """
    Generates a single PDF containing multiple tax invoices (bulk export).
    orders_data is a list of tuples containing: (order, customer, items)
    """
    if company is None:
        try:
            from models.company import CompanyModel
            company = CompanyModel.get_profile()
        except Exception:
            company = COMPANY_PROFILE

    page_dim = A4 if page_size.upper() == "A4" else LETTER
    width, height = page_dim

    if filename is None:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = INVOICES_DIR / f"Bulk_Tax_Invoices_{timestamp}_{page_size.upper()}.pdf"
    else:
        filename = Path(filename)

    margin = 12
    printable_width = width - (margin * 2)

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=page_dim,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    styles = getSampleStyleSheet()
    copies_list = _resolve_tax_invoice_copies(copy_type)

    watermark_jpg = Path("assets/watermark.jpg")
    watermark_png = Path("assets/watermark_transparent.png")
    
    if watermark_jpg.exists() and not watermark_png.exists():
        try:
            from PIL import Image
            img = Image.open(str(watermark_jpg)).convert("RGBA")
            alpha = img.split()[3]
            alpha = alpha.point(lambda p: p * 0.12)
            img.putalpha(alpha)
            img.save(str(watermark_png), "PNG")
        except Exception as ex:
            print("Failed to process watermark:", ex)

    def _add_watermark(canvas, doc_obj):
        if watermark_png.exists():
            try:
                from reportlab.lib.utils import ImageReader
                reader = ImageReader(str(watermark_png))
                iw, ih = reader.getSize()
                aspect = ih / float(iw)
                w = 300
                h = 300 * aspect
                page_w, page_h = doc_obj.pagesize
                x = (page_w - w) / 2.0
                y = (page_h - h) / 2.0
                canvas.saveState()
                canvas.drawImage(reader, x, y, width=w, height=h, mask='auto')
                canvas.restoreState()
            except Exception:
                pass

    story = []
    is_first_page = True
    
    for order, customer, items in orders_data:
        for idx, c_label in enumerate(copies_list):
            if not is_first_page:
                story.append(PageBreak())
            is_first_page = False
            
            page_elements = _build_tax_invoice_page_story(
                order=order,
                customer=customer,
                items=items,
                company=company,
                printable_width=printable_width,
                copy_title=c_label,
                styles=styles
            )
            story.extend(page_elements)

    if not story:
        return None

    doc.build(
        story,
        onFirstPage=_add_watermark,
        onLaterPages=_add_watermark
    )
    return str(filename)


def generate_purchase_invoice_pdf(po, supplier, items, company=None, page_size="A4", copy_type="ORIGINAL FOR RECIPIENT", filename=None):
    """
    Generates a professional GST Purchase Tax Invoice / Purchase Order matching exact user proforma layout:
    - Full A4 Page height
    - No horizontal lines between item rows (only vertical column dividers)
    - Supplier/Vendor as Seller (Bill From)
    - Company Profile as Buyer (Bill To)
    - 2-level HSN/SAC summary table (CGST Rate|Amount, SGST Rate|Amount)
    - Terms & Conditions and Signatory footer
    """
    if company is None:
        try:
            from models.company import CompanyModel
            company = CompanyModel.get_profile()
        except Exception:
            company = COMPANY_PROFILE

    page_dim = A4 if page_size.upper() == "A4" else LETTER
    width, height = page_dim

    po_status = str(po.get('status', 'Received')).strip()
    is_received = po_status.lower() in ('received', 'completed')
    is_cancelled = po_status.lower() == 'cancelled'

    if filename is None:
        po_num_clean = str(po.get('po_number', 'PO-001')).replace('/', '_')
        prefix = "Purchase_Invoice" if is_received else "Purchase_Order"
        filename = INVOICES_DIR / f"{prefix}_{po_num_clean}_{page_size.upper()}.pdf"
    else:
        filename = Path(filename)

    margin = 12
    printable_width = width - (margin * 2)

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=page_dim,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    story = []

    # Typography Styles
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=15,
        textColor=colors.HexColor("#0F172A")
    )

    style_badge = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        alignment=2,
        textColor=colors.HexColor("#475569")
    )

    style_body = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )

    style_body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_cell_right = ParagraphStyle(
        'TableCellRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=2,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_cell_right_bold = ParagraphStyle(
        'TableCellRightBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        alignment=2,
        textColor=colors.HexColor("#0F172A")
    )

    style_table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#0F172A")
    )

    # 1. HEADER SECTION
    if is_cancelled:
        main_heading = "PURCHASE INVOICE"
        copy_label = "<font color='#ef4444'><b>[ CANCELLED PURCHASE ]</b></font>"
    elif is_received:
        main_heading = "PURCHASE TAX INVOICE"
        copy_label = f"<font color='#059669'><b>[ INWARD SUPPLY / PURCHASE RECORD ]</b></font>"
    else:
        main_heading = "PURCHASE ORDER"
        copy_label = f"<font color='#475569'><b>[ PURCHASE ORDER (PENDING) ]</b></font>"

    header_table = Table([
        [
            Paragraph(f"<b>{main_heading}</b>", style_title),
            Paragraph(copy_label, style_badge)
        ]
    ], colWidths=[printable_width * 0.5, printable_width * 0.5])

    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)

    # 2. SUPPLIER / VENDOR DETAILS (BILL FROM) & PURCHASE META GRID
    sup_name = supplier.get('name', '') or po.get('supplier_name', 'Supplier')
    sup_comp = supplier.get('company_name', '') or po.get('company_name', '')
    sup_display = sup_comp if sup_comp else sup_name
    if sup_comp and sup_name and sup_comp.lower() != sup_name.lower():
        sup_display = f"{sup_comp} (Attn: {sup_name})"

    sup_addr = supplier.get('address', '') or po.get('supplier_address', 'N/A')
    sup_gst = supplier.get('gstin', '') or po.get('supplier_gstin', 'N/A')
    sup_mob = supplier.get('phone', '') or po.get('supplier_phone', '')
    sup_pan = supplier.get('pan', '') or po.get('supplier_pan', '')
    sup_email = supplier.get('email', '') or po.get('supplier_email', '')

    sup_contact_str = ""
    if sup_mob:
        sup_contact_str += f"<b>Mobile:</b> {sup_mob} &nbsp;&nbsp;"
    if sup_email:
        sup_contact_str += f"<b>Email:</b> {sup_email}"

    sup_pan_str = f"<b>PAN:</b> {sup_pan}" if sup_pan else ""

    sup_text = f"""
    <font color='#475569'><b>SUPPLIER / VENDOR (BILL FROM)</b></font><br/>
    <font size='10'><b>{sup_display}</b></font><br/>
    {sup_addr}<br/>
    <b>GSTIN:</b> {sup_gst} &nbsp;&nbsp; {sup_pan_str}<br/>
    {sup_contact_str}
    """

    po_no = po.get('po_number', '')
    po_date = po.get('order_date', '')
    exp_date = po.get('expected_date', 'N/A')
    pos = supplier.get('place_of_supply', '') or po.get('supplier_pos', 'Uttar Pradesh')

    meta_text_1 = f"<b>PO / Ref No.</b><br/>{po_no}"
    meta_text_2 = f"<b>Purchase Date</b><br/>{po_date}"
    meta_text_3 = f"<b>Delivery Date</b><br/>{exp_date}"
    meta_text_4 = f"<b>Status:</b> {po_status.upper()}"
    meta_text_5 = f"<b>Place of Supply:</b> {pos}"
    meta_text_6 = f"<b>Notes:</b> {po.get('notes', 'Direct Purchase Entry')}"

    t_meta_right = Table([
        [Paragraph(meta_text_1, style_table_cell_center), Paragraph(meta_text_2, style_table_cell_center), Paragraph(meta_text_3, style_table_cell_center)],
        [Paragraph(meta_text_4, style_body_bold), "", ""],
        [Paragraph(meta_text_5, style_body_bold), "", ""],
        [Paragraph(meta_text_6, style_body), "", ""]
    ], colWidths=[printable_width * 0.16, printable_width * 0.17, printable_width * 0.17])

    t_meta_right.setStyle(TableStyle([
        ('SPAN', (0, 1), (2, 1)),
        ('SPAN', (0, 2), (2, 2)),
        ('SPAN', (0, 3), (2, 3)),
        ('INNERGRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    t_supplier_grid = Table([
        [Paragraph(sup_text, style_body), t_meta_right]
    ], colWidths=[printable_width * 0.5, printable_width * 0.5])

    t_supplier_grid.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (0, 0), 4),
        ('BOTTOMPADDING', (0, 0), (0, 0), 4),
        ('LEFTPADDING', (0, 0), (0, 0), 5),
        ('RIGHTPADDING', (0, 0), (0, 0), 5),
        ('TOPPADDING', (1, 0), (1, 0), 0),
        ('BOTTOMPADDING', (1, 0), (1, 0), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 0),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
    ]))
    story.append(t_supplier_grid)

    # 3. BUYER DETAILS (BILL TO - USER COMPANY)
    comp_name = company.get('name', '')
    comp_addr = company.get('address', '')
    comp_gst = company.get('gstin', '')
    comp_mob = company.get('mobile', '')
    comp_pan = company.get('pan', '')
    comp_email = company.get('email', '')
    comp_udyam = company.get('udyam_reg_no', 'UDYAM-UP-18-0048627') or 'UDYAM-UP-18-0048627'

    buyer_bill_text = f"""
    <font color='#475569'><b>BUYER / RECIPIENT (BILL TO)</b></font><br/>
    <b>{comp_name}</b><br/>
    <b>Address:</b> {comp_addr}<br/>
    <b>GSTIN:</b> {comp_gst} &nbsp;&nbsp; <b>PAN:</b> {comp_pan}<br/>
    <b>Mobile:</b> {comp_mob} &nbsp;&nbsp; <b>Email:</b> {comp_email}
    """

    buyer_ship_text = f"""
    <font color='#475569'><b>CONSIGNEE / SHIP TO</b></font><br/>
    <b>{comp_name}</b><br/>
    <b>Delivery Address:</b> {comp_addr}<br/>
    <b>UDYAM REG. NO.:</b> {comp_udyam}
    """

    t_buyer = Table([
        [Paragraph(buyer_bill_text, style_body), Paragraph(buyer_ship_text, style_body)]
    ], colWidths=[printable_width * 0.5, printable_width * 0.5])

    t_buyer.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_buyer)

    # 4. MAIN ITEMS TABLE
    col_w = [
        35,                   # S.NO.
        225,                  # ITEMS
        70,                   # HSN
        70,                   # QTY.
        80,                   # RATE / UNIT COST
        printable_width - 480 # AMOUNT (91.27pt)
    ]

    items_data = [
        [
            Paragraph("<b>S.NO.</b>", style_table_header),
            Paragraph("<b>ITEMS / PRODUCT DESCRIPTION</b>", style_table_header),
            Paragraph("<b>HSN</b>", style_table_header),
            Paragraph("<b>QTY.</b>", style_table_header),
            Paragraph("<b>UNIT COST</b>", style_table_header),
            Paragraph("<b>TAXABLE COST</b>", style_table_header)
        ]
    ]

    sno_lines = []
    item_lines = []
    hsn_lines = []
    qty_lines = []
    rate_lines = []
    amt_lines = []

    total_qty = 0.0
    hsn_tax_summary = {}

    subtotal_val = float(po.get('subtotal', 0.0) or 0.0)
    freight_val = float(po.get('freight', 0.0) or 0.0)
    cgst_total = float(po.get('cgst_amount', 0.0) or 0.0)
    sgst_total = float(po.get('sgst_amount', 0.0) or 0.0)
    igst_total = float(po.get('igst_amount', 0.0) or 0.0)
    round_off = float(po.get('round_off', 0.0) or 0.0)
    grand_total = float(po.get('total_amount', 0.0) or 0.0)

    for idx, item in enumerate(items, start=1):
        qty = float(item.get('quantity', 0))
        rate = float(item.get('unit_cost', item.get('unit_price', 0)))
        amt = float(item.get('total_cost', item.get('amount', qty * rate)))
        unit_str = item.get('unit', 'PCS')
        hsn = str(item.get('hsn_code', '39211310'))
        subcat = str(item.get('subcategory', '')).strip()

        total_qty += qty

        if igst_total > 0:
            cgst_r = 0.0
            sgst_r = 0.0
            igst_r = 18.0
            cgst_amt = 0.0
            sgst_amt = 0.0
            igst_amt = round(amt * 0.18, 2)
        else:
            cgst_r = 9.0 if cgst_total > 0 else 0.0
            sgst_r = 9.0 if sgst_total > 0 else 0.0
            igst_r = 0.0
            cgst_amt = round(amt * (cgst_r / 100.0), 2)
            sgst_amt = round(amt * (sgst_r / 100.0), 2)
            igst_amt = 0.0

        if hsn not in hsn_tax_summary:
            hsn_tax_summary[hsn] = {
                'taxable': 0.0,
                'cgst_rate': cgst_r,
                'cgst_amt': 0.0,
                'sgst_rate': sgst_r,
                'sgst_amt': 0.0,
                'igst_rate': igst_r,
                'igst_amt': 0.0,
            }
        hsn_tax_summary[hsn]['taxable'] += amt
        hsn_tax_summary[hsn]['cgst_amt'] += cgst_amt
        hsn_tax_summary[hsn]['sgst_amt'] += sgst_amt
        hsn_tax_summary[hsn]['igst_amt'] += igst_amt

        sno_lines.append(str(idx))
        
        item_title = item.get('item_name', '')
        if subcat:
            item_display = f"<b>{item_title}</b><br/><font size='8' color='#475569'>Grade/Type: {subcat}</font>"
        else:
            item_display = f"<b>{item_title}</b>"
            
        item_lines.append(item_display)
        hsn_lines.append(hsn)
        qty_lines.append(f"{qty:g} {unit_str}")
        rate_lines.append(f"{rate:,.2f}")
        amt_lines.append(f"{amt:,.2f}")

    items_data.append([
        Paragraph("<br/>".join(sno_lines), style_table_cell_center),
        Paragraph("<br/>".join(item_lines), style_table_cell),
        Paragraph("<br/>".join(hsn_lines), style_table_cell_center),
        Paragraph("<br/>".join(qty_lines), style_table_cell_center),
        Paragraph("<br/>".join(rate_lines), style_table_cell_right),
        Paragraph("<br/>".join(amt_lines), style_table_cell_right)
    ])

    # Optional Freight / Fare Line if present
    if freight_val > 0:
        sac_code = "9965"
        if sac_code not in hsn_tax_summary:
            hsn_tax_summary[sac_code] = {
                'taxable': 0.0,
                'cgst_rate': 9.0 if cgst_total > 0 else 0.0,
                'cgst_amt': 0.0,
                'sgst_rate': 9.0 if sgst_total > 0 else 0.0,
                'sgst_amt': 0.0,
                'igst_rate': 18.0 if igst_total > 0 else 0.0,
                'igst_amt': 0.0,
            }
        hsn_tax_summary[sac_code]['taxable'] += freight_val
        if igst_total > 0:
            hsn_tax_summary[sac_code]['igst_amt'] += round(freight_val * 0.18, 2)
        else:
            hsn_tax_summary[sac_code]['cgst_amt'] += round(freight_val * 0.09, 2)
            hsn_tax_summary[sac_code]['sgst_amt'] += round(freight_val * 0.09, 2)

        items_data.append([
            Paragraph("<i>Freight / Fare (excl GST)</i>", style_table_cell_right),
            "", "", "",
            Paragraph("-", style_table_cell_center),
            Paragraph(f"Rs. {freight_val:,.2f}", style_table_cell_right)
        ])

    if igst_total > 0:
        items_data.append([
            Paragraph("<i>IGST @ 18%</i>", style_table_cell_right),
            "", "", "",
            Paragraph("-", style_table_cell_center),
            Paragraph(f"Rs. {igst_total:,.2f}", style_table_cell_right)
        ])
    else:
        if cgst_total > 0:
            items_data.append([
                Paragraph("<i>CGST @ 9%</i>", style_table_cell_right),
                "", "", "",
                Paragraph("-", style_table_cell_center),
                Paragraph(f"Rs. {cgst_total:,.2f}", style_table_cell_right)
            ])
        if sgst_total > 0:
            items_data.append([
                Paragraph("<i>SGST @ 9%</i>", style_table_cell_right),
                "", "", "",
                Paragraph("-", style_table_cell_center),
                Paragraph(f"Rs. {sgst_total:,.2f}", style_table_cell_right)
            ])

    if round_off != 0.0:
        items_data.append([
            Paragraph("<i>Round Off</i>", style_table_cell_right),
            "", "", "",
            Paragraph("-", style_table_cell_center),
            Paragraph(f"{round_off:,.2f}", style_table_cell_right)
        ])

    # TOTAL Row
    items_data.append([
        Paragraph("<b>TOTAL</b>", style_table_header),
        "", "",
        Paragraph(f"<b>{total_qty:g}</b>", style_table_cell_center),
        "",
        Paragraph(f"<b>Rs. {grand_total:,.2f}</b>", style_table_cell_right_bold)
    ])

    num_tax_rows = len(items_data) - 2
    item_body_height = 370 - (num_tax_rows * 16)
    if item_body_height < 150:
        item_body_height = 150

    row_heights = [20, item_body_height] + [16] * (len(items_data) - 3) + [20]

    t_items = Table(items_data, colWidths=col_w, rowHeights=row_heights)

    items_table_styles = [
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('LINEBEFORE', (1,0), (1,-1), 0.75, colors.black),
        ('LINEBEFORE', (2,0), (2,-1), 0.75, colors.black),
        ('LINEBEFORE', (3,0), (3,-1), 0.75, colors.black),
        ('LINEBEFORE', (4,0), (4,-1), 0.75, colors.black),
        ('LINEBEFORE', (5,0), (5,-1), 0.75, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('VALIGN', (0,-1), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]

    tax_start_idx = 2
    for r_idx in range(tax_start_idx, len(items_data) - 1):
        items_table_styles.append(('SPAN', (0, r_idx), (3, r_idx)))

    items_table_styles.append(('LINEABOVE', (0, tax_start_idx), (-1, tax_start_idx), 0.75, colors.black))
    items_table_styles.append(('SPAN', (0, -1), (2, -1)))
    items_table_styles.append(('LINEABOVE', (0, -1), (-1, -1), 1, colors.black))
    items_table_styles.append(('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F8FAFC")))

    t_items.setStyle(TableStyle(items_table_styles))
    story.append(t_items)

    # 5. HSN / SAC SUMMARY TABLE
    if igst_total > 0:
        gst_summary_data = [
            [
                Paragraph("<b>HSN/SAC</b>", style_table_header),
                Paragraph("<b>Taxable Value</b>", style_table_header),
                Paragraph("<b>Integrated Tax (IGST)</b>", style_table_header),
                "",
                Paragraph("<b>Total Tax Amount</b>", style_table_header)
            ],
            [
                "", "",
                Paragraph("<b>Rate</b>", style_table_header),
                Paragraph("<b>Amount</b>", style_table_header),
                ""
            ]
        ]

        tot_taxable = 0.0
        tot_igst_sum = 0.0

        for hsn_code, vals in hsn_tax_summary.items():
            taxable = vals['taxable']
            i_amt = vals.get('igst_amt', 0.0)
            tot_taxable += taxable
            tot_igst_sum += i_amt

            gst_summary_data.append([
                Paragraph(hsn_code, style_table_cell_center),
                Paragraph(f"{taxable:,.2f}", style_table_cell_right),
                Paragraph(f"{vals.get('igst_rate', 18.0):g}%", style_table_cell_center),
                Paragraph(f"{i_amt:,.2f}", style_table_cell_right),
                Paragraph(f"Rs. {i_amt:,.2f}", style_table_cell_right)
            ])

        gst_summary_data.append([
            Paragraph("<b>Total</b>", style_table_header),
            Paragraph(f"<b>{tot_taxable:,.2f}</b>", style_table_cell_right_bold),
            "",
            Paragraph(f"<b>{tot_igst_sum:,.2f}</b>", style_table_cell_right_bold),
            Paragraph(f"<b>Rs. {tot_igst_sum:,.2f}</b>", style_table_cell_right_bold)
        ])

        hsn_col_w = [
            printable_width * 0.22,
            printable_width * 0.24,
            printable_width * 0.16,
            printable_width * 0.18,
            printable_width * 0.20
        ]

        t_gst = Table(gst_summary_data, colWidths=hsn_col_w)
        t_gst.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (1, 1)),
            ('SPAN', (2, 0), (3, 0)),
            ('SPAN', (4, 0), (4, 1)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor("#F1F5F9")),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F8FAFC")),
        ]))
        story.append(t_gst)
    else:
        gst_summary_data = [
            [
                Paragraph("<b>HSN/SAC</b>", style_table_header),
                Paragraph("<b>Taxable Value</b>", style_table_header),
                Paragraph("<b>CGST</b>", style_table_header),
                "",
                Paragraph("<b>SGST</b>", style_table_header),
                "",
                Paragraph("<b>Total Tax Amount</b>", style_table_header)
            ],
            [
                "", "",
                Paragraph("<b>Rate</b>", style_table_header),
                Paragraph("<b>Amount</b>", style_table_header),
                Paragraph("<b>Rate</b>", style_table_header),
                Paragraph("<b>Amount</b>", style_table_header),
                ""
            ]
        ]

        tot_taxable = 0.0
        tot_cgst_sum = 0.0
        tot_sgst_sum = 0.0

        for hsn_code, vals in hsn_tax_summary.items():
            taxable = vals['taxable']
            c_amt = vals['cgst_amt']
            s_amt = vals['sgst_amt']
            tot_tax = c_amt + s_amt

            tot_taxable += taxable
            tot_cgst_sum += c_amt
            tot_sgst_sum += s_amt

            gst_summary_data.append([
                Paragraph(hsn_code, style_table_cell_center),
                Paragraph(f"{taxable:,.2f}", style_table_cell_right),
                Paragraph(f"{vals['cgst_rate']:g}%", style_table_cell_center),
                Paragraph(f"{c_amt:,.2f}", style_table_cell_right),
                Paragraph(f"{vals['sgst_rate']:g}%", style_table_cell_center),
                Paragraph(f"{s_amt:,.2f}", style_table_cell_right),
                Paragraph(f"Rs. {tot_tax:,.2f}", style_table_cell_right)
            ])

        gst_summary_data.append([
            Paragraph("<b>Total</b>", style_table_header),
            Paragraph(f"<b>{tot_taxable:,.2f}</b>", style_table_cell_right_bold),
            "",
            Paragraph(f"<b>{tot_cgst_sum:,.2f}</b>", style_table_cell_right_bold),
            "",
            Paragraph(f"<b>{tot_sgst_sum:,.2f}</b>", style_table_cell_right_bold),
            Paragraph(f"<b>Rs. {(tot_cgst_sum + tot_sgst_sum):,.2f}</b>", style_table_cell_right_bold)
        ])

        hsn_col_w = [
            printable_width * 0.18,
            printable_width * 0.18,
            printable_width * 0.10,
            printable_width * 0.14,
            printable_width * 0.10,
            printable_width * 0.14,
            printable_width * 0.16
        ]

        t_gst = Table(gst_summary_data, colWidths=hsn_col_w)
        t_gst.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (1, 0), (1, 1)),
            ('SPAN', (2, 0), (3, 0)),
            ('SPAN', (4, 0), (5, 0)),
            ('SPAN', (6, 0), (6, 1)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor("#F1F5F9")),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F8FAFC")),
        ]))
        story.append(t_gst)

    # 6. TOTAL IN WORDS BOX
    words_str = number_to_words_indian(grand_total)
    words_text = f"<b>Total Purchase Amount (in words)</b><br/>{words_str}"

    t_words = Table([[Paragraph(words_text, style_body)]], colWidths=[printable_width])
    t_words.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_words)

    # 7. FOOTER (NOTES & SIGNATORY)
    terms_list = company.get('terms', [])
    terms_body = "<br/>".join(terms_list) if isinstance(terms_list, list) else str(terms_list)
    terms_text = f"""
    <b>Purchase Notes & Verification</b><br/>
    1. Goods received in sound condition and verified against purchase order specifications.<br/>
    2. Stock inventory balance updated automatically in system ledger.
    """

    sign_text = f"""
    <br/><br/>
    <b>Authorised Signatory For</b><br/>
    {comp_name}
    """

    t_footer = Table([
        [
            Paragraph(terms_text, style_body),
            Paragraph(sign_text, style_table_cell_center)
        ]
    ], colWidths=[printable_width * 0.70, printable_width * 0.30])

    t_footer.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_footer)

    doc.build(story)
    return str(filename)


def generate_customer_po_pdf(po, customer, items, dispatches=None, company=None, page_size="A4", filename=None):
    """
    Generates a professional Customer Purchase Order (Party PO) PDF Statement matching the proforma layout:
    - Customer / Party as Buyer / Client
    - Company as Supplier / Seller
    - Line items with Subcategory/Grade, Ordered KG, Rate, and GST breakdown
    - Dispatched & Balance status summary
    - Authorized Signatory and Terms
    """
    if company is None:
        try:
            from models.company import CompanyModel
            company = CompanyModel.get_profile()
        except Exception:
            company = COMPANY_PROFILE

    page_dim = A4 if page_size.upper() == "A4" else LETTER
    width, height = page_dim

    if filename is None:
        po_num_clean = str(po.get('po_number', 'CPO-001')).replace('/', '_')
        filename = INVOICES_DIR / f"Party_PO_{po_num_clean}_{page_size.upper()}.pdf"
    else:
        filename = Path(filename)

    margin = 12
    printable_width = width - (margin * 2)

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=page_dim,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    story = []
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle('CPOTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=15, textColor=colors.HexColor("#0F172A"))
    style_badge = ParagraphStyle('CPOBadge', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, alignment=2, textColor=colors.HexColor("#475569"))
    style_body = ParagraphStyle('CPOBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor("#0F172A"))
    style_body_bold = ParagraphStyle('CPOBodyBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.HexColor("#0F172A"))
    style_table_header = ParagraphStyle('CPOTH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#0F172A"))
    style_table_cell = ParagraphStyle('CPOTC', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor("#0F172A"))
    style_table_cell_center = ParagraphStyle('CPOTCC', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#0F172A"))
    style_table_cell_right = ParagraphStyle('CPOTCR', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, alignment=2, textColor=colors.HexColor("#0F172A"))
    style_table_cell_right_bold = ParagraphStyle('CPOTCRB', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, alignment=2, textColor=colors.HexColor("#0F172A"))

    # 1. Header Section
    po_status = str(po.get('status', 'Open')).strip()
    header_table = Table([
        [
            Paragraph("<b>CUSTOMER / PARTY PURCHASE ORDER (PO)</b>", style_title),
            Paragraph(f"<font color='#0284c7'><b>[ STATUS: {po_status.upper()} ]</b></font>", style_badge)
        ]
    ], colWidths=[printable_width * 0.6, printable_width * 0.4])

    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)

    # 2. Party (Buyer / Customer) Details & PO Meta Grid
    cust_name = customer.get('name', '') or po.get('customer_name', 'Customer')
    cust_comp = customer.get('company_name', '') or po.get('company_name', '')
    cust_display = cust_comp if cust_comp else cust_name
    if cust_comp and cust_name and cust_comp.lower() != cust_name.lower():
        cust_display = f"{cust_comp} (Attn: {cust_name})"

    cust_addr = customer.get('address', '') or po.get('customer_address', 'N/A')
    cust_gst = customer.get('gstin', '') or po.get('customer_gstin', 'N/A')
    cust_mob = customer.get('phone', '') or po.get('customer_phone', '')
    cust_pan = customer.get('pan', '') or po.get('customer_pan', '')
    cust_email = customer.get('email', '') or po.get('customer_email', '')

    cust_contact_str = ""
    if cust_mob:
        cust_contact_str += f"<b>Mobile:</b> {cust_mob} &nbsp;&nbsp;"
    if cust_email:
        cust_contact_str += f"<b>Email:</b> {cust_email}"

    cust_pan_str = f"<b>PAN:</b> {cust_pan}" if cust_pan else ""

    cust_text = f"""
    <font color='#475569'><b>CUSTOMER / BUYER DETAILS (BILL TO)</b></font><br/>
    <font size='10'><b>{cust_display}</b></font><br/>
    {cust_addr}<br/>
    <b>GSTIN:</b> {cust_gst} &nbsp;&nbsp; {cust_pan_str}<br/>
    {cust_contact_str}
    """

    po_no = po.get('po_number', '')
    po_date = po.get('po_date', '')
    tgt_date = po.get('target_delivery_date', 'N/A')

    meta_text_1 = f"<b>PO Ref No.</b><br/>{po_no}"
    meta_text_2 = f"<b>PO Date</b><br/>{po_date}"
    meta_text_3 = f"<b>Target Date</b><br/>{tgt_date}"
    meta_text_4 = f"<b>Order Status:</b> {po_status.upper()}"
    meta_text_5 = f"<b>Notes / Delivery Terms:</b> {po.get('notes', 'Standard terms apply')}"

    t_meta_right = Table([
        [Paragraph(meta_text_1, style_table_cell_center), Paragraph(meta_text_2, style_table_cell_center), Paragraph(meta_text_3, style_table_cell_center)],
        [Paragraph(meta_text_4, style_body_bold), "", ""],
        [Paragraph(meta_text_5, style_body), "", ""]
    ], colWidths=[printable_width * 0.16, printable_width * 0.17, printable_width * 0.17])

    t_meta_right.setStyle(TableStyle([
        ('SPAN', (0, 1), (2, 1)),
        ('SPAN', (0, 2), (2, 2)),
        ('INNERGRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    t_cust_grid = Table([
        [Paragraph(cust_text, style_body), t_meta_right]
    ], colWidths=[printable_width * 0.5, printable_width * 0.5])

    t_cust_grid.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (0, 0), 4),
        ('BOTTOMPADDING', (0, 0), (0, 0), 4),
        ('LEFTPADDING', (0, 0), (0, 0), 5),
        ('RIGHTPADDING', (0, 0), (0, 0), 5),
        ('TOPPADDING', (1, 0), (1, 0), 0),
        ('BOTTOMPADDING', (1, 0), (1, 0), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 0),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
    ]))
    story.append(t_cust_grid)

    # 3. Seller (Company Details - Bill From)
    comp_name = company.get('name', '')
    comp_addr = company.get('address', '')
    comp_gst = company.get('gstin', '')
    comp_mob = company.get('mobile', '')
    comp_pan = company.get('pan', '')
    comp_email = company.get('email', '')
    comp_udyam = company.get('udyam_reg_no', 'UDYAM-UP-18-0048627') or 'UDYAM-UP-18-0048627'

    seller_text = f"""
    <font color='#475569'><b>SELLER / SUPPLIER (BILL FROM)</b></font><br/>
    <b>{comp_name}</b><br/>
    <b>Address:</b> {comp_addr}<br/>
    <b>GSTIN:</b> {comp_gst} &nbsp;&nbsp; <b>PAN:</b> {comp_pan}<br/>
    <b>Mobile:</b> {comp_mob} &nbsp;&nbsp; <b>Email:</b> {comp_email}
    """

    seller_extra = f"""
    <font color='#475569'><b>DISPATCH & MANUFACTURING FACILITY</b></font><br/>
    <b>{comp_name}</b><br/>
    <b>Works:</b> {comp_addr}<br/>
    <b>UDYAM REG. NO.:</b> {comp_udyam}
    """

    t_seller = Table([
        [Paragraph(seller_text, style_body), Paragraph(seller_extra, style_body)]
    ], colWidths=[printable_width * 0.5, printable_width * 0.5])

    t_seller.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_seller)

    # 4. Main Items Table
    col_w = [
        30,                   # S.NO.
        200,                  # ITEMS
        65,                   # ORDERED QTY
        65,                   # DISPATCHED
        65,                   # BALANCE
        70,                   # RATE
        printable_width - 495 # AMOUNT (76.27pt)
    ]

    items_data = [
        [
            Paragraph("<b>S.NO.</b>", style_table_header),
            Paragraph("<b>PRODUCT DESCRIPTION & GRADE</b>", style_table_header),
            Paragraph("<b>ORDERED</b>", style_table_header),
            Paragraph("<b>DISPATCH</b>", style_table_header),
            Paragraph("<b>BALANCE</b>", style_table_header),
            Paragraph("<b>RATE (₹)</b>", style_table_header),
            Paragraph("<b>AMOUNT (₹)</b>", style_table_header)
        ]
    ]

    sno_lines = []
    item_lines = []
    ord_lines = []
    disp_lines = []
    bal_lines = []
    rate_lines = []
    amt_lines = []

    tot_ord_qty = 0.0
    tot_disp_qty = 0.0
    tot_bal_qty = 0.0

    for idx, item in enumerate(items, start=1):
        ord_qty = float(item.get('ordered_qty_kg', item.get('quantity', 0)))
        disp_qty = float(item.get('dispatched_qty_kg', 0))
        bal_qty = max(0.0, ord_qty - disp_qty)
        rate = float(item.get('unit_price', item.get('unit_cost', 0)))
        amt = float(item.get('total_amount', ord_qty * rate))
        unit_str = item.get('unit', 'KG')
        subcat = str(item.get('subcategory', '')).strip()

        tot_ord_qty += ord_qty
        tot_disp_qty += disp_qty
        tot_bal_qty += bal_qty

        sno_lines.append(str(idx))
        item_title = item.get('item_name', '')
        if subcat:
            item_display = f"<b>{item_title}</b><br/><font size='8' color='#475569'>Grade: {subcat}</font>"
        else:
            item_display = f"<b>{item_title}</b>"
            
        item_lines.append(item_display)
        ord_lines.append(f"{ord_qty:g} {unit_str}")
        disp_lines.append(f"{disp_qty:g} {unit_str}")
        bal_lines.append(f"{bal_qty:g} {unit_str}")
        rate_lines.append(f"{rate:,.2f}")
        amt_lines.append(f"{amt:,.2f}")

    items_data.append([
        Paragraph("<br/>".join(sno_lines), style_table_cell_center),
        Paragraph("<br/>".join(item_lines), style_table_cell),
        Paragraph("<br/>".join(ord_lines), style_table_cell_center),
        Paragraph("<br/>".join(disp_lines), style_table_cell_center),
        Paragraph("<br/>".join(bal_lines), style_table_cell_center),
        Paragraph("<br/>".join(rate_lines), style_table_cell_right),
        Paragraph("<br/>".join(amt_lines), style_table_cell_right)
    ])

    subtotal_val = float(po.get('subtotal', 0.0))
    cgst_total = float(po.get('cgst_amount', 0.0))
    sgst_total = float(po.get('sgst_amount', 0.0))
    grand_total = float(po.get('total_po_amount', subtotal_val + cgst_total + sgst_total))

    if cgst_total > 0:
        items_data.append([
            Paragraph("<i>CGST @ 9%</i>", style_table_cell_right),
            "", "", "", "",
            Paragraph("-", style_table_cell_center),
            Paragraph(f"Rs. {cgst_total:,.2f}", style_table_cell_right)
        ])

        items_data.append([
            Paragraph("<i>SGST @ 9%</i>", style_table_cell_right),
            "", "", "", "",
            Paragraph("-", style_table_cell_center),
            Paragraph(f"Rs. {sgst_total:,.2f}", style_table_cell_right)
        ])

    # TOTAL Row
    items_data.append([
        Paragraph("<b>TOTAL</b>", style_table_header),
        "",
        Paragraph(f"<b>{tot_ord_qty:g}</b>", style_table_cell_center),
        Paragraph(f"<b>{tot_disp_qty:g}</b>", style_table_cell_center),
        Paragraph(f"<b>{tot_bal_qty:g}</b>", style_table_cell_center),
        "",
        Paragraph(f"<b>Rs. {grand_total:,.2f}</b>", style_table_cell_right_bold)
    ])

    num_tax_rows = len(items_data) - 2
    item_body_height = 360 - (num_tax_rows * 16)
    if item_body_height < 140:
        item_body_height = 140

    row_heights = [20, item_body_height] + [16] * (len(items_data) - 3) + [20]

    t_items = Table(items_data, colWidths=col_w, rowHeights=row_heights)

    items_table_styles = [
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('LINEBEFORE', (1,0), (1,-1), 0.75, colors.black),
        ('LINEBEFORE', (2,0), (2,-1), 0.75, colors.black),
        ('LINEBEFORE', (3,0), (3,-1), 0.75, colors.black),
        ('LINEBEFORE', (4,0), (4,-1), 0.75, colors.black),
        ('LINEBEFORE', (5,0), (5,-1), 0.75, colors.black),
        ('LINEBEFORE', (6,0), (6,-1), 0.75, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('VALIGN', (0,-1), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]

    tax_start_idx = 2
    for r_idx in range(tax_start_idx, len(items_data) - 1):
        items_table_styles.append(('SPAN', (0, r_idx), (4, r_idx)))

    items_table_styles.append(('LINEABOVE', (0, tax_start_idx), (-1, tax_start_idx), 0.75, colors.black))
    items_table_styles.append(('SPAN', (0, -1), (1, -1)))
    items_table_styles.append(('LINEABOVE', (0, -1), (-1, -1), 1, colors.black))
    items_table_styles.append(('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F8FAFC")))

    t_items.setStyle(TableStyle(items_table_styles))
    story.append(t_items)

    # 5. TOTAL IN WORDS BOX
    words_str = number_to_words_indian(grand_total)
    words_text = f"<b>Total PO Amount (in words)</b><br/>{words_str}"

    t_words = Table([[Paragraph(words_text, style_body)]], colWidths=[printable_width])
    t_words.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_words)

    # 6. FOOTER (TERMS & SIGNATORY)
    terms_text = f"""
    <b>Order Terms & Delivery Conditions</b><br/>
    1. Delivery to be executed in batches or as per mutual release orders.<br/>
    2. Tax invoices to be issued corresponding to each dispatched consignment.
    """

    sign_text = f"""
    <br/><br/>
    <b>Authorised Signatory For</b><br/>
    {comp_name}
    """

    t_footer = Table([
        [
            Paragraph(terms_text, style_body),
            Paragraph(sign_text, style_table_cell_center)
        ]
    ], colWidths=[printable_width * 0.70, printable_width * 0.30])

    t_footer.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_footer)

    doc.build(story)
    return str(filename)


