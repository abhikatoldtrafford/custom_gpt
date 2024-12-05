import json
import tempfile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from openai import OpenAI
import streamlit as st

# Set up OpenAI API
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)


def send_to_gpt(input_data):
    """
    Send the consolidated JSON data to GPT and get the analysis.
    """
    system_prompt = """
    You are a strategic insights expert. Integrate the inputs into a CEO mandate document
    outlining strategic priorities, focus areas, and a delegation plan.
    a) Customize the response STRICTLY from the input provided.
    b) Provide critical and analytical insights

    Output JSON format:
    {
        "strategic_priorities": ["Priority 1 with supporting metric", "Priority 2 with supporting metric", ..., "Priority n with supporting metric"],
        "non_negotiables": ["Non-Negotiable 1 with supporting metric", "Non-Negotiable 2 with supporting metric", ..., "Non-Negotiable n with supporting metric"],
        "delegation_focus": {
            "delegate": ["Task 1 with supporting metric", "Task 2 with supporting metric", ..., "Task n with supporting metric"],
            "retain": ["Task 1 with supporting metric", "Task 2 with supporting metric", ..., "Task n with supporting metric"]
        },
        "next_steps": ["Step 1 with supporting metric", "Step 2 with supporting metric", ..., "Step n with supporting metric"],
    }
    
    PS: STRICTLY adhere to the output JSON format
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({"Strategic Priorities": input_data['Strategic Priorities'], "Leadership Trust Barometer": input_data['Leadership Trust Barometer'], 'Time Liberation Matrix': input_data['Time Liberation Matrix'], 'Profit and Loss': input_data['P&L Power Insight']})}
            ]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise RuntimeError(f"Error communicating with GPT: {e}")


def generate_ceo_mandate(gpt_response):
    """
    Generate the CEO Mandate PDF document from the GPT response.
    """
    temp_pdf = tempfile.mktemp(".pdf")
    doc = SimpleDocTemplate(temp_pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    story = []

    # Title
    story.append(Paragraph("CEO Mandate", title_style))
    story.append(Spacer(1, 12))

    # Strategic Priorities
    priorities = gpt_response.get("strategic_priorities", [])
    if priorities:
        story.append(Paragraph("Strategic Priorities:", heading_style))
        for priority in priorities:
            story.append(Paragraph(f"• {priority}", normal_style))
        story.append(Spacer(1, 12))

    # Non-Negotiables
    non_negotiables = gpt_response.get("non_negotiables", [])
    if non_negotiables:
        story.append(Paragraph("Non-Negotiables:", heading_style))
        for item in non_negotiables:
            story.append(Paragraph(f"• {item}", normal_style))
        story.append(Spacer(1, 12))

    # Delegation Focus
    delegation = gpt_response.get("delegation_focus", {})
    if delegation:
        story.append(Paragraph("Delegation Focus:", heading_style))
        story.append(Paragraph("Tasks to Delegate:", normal_style))
        for task in delegation.get("delegate", []):
            story.append(Paragraph(f"• {task}", normal_style))
        story.append(Paragraph("Tasks to Retain:", normal_style))
        for task in delegation.get("retain", []):
            story.append(Paragraph(f"• {task}", normal_style))
        story.append(Spacer(1, 12))

    # Next Steps
    next_steps = gpt_response.get("next_steps", [])
    if next_steps:
        story.append(Paragraph("Next Steps:", heading_style))
        for step in next_steps:
            story.append(Paragraph(f"• {step}", normal_style))
        story.append(Spacer(1, 12))

    # Build the PDF
    doc.build(story)
    return temp_pdf


def create_report(input_data):
    """
    Main function to process the input JSON file and generate the CEO mandate.
    """
    try:
        # Send input data to GPT for analysis
        gpt_response = send_to_gpt(input_data)

        # Generate PDF document using GPT response
        pdf_path = generate_ceo_mandate(gpt_response)

        return pdf_path
    except Exception as e:
        raise RuntimeError(f"Failed to create report: {e}")


if __name__ == "__main__":
    input_file = "files/ceo_mandate.json"  # Input JSON file
    # Load the input data
    with open(input_file, "r") as f:
        input_data = json.load(f)
    try:
        # Call create_report to generate the mandate
        pdf_report = create_report(input_data)
        print(f"CEO Mandate generated at: {pdf_report}")
    except Exception as e:
        print(f"Error: {e}")
