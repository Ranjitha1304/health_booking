from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from datetime import datetime

def create_medical_response_pdf(report, response, patient_info=None, doctor_info=None):
    """Create a professional medical response PDF"""
    
    # Create buffer for PDF
    buffer = BytesIO()
    
    # Create document with A4 size
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#283593'),
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#1565c0'),
        spaceAfter=8,
        spaceBefore=15,
        leftIndent=0,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'NormalJustified',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#263238'),
        leading=12,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    highlight_style = ParagraphStyle(
        'Highlight',
        parent=normal_style,
        backColor=colors.HexColor('#e3f2fd'),
        borderPadding=5,
        borderColor=colors.HexColor('#bbdefb'),
        borderWidth=1
    )
    
    # Story to hold flowables
    story = []
    
    # Header with decorative line
    header_table = Table([
        ['HEALTHCARE CONSULTATION SYSTEM', 'CONFIDENTIAL MEDICAL REPORT'],
        ['', '']
    ], colWidths=[doc.width/2.0]*2)
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.HexColor('#1a237e')),
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#e0e0e0')),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Main Title
    story.append(Paragraph("COMPREHENSIVE MEDICAL CONSULTATION REPORT", title_style))
    story.append(Spacer(1, 25))
    
    # Patient and Doctor Information Section
    story.append(Paragraph("PATIENT & CONSULTANT INFORMATION", section_title_style))
    
    # Patient details - using available fields
    patient_name = patient_info.get('full_name', 'Not specified') if patient_info else report.patient.get_full_name() or 'Not specified'
    
    patient_details = [
        f"Patient Name: {patient_name}"
    ]
    
    # Doctor details
    doc_name = doctor_info.get('full_name', 'Not specified') if doctor_info else response.doctor.get_full_name() or 'Not specified'
    
    doctor_details = [
        f"Consultant Name: Dr. {doc_name}"
    ]
    
    # Create info table with better styling
    info_data = [
        ['PATIENT INFORMATION', 'CONSULTANT INFORMATION'],
        ['<br/>'.join(patient_details), '<br/>'.join(doctor_details)]
    ]
    
    info_table = Table(info_data, colWidths=[doc.width/2.0]*2)
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdbdbd')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 25))
    
    # Report Information
    story.append(Paragraph("REPORT DETAILS", section_title_style))
    report_data = [
        ['Report Title', report.title],
        ['Medical Category', report.get_category_display()],
        ['Report Upload Date', report.uploaded_at.strftime("%B %d, %Y at %I:%M %p")],
        ['Consultation Date', response.created_at.strftime("%B %d, %Y at %I:%M %p")]
    ]
    
    report_table = Table(report_data, colWidths=[doc.width/3.0, doc.width*2/3.0])
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#263238')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(report_table)
    story.append(Spacer(1, 25))
    
    # Medical Findings and Diagnosis Section
    story.append(Paragraph("MEDICAL DIAGNOSIS & FINDINGS", section_title_style))
    diagnosis_text = response.diagnosis.replace('\n', '<br/>') if response.diagnosis else "No diagnosis provided."
    story.append(Paragraph(diagnosis_text, highlight_style))
    story.append(Spacer(1, 20))
    
    # Prescription Section
    story.append(Paragraph("PRESCRIPTION DETAILS", section_title_style))
    
    # Parse prescription - check if it can be formatted as a table
    prescription_text = response.prescription.strip() if response.prescription else "No prescription provided."
    lines = prescription_text.split('\n')
    
    # Check if any line contains pipe separator (suggested format)
    has_table_format = any('|' in line for line in lines if line.strip())
    
    if has_table_format and len(lines) > 1:
        # Create prescription table
        prescription_data = [['<b>Medication</b>', '<b>Dosage</b>', '<b>Frequency</b>', '<b>Duration</b>']]
        
        for line in lines:
            line = line.strip()
            if line:
                if '|' in line:
                    parts = [part.strip() for part in line.split('|')]
                    # Ensure we have exactly 4 columns
                    while len(parts) < 4:
                        parts.append('')
                    if len(parts) > 4:
                        parts = parts[:4]
                    prescription_data.append(parts)
                else:
                    # If no pipe but we're in table mode, put in first column
                    prescription_data.append([line, '', '', ''])
        
        if len(prescription_data) > 1:  # If we have data beyond header
            prescription_table = Table(prescription_data, colWidths=[doc.width/4.0]*4)
            prescription_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d47a1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbdefb')),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(prescription_table)
        else:
            story.append(Paragraph(prescription_text.replace('\n', '<br/>'), normal_style))
    else:
        # Display as regular text
        story.append(Paragraph(prescription_text.replace('\n', '<br/>'), normal_style))
    
    story.append(Spacer(1, 20))
    
    # Recommendations Section
    story.append(Paragraph("RECOMMENDATIONS & FOLLOW-UP INSTRUCTIONS", section_title_style))
    recommendations_text = response.recommendations.replace('\n', '<br/>') if response.recommendations else "No recommendations provided."
    story.append(Paragraph(recommendations_text, highlight_style))
    story.append(Spacer(1, 20))
    
    # Medical Advice Section
    if response.advice and response.advice.strip():
        story.append(Paragraph("MEDICAL ADVICE & PRECAUTIONS", section_title_style))
        story.append(Paragraph(response.advice.replace('\n', '<br/>'), normal_style))
        story.append(Spacer(1, 20))
    
    # Page break if needed
    story.append(PageBreak())
    
    # Important Medical Information Section
    story.append(Paragraph("IMPORTANT MEDICAL INFORMATION", ParagraphStyle(
        'ImportantTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#c62828'),
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )))
    
    important_notes = [
        ("Confidentiality Notice", "This document contains confidential medical information. Unauthorized disclosure is prohibited."),
        ("Medication Adherence", "Take all medications as prescribed. Do not stop medication without consulting your doctor."),
        ("Side Effects", "Report any unusual symptoms or side effects to your doctor immediately."),
        ("Follow-up Appointments", "Keep all scheduled follow-up appointments for optimal care."),
        ("Emergency Contact", "For medical emergencies, contact emergency services or go to the nearest hospital."),
        ("Lifestyle Recommendations", "Follow dietary, exercise, and lifestyle recommendations as advised."),
        ("Document Storage", "Keep this document with your medical records for future reference."),
        ("Validity", "This consultation is valid until your next scheduled follow-up appointment.")
    ]
    
    for i, (title, content) in enumerate(important_notes, 1):
        story.append(Paragraph(f"{i}. <b>{title}</b>", ParagraphStyle(
            'NoteTitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=3,
            fontName='Helvetica-Bold'
        )))
        story.append(Paragraph(content, ParagraphStyle(
            'NoteContent',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#455a64'),
            spaceAfter=10,
            leftIndent=20
        )))
    
    story.append(Spacer(1, 25))
    
    # Signature Section with decorative border
    signature_data = [
        ['', ''],
        ['______________________________', '______________________________'],
        ['Patient\'s Acknowledgement', 'Doctor\'s Signature'],
        ['', ''],
        ['Date: ________________________', f'Consultation Date: {response.created_at.strftime("%B %d, %Y")}'],
        ['', f'Dr. {doc_name}']
    ]
    
    signature_table = Table(signature_data, colWidths=[doc.width/2.0]*2)
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 2), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 3), 10),
        ('FONTSIZE', (0, 4), (-1, -1), 9),
        ('TEXTCOLOR', (0, 4), (-1, -1), colors.HexColor('#546e7a')),
        ('SPACEAFTER', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (0, 1), (-1, 1), 0.5, colors.HexColor('#1a237e')),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor('#1a237e')),
    ]))
    story.append(signature_table)
    
    story.append(Spacer(1, 30))
    
    # Footer with watermark effect
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#757575'),
        alignment=TA_CENTER
    )
    
    story.append(Paragraph(
        "_________________________________________________________________________________", 
        ParagraphStyle('Line', parent=styles['Normal'], fontSize=6, textColor=colors.gray, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 5))
    story.append(Paragraph("ELECTRONICALLY GENERATED MEDICAL DOCUMENT - VALID WITHOUT PHYSICAL SIGNATURE", footer_style))
    story.append(Paragraph(f"Document Generated: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}", footer_style))
    story.append(Paragraph("Healthcare Consultation System © All Rights Reserved", footer_style))
    story.append(Paragraph(f"Page 1 of 1", footer_style))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF value from buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def generate_pdf_filename(report, response):
    """Generate a professional filename for the PDF"""
    patient_name = report.patient.get_full_name().replace(' ', '_') if report.patient.get_full_name() else f"Patient_{report.patient.id}"
    doctor_name = response.doctor.last_name if response.doctor.last_name else f"Doctor_{response.doctor.id}"
    date_str = response.created_at.strftime("%Y%m%d")
    return f"Medical_Consultation_{patient_name}_{doctor_name}_{date_str}.pdf"