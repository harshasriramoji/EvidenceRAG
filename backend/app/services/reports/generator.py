import os
import uuid
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.app.core.config import settings
from backend.app.models.entities import VerificationResult, Report, Document

def draw_report_decorations(canvas_obj, doc_obj):
    """Draw page header and footer decorations."""
    canvas_obj.saveState()
    w, h = A4

    # Top banner bar
    canvas_obj.setFillColor(colors.HexColor("#0B192C"))
    canvas_obj.rect(0, h - 25, w, 25, fill=1, stroke=0)
    canvas_obj.setFillColor(colors.HexColor("#026FC3"))
    canvas_obj.rect(0, h - 28, w, 3, fill=1, stroke=0)

    # Header text
    canvas_obj.setFont("Helvetica-Bold", 9)
    canvas_obj.setFillColor(colors.white)
    canvas_obj.drawString(40, h - 17, "EvidenceRAG — Explainable Pre-Submission Verification System")

    # Footer
    canvas_obj.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(40, 30, w - 40, 30)

    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.HexColor("#64748B"))
    canvas_obj.drawString(40, 18, "Confidential Pre-Submission Audit Report • Powered by Retrieval-Augmented Generation")
    page_num = canvas_obj.getPageNumber()
    canvas_obj.drawRightString(w - 40, 18, f"Page {page_num}")

    canvas_obj.restoreState()

class ReportGenerator:
    """
    Generates downloadable, publication-grade PDF Verification Reports using ReportLab.
    """

    @staticmethod
    def generate_pdf_report(verification: VerificationResult, db: Session) -> Report:
        report_uuid = f"RPT-{datetime.date.today().strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"
        file_path = settings.REPORTS_DIR / f"{report_uuid}.pdf"

        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=45,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'RptTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0B192C"),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'RptSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#026FC3"),
            spaceAfter=15
        )
        h2_style = ParagraphStyle(
            'RptH2',
            parent=styles['Heading2'],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'RptBody',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )
        bold_style = ParagraphStyle(
            'RptBold',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#0F172A")
        )

        story = []

        # Header Title
        story.append(Paragraph("EvidenceRAG Verification Audit Report", title_style))
        story.append(Paragraph("Automated Pre-Submission Compliance & Cross-Document Consistency Analysis", subtitle_style))

        # Status badge color mapping
        status_colors = {
            "Passed": colors.HexColor("#10B981"),
            "Passed with Warnings": colors.HexColor("#F59E0B"),
            "Needs Correction": colors.HexColor("#EF4444"),
            "Manual Review Required": colors.HexColor("#6366F1"),
            "Processing Failed": colors.HexColor("#64748B")
        }
        status_bg = status_colors.get(verification.overall_status, colors.HexColor("#64748B"))

        # Metadata Summary Card
        meta_data = [
            [
                Paragraph("<b>Report ID:</b>", bold_style), Paragraph(report_uuid, body_style),
                Paragraph("<b>Verification Mode:</b>", bold_style), Paragraph(verification.verification_mode.title(), body_style)
            ],
            [
                Paragraph("<b>Date Generated:</b>", bold_style), Paragraph(datetime.datetime.utcnow().strftime("%d %B %Y, %H:%M UTC"), body_style),
                Paragraph("<b>Overall Status:</b>", bold_style), Paragraph(f"<b><font color='white'>{verification.overall_status}</font></b>", bold_style)
            ],
            [
                Paragraph("<b>Applicant Email:</b>", bold_style), Paragraph(verification.user.email if verification.user else "N/A", body_style),
                Paragraph("<b>Issues Identified:</b>", bold_style), Paragraph(f"{verification.critical_issues} Critical, {verification.warning_issues} Warnings", body_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[100, 160, 110, 150])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (3, 1), (3, 1), status_bg),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 12))

        # Executive Summary
        story.append(Paragraph("1. Executive Verification Summary", h2_style))
        story.append(Paragraph(verification.summary or "Verification audit completed.", body_style))
        story.append(Spacer(1, 10))

        # Documents Included
        import json
        doc_ids = []
        try:
            doc_ids = json.loads(verification.document_ids)
        except Exception:
            pass

        docs = db.query(Document).filter(Document.id.in_(doc_ids)).all() if doc_ids else []
        if docs:
            story.append(Paragraph("2. Evaluated Document Credentials", h2_style))
            doc_table_data = [
                [Paragraph("<b>File Name</b>", bold_style), Paragraph("<b>Category</b>", bold_style), Paragraph("<b>Quality</b>", bold_style), Paragraph("<b>OCR Readability</b>", bold_style)]
            ]
            for d in docs:
                qual_str = f"Score: {d.image_quality_score}"
                if d.is_blurry: qual_str += " (Blurry)"
                if d.is_low_res: qual_str += " (Low Res)"
                doc_table_data.append([
                    Paragraph(d.original_filename, body_style),
                    Paragraph(d.category, body_style),
                    Paragraph(qual_str, body_style),
                    Paragraph(f"{len(d.raw_text.split() if d.raw_text else 0)} words extracted", body_style)
                ])

            doc_table = Table(doc_table_data, colWidths=[180, 130, 110, 100])
            doc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(doc_table)
            story.append(Spacer(1, 12))

        # Cross Document Comparison Results (Mode B)
        if verification.cross_comparisons:
            story.append(Paragraph("3. Cross-Document Field Comparison Matrix", h2_style))
            cmp_data = [
                [
                    Paragraph("<b>Field</b>", bold_style),
                    Paragraph("<b>Document A</b>", bold_style),
                    Paragraph("<b>Document B</b>", bold_style),
                    Paragraph("<b>Match / Score</b>", bold_style)
                ]
            ]
            for c in verification.cross_comparisons:
                match_txt = f"<font color='{'#10B981' if c.is_match else '#EF4444'}'><b>{'MATCH' if c.is_match else 'MISMATCH'}</b> ({int(c.similarity_score * 100)}%)</font>"
                cmp_data.append([
                    Paragraph(f"<b>{c.field_name}</b>", bold_style),
                    Paragraph(f"{c.doc_a_name[:25]}...<br/><b>Value:</b> {c.val_a or 'null'}", body_style),
                    Paragraph(f"{c.doc_b_name[:25]}...<br/><b>Value:</b> {c.val_b or 'null'}", body_style),
                    Paragraph(match_txt, body_style)
                ])

            cmp_table = Table(cmp_data, colWidths=[90, 160, 160, 110])
            cmp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#026FC3')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(cmp_table)
            story.append(Spacer(1, 12))

        # Detected Issues and RAG Grounded Explanations
        story.append(Paragraph(f"{'4' if verification.cross_comparisons else '3'}. Detected Issues & Explainable RAG Guidance", h2_style))
        if not verification.issues:
            story.append(Paragraph("<b>No compliance defects detected.</b> All evaluated fields satisfied mandatory criteria.", body_style))
        else:
            for idx, iss in enumerate(verification.issues, 1):
                sev_color = colors.HexColor("#EF4444") if iss.severity == "critical" else (
                    colors.HexColor("#F59E0B") if iss.severity in ("high", "medium") else colors.HexColor("#026FC3")
                )
                
                issue_box = [
                    [
                        Paragraph(f"<b>Issue #{idx}: {iss.title}</b>", bold_style),
                        Paragraph(f"<b><font color='{sev_color}'>{iss.severity.upper()}</font></b>", bold_style)
                    ],
                    [
                        Paragraph(f"<b>Document:</b> {iss.document_name or 'Uploaded File'}", body_style),
                        Paragraph(f"<b>Category:</b> {iss.category.replace('_', ' ').title()}", body_style)
                    ],
                    [
                        Paragraph(f"<b>Expected:</b> {iss.expected_value or 'N/A'}", body_style),
                        Paragraph(f"<b>Actual:</b> {iss.actual_value or 'N/A'}", body_style)
                    ],
                    [
                        Paragraph(f"<b>Evidence:</b> <i>{iss.evidence_snippet or 'None'}</i>", body_style),
                        Paragraph(f"<b>Manual Review:</b> {'Recommended' if iss.manual_review_recommended else 'Not Required'}", body_style)
                    ],
                    [
                        Paragraph(f"<b>RAG Grounded Explanation:</b><br/>{iss.explanation}", body_style),
                        Paragraph(f"<b>Recommended Correction:</b><br/>{iss.suggested_correction}", body_style)
                    ],
                    [
                        Paragraph(f"<b>Regulatory Source:</b> <font color='#026FC3'>{iss.rag_source or 'Scholarship Verification Guidelines'}</font>", body_style),
                        Paragraph(f"<b>Rule Code:</b> {iss.rag_rule_id or 'RULE-GEN'}", body_style)
                    ]
                ]
                iss_table = Table(issue_box, colWidths=[260, 260])
                iss_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
                    ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#CBD5E1')),
                    ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#E2E8F0')),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('SPAN', (0, 4), (0, 4)),
                    ('SPAN', (1, 4), (1, 4)),
                ]))
                story.append(iss_table)
                story.append(Spacer(1, 8))

        # Legal & Assistive Disclaimer
        story.append(Spacer(1, 10))
        disclaimer_text = """
        <b>ASSISTIVE PRE-SUBMISSION AUDIT DISCLAIMER:</b><br/>
        EvidenceRAG is an artificial intelligence decision-support tool created to assist scholarship applicants 
        in discovering clerical oversights and documentation discrepancies prior to final submission. 
        Automated findings, OCR quality warnings, or missing signature alerts <b>never</b> constitute a declaration 
        of fraudulent intent or document invalidity. Final determination rests exclusively with institutional review boards.
        """
        disclaimer_table = Table([[Paragraph(disclaimer_text, body_style)]], colWidths=[520])
        disclaimer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(disclaimer_table)

        # Build document
        doc.build(story, onFirstPage=draw_report_decorations, onLaterPages=draw_report_decorations)

        # Create Report DB record
        report_record = Report(
            verification_id=verification.id,
            user_id=verification.user_id,
            report_uuid=report_uuid,
            file_path=str(file_path),
            file_size=file_path.stat().st_size
        )
        db.add(report_record)
        db.commit()
        db.refresh(report_record)

        return report_record

    @classmethod
    def generate_correction_checklist_pdf(cls, user: Any, db: Session) -> Report:
        """Generate a concise, action-oriented correction checklist PDF for the student."""
        from backend.app.models.entities import Issue, Document, VerificationResult

        user_docs = db.query(Document).filter(Document.user_id == user.id).all()
        doc_ids = [d.id for d in user_docs]
        issues = db.query(Issue).filter(Issue.document_id.in_(doc_ids)).all() if doc_ids else []

        latest_verification = db.query(VerificationResult).filter(
            VerificationResult.user_id == user.id
        ).order_by(VerificationResult.created_at.desc()).first()

        v_id = latest_verification.id if latest_verification else 1
        checklist_uuid = f"CHECKLIST-{uuid.uuid4().hex[:8].upper()}"
        file_path = settings.REPORTS_DIR / f"{checklist_uuid}.pdf"

        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=45,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ChecklistTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'ChecklistSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#475569'),
            spaceAfter=12
        )
        body_style = ParagraphStyle(
            'ChecklistBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#0F172A')
        )
        bold_style = ParagraphStyle(
            'ChecklistBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#0F172A')
        )

        story = []
        story.append(Paragraph("Scholarship Pre-Submission Action Checklist", title_style))
        story.append(Paragraph(f"Applicant: <b>{user.email}</b> • Generated on: {datetime.datetime.now(datetime.timezone.utc).strftime('%d %B %Y, %H:%M UTC')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=12))

        if issues:
            story.append(Paragraph("<b>Required Document Corrections & Statutory Remediations:</b>", bold_style))
            story.append(Spacer(1, 6))

            data = [["[ ]", "Document & Page", "Issue Title & Severity", "Recommended Action / Fix", "Statutory Reference"]]
            for iss in issues:
                data.append([
                    "[ ]",
                    Paragraph(f"{iss.document_name}<br/><font color='#64748B'>Page {iss.page_number or 1}</font>", body_style),
                    Paragraph(f"<b>{iss.title}</b><br/><font color='{colors.HexColor('#DC2626') if iss.severity.lower() == 'critical' else colors.HexColor('#D97706')}'>[{iss.severity.upper()}]</font>", body_style),
                    Paragraph(iss.suggested_correction, body_style),
                    Paragraph(iss.rag_source or "Portal Norms", body_style)
                ])

            t = Table(data, colWidths=[25, 110, 140, 160, 80])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EFF6FF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1D4ED8')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
        else:
            story.append(Paragraph("<b>Status: All uploaded credentials satisfy statutory compliance criteria! Zero pending actions.</b>", bold_style))

        story.append(Spacer(1, 20))
        story.append(Paragraph("<i>Note: This checklist is generated for applicant pre-submission guidance and does not represent an official government grant confirmation.</i>", subtitle_style))

        doc.build(story, onFirstPage=draw_report_decorations, onLaterPages=draw_report_decorations)

        report_record = Report(
            verification_id=v_id,
            user_id=user.id,
            report_uuid=checklist_uuid,
            file_path=str(file_path),
            file_size=file_path.stat().st_size
        )
        db.add(report_record)
        db.commit()
        db.refresh(report_record)
        return report_record

