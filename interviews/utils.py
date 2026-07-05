import os
from io import BytesIO
from django.core.files.storage import default_storage
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def calculate_adaptive_difficulty(current_level, recent_scores):
    """
    Adjusts current difficulty level (1-10) based on average performance of recent answers.
    If average score >= 8.0, increase difficulty by 1.
    If average score <= 5.0, decrease difficulty by 1.
    """
    if not recent_scores:
        return current_level
        
    avg_score = sum(recent_scores) / len(recent_scores)
    
    if avg_score >= 8.0:
        new_level = current_level + 1
    elif avg_score <= 5.0:
        new_level = current_level - 1
    else:
        new_level = current_level
        
    # Cap between 1 and 10
    return max(1, min(10, new_level))

def generate_interview_report_pdf(session):
    """
    Builds a structured feedback PDF report for the completed interview session
    using ReportLab flowables, and saves it to media/Cloudinary.
    """
    from .models import Report
    
    # Check if report already exists, update or create
    report, created = Report.objects.get_or_create(session=session)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom color palette matching the brand identity
    brand_primary = colors.HexColor("#6366f1")    # Indigo
    brand_secondary = colors.HexColor("#0f172a")  # Slate dark
    accent_green = colors.HexColor("#10b981")     # Mint
    text_dark = colors.HexColor("#1e293b")
    text_muted = colors.HexColor("#64748b")
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=brand_secondary,
        spaceAfter=12
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=brand_primary,
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_dark
    )
    
    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=brand_primary
    )
    
    muted_style = ParagraphStyle(
        'MutedTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=text_muted
    )
    
    story = []
    
    # --- HEADER / TITLE ---
    story.append(Paragraph("InterviewForge AI - Interview Report", title_style))
    story.append(Paragraph(f"Candidate: {session.user.username}", body_style))
    story.append(Paragraph(f"Interview Focus: {session.interview_type}", body_style))
    story.append(Paragraph(f"Format/Difficulty: {session.difficulty.capitalize()}", body_style))
    story.append(Paragraph(f"Date Completed: {session.created_at.strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(Spacer(1, 15))
    
    # --- PERFORMANCE STATS TABLE ---
    questions_list = session.questions.all()
    total_q = questions_list.count()
    graded_evals = [q.answer.evaluation.overall_score for q in questions_list if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation')]
    avg_score = float(sum(graded_evals) / len(graded_evals)) if graded_evals else 0.0
    
    readiness_rating = int(avg_score * 10)  # Convert 0-10 score to 0-100% readiness
    report.readiness_score = readiness_rating
    
    stats_data = [
        [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Value</b>", body_style)],
        [Paragraph("Total Questions Asked", body_style), Paragraph(str(total_q), body_style)],
        [Paragraph("Average Interview Score", body_style), Paragraph(f"{avg_score:.2f} / 10.0", body_style)],
        [Paragraph("Estimated Job Readiness Score", body_style), Paragraph(f"{readiness_rating}%", body_style)]
    ]
    
    stats_table = Table(stats_data, colWidths=[2.5*inch, 2.5*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 20))
    
    # --- DETAILED QUESTIONS TRANSCRIPT ---
    story.append(Paragraph("Question & Evaluation Log", h2_style))
    
    for idx, q in enumerate(questions_list, start=1):
        q_elements = []
        q_elements.append(Paragraph(f"<b>Round {idx}:</b> {q.question_text}", body_style))
        
        if hasattr(q, 'answer'):
            q_elements.append(Paragraph(f"<i>Candidate Answer:</i> {q.answer.answer_text}", body_style))
            if hasattr(q.answer, 'evaluation'):
                eval_obj = q.answer.evaluation
                q_elements.append(Paragraph(f"<b>Grading Score: {eval_obj.overall_score}/10.0</b> (Tech: {eval_obj.technical_score}, Comm: {eval_obj.communication_score}, Depth: {eval_obj.depth_score})", body_style))
                q_elements.append(Paragraph(f"<b>Missing Concepts:</b> {', '.join(eval_obj.missing_concepts) if eval_obj.missing_concepts else 'None'}", callout_style))
                q_elements.append(Paragraph(f"<b>Ideal Response:</b> {eval_obj.ideal_answer}", body_style))
        else:
            q_elements.append(Paragraph("<i>Candidate did not provide an answer.</i>", muted_style))
            
        q_elements.append(Spacer(1, 10))
        story.append(KeepTogether(q_elements))
        
    # --- BUILD DOCUMENT ---
    doc.build(story)
    
    # Reset buffer cursor before uploading to storage
    buffer.seek(0)
    
    # --- SAVE PDF TO DB STORAGE ---
    pdf_filename = f"reports/report_{session.id}.pdf"
    default_storage.save(pdf_filename, buffer)
    
    report.pdf_url = default_storage.url(pdf_filename)
    report.timeline = [{"round": idx + 1, "score": float(val)} for idx, val in enumerate(graded_evals)]
    
    # Curate some default learning/courses recommendations to log in table
    report.projects_recommended = [
        "Create a structured Python class wrapper enforcing atomic queries",
        "Deploy a Django REST app template containerized under a redis cache instance"
    ]
    report.courses_recommended = [
        "Django REST Framework In-Depth (InterviewForge Academy)",
        "System Architecture Design Bootcamp"
    ]
    
    report.save()
    return report.pdf_url
