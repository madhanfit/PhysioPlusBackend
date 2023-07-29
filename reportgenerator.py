import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, PageTemplate, BaseDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, Frame, PageBreak
from reportlab.pdfgen import canvas
from io import BytesIO

def create_pain_scale_graph(painscales, dates):
    fig = go.Figure(data=go.Scatter(x=dates, y=painscales, mode='lines+markers'))
    fig.update_layout(title_text='Pain Scale Graph', xaxis_title='Date', yaxis_title='Pain Scale')
    return fig.to_image(format='png')

def create_pdf(name, age, gender, referred_by, chief_complaint, previous_treatment, diagnosis, duration,
               treatment_given, treatment_dates, painscales, advised_exercise, home_advice, next_review):
    doc = SimpleDocTemplate("hospital_report.pdf", pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)

    # Create custom page template with borders
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='test', frames=frame, onPage=draw_page_border)
    doc.addPageTemplates([template])

    # Styles for the headings and subheadings
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18, textColor=colors.blue, alignment=1)
    heading_style = ParagraphStyle("Heading1", parent=styles["Heading2"], fontSize=14, textColor=colors.blue, alignment=1)
    subheading_style = ParagraphStyle("Subheading", parent=styles["Heading3"], spaceAfter=6)

    # Data for the table
    data = [
        ["Name", name],
        ["Age", age],
        ["Gender", gender],
        ["Referred by", referred_by],
        ["Chief Complaint", chief_complaint],
        ["Previous Treatment Taken", previous_treatment],
        ["Diagnosis", diagnosis],
        ["Duration", duration],
        ["Treatment Given", treatment_given],
        ["No of Days Treatment Taken / Date", "\n".join(treatment_dates)],
        ["Advised Exercise", advised_exercise],
        ["Home Advice", home_advice],
        ["Next Review", next_review],
    ]

    # Create the pain scale graph
    graph = create_pain_scale_graph(painscales, treatment_dates)
    img_buffer = BytesIO(graph)
    pain_scale_img = Image(img_buffer, width=6*inch, height=4*inch)

    hospital_logo = Image('hospital_logo.png', width=4*inch, height=1*inch)

    # Build the PDF content for the first page
    first_page_content = []

    # Header bar
    # first_page_content.append(Paragraph("<b>------------------------ HEADER BAR ------------------------</b>", heading_style))

    # Main Title
    # first_page_content.append(Paragraph("SRI THIRUMALA PHYSIOTHERAPHY & PAIN RELIEF CLINIC", title_style))
    first_page_content.append(hospital_logo)
    # Address and line break
    first_page_content.append(Paragraph("69, Arcot Road, Cheyyar – 604407, Thiruvannamalai District,", heading_style))
    first_page_content.append(Paragraph("(Opp Government Boys Higher Secondary School)", heading_style))
    first_page_content.append(Paragraph("04182 – 222527 Cell: 9843078583, 9566376777", heading_style))
    first_page_content.append(Spacer(1, 0.2*inch))  # Line break

    # Daily Treatment Summary
    # first_page_content.append(Paragraph("DAILY TREATMENT SUMMARY:", heading_style))

    # Build and apply table style
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
    ])

    # Create the table
    table = Table(data)
    table.setStyle(table_style)

    # Add the Daily Treatment Summary before the main table
    first_page_content.append(Paragraph("DAILY TREATMENT SUMMARY:", heading_style))

    # Line break after Daily Treatment Summary
    first_page_content.append(Spacer(1, 0.2*inch))

    # Add the main table
    first_page_content.append(table)

    # Combine the content for the two pages
    story = first_page_content + [PageBreak()]

    # Build the PDF content for the second page
    second_page_content = []

    # Add the pain scale graph
    second_page_content.append(Paragraph("<b>Pain Scale Graph during the Treatment Period:</b>", subheading_style))
    second_page_content.append(pain_scale_img)

    # Combine the content for the two pages
    story += second_page_content

    doc.build(story)

def draw_page_border(canvas, doc):
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(2)
    canvas.rect(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, stroke=1)

# # Sample data
# name = "John Doe"
# age = "30"
# gender = "Male"
# referred_by = "Dr. Smith"
# Date = "23-3034"
# chief_complaint = "Back pain"
# previous_treatment = "Physiotherapy sessions"
# diagnosis = "Muscle strain"
# duration = "2 weeks"
# treatment_given = "Massage, Heat therapy"
# treatment_dates = ["2023-07-25", "2023-07-26", "2023-07-27", "2023-07-28", "2023-07-29"]
# painscales = [2, 3, 1, 2, 1]
# advised_exercise = "Stretching exercises"
# home_advice = "Apply ice pack if needed"
# next_review = "2023-08-02"

# # Generate the PDF report
# create_pdf(name, age, gender, referred_by, chief_complaint, previous_treatment, diagnosis, duration,
#            treatment_given, treatment_dates, painscales, advised_exercise, home_advice, next_review)



