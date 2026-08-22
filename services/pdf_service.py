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
    SimpleDocTemplate, Paragraph, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from config import INVOICES_DIR, COMPANY_PROFILE
from services.num2words_service import number_to_words_indian


def generate_tax_invoice_pdf(order, customer, items, company=None, page_size="A4", copy_type="ORIGINAL FOR RECIPIENT", filename=None):
    """
    Generates a professional GST Tax Invoice matching exact user proforma layout:
    - Full A4 Page height
    - No horizontal lines between item rows (only vertical column dividers)
    - 2-level HSN/SAC summary table (CGST Rate|Amount, SGST Rate|Amount)
    - Bank details, Terms & Conditions, and Signatory footer
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

    is_cancelled = str(order.get('status', '')).lower() == 'cancelled' or str(order.get('payment_status', '')).lower() == 'cancelled'
    copy_label = "<font color='#ef4444'><b>[ CANCELLED INVOICE ]</b></font>" if is_cancelled else f"<font color='#475569'><b>{copy_type.upper()}</b></font>"

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
    veh_no = order.get('vehicle_no', 'N/A')
    eway_no = order.get('eway_bill_no', 'N/A')
    pos = order.get('place_of_supply', 'Uttar Pradesh')

    meta_text_1 = f"<b>Invoice No.</b><br/>{inv_no}"
    meta_text_2 = f"<b>Invoice Date</b><br/>{inv_date}"
    meta_text_3 = f"<b>Due Date</b><br/>{due_date}"
    meta_text_4 = f"<b>Vehicle No.:</b> {veh_no if veh_no else 'N/A'}"
    meta_text_5 = f"<b>E-Way Bill No.:</b> {eway_no if eway_no else 'N/A'}"
    meta_text_6 = f"<b>Place of Supply:</b> {pos}"

    t_meta_right = Table([
        [Paragraph(meta_text_1, style_table_cell_center), Paragraph(meta_text_2, style_table_cell_center), Paragraph(meta_text_3, style_table_cell_center)],
        [Paragraph(meta_text_4, style_body_bold), "", ""],
        [Paragraph(meta_text_5, style_body_bold), "", ""],
        [Paragraph(meta_text_6, style_body_bold), "", ""]
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
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
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

    for idx, item in enumerate(items, start=1):
        qty = float(item.get('quantity', 0))
        rate = float(item.get('unit_price', 0))
        amt = float(item.get('amount', qty * rate))
        unit_str = item.get('unit', 'PCS')
        hsn = str(item.get('hsn_code', '00000000'))

        total_qty += qty

        cgst_r = float(item.get('cgst_rate', 9.0))
        sgst_r = float(item.get('sgst_rate', 9.0))
        cgst_amt = round(amt * (cgst_r / 100.0), 2)
        sgst_amt = round(amt * (sgst_r / 100.0), 2)

        if hsn not in hsn_tax_summary:
            hsn_tax_summary[hsn] = {
                'taxable': 0.0,
                'cgst_rate': cgst_r,
                'cgst_amt': 0.0,
                'sgst_rate': sgst_r,
                'sgst_amt': 0.0,
            }
        hsn_tax_summary[hsn]['taxable'] += amt
        hsn_tax_summary[hsn]['cgst_amt'] += cgst_amt
        hsn_tax_summary[hsn]['sgst_amt'] += sgst_amt

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

    cgst_total = float(order.get('cgst_amount', 0.0))
    sgst_total = float(order.get('sgst_amount', 0.0))
    round_off = float(order.get('round_off', 0.0))
    grand_total = float(order.get('total_amount', 0.0))

    # Optional Freight / Fare Line if present
    freight_val = float(order.get('freight', 0.0))
    if freight_val > 0:
        f_cgst = round(freight_val * 0.09, 2)
        f_sgst = round(freight_val * 0.09, 2)
        sac_code = "9965"
        if sac_code not in hsn_tax_summary:
            hsn_tax_summary[sac_code] = {
                'taxable': 0.0,
                'cgst_rate': 9.0,
                'cgst_amt': 0.0,
                'sgst_rate': 9.0,
                'sgst_amt': 0.0,
            }
        hsn_tax_summary[sac_code]['taxable'] += freight_val
        hsn_tax_summary[sac_code]['cgst_amt'] += f_cgst
        hsn_tax_summary[sac_code]['sgst_amt'] += f_sgst

        items_data.append([
            Paragraph("<i>Freight / Fare (excl 18% GST)</i>", style_table_cell_right),
            "", "", "",
            Paragraph("-", style_table_cell_center),
            Paragraph(f"Rs. {freight_val:,.2f}", style_table_cell_right)
        ])

    # Tax Calculation Lines
    items_data.append([
        Paragraph("<i>CGST @ 9%</i>", style_table_cell_right),
        "", "", "",
        Paragraph("-", style_table_cell_center),
        Paragraph(f"Rs. {cgst_total:,.2f}", style_table_cell_right)
    ])

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
        ('BOX', (0,0), (-1,-1), 1, colors.black),
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

    doc.build(story)
    return str(filename)
