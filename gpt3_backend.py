import json
import tempfile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from openai import OpenAI
import streamlit as st

# Set up OpenAI API
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

def analyze_tasks(input_data):
    """
    Analyze tasks to generate a prioritization matrix and recommendations.
    """
    tasks = input_data.get("Tasks", [])
    time_spend_areas = input_data.get("Time Spend Areas", [])
    task_matrix = []

    # Analyze each task for prioritization and recommendations
    for task in tasks:
        recommendation = ""
        if task["impact"] == "High Impact":
            if task["urgency"] == "High Urgency":
                recommendation = "Retain"
            else:
                recommendation = "Retain (with efficiency)"
        else:
            recommendation = "Delegate"

        task_matrix.append({
            "task": task["task"],
            "time_spent": f"{task['time_allocation']}%",
            "urgency": task["urgency"],
            "impact": task["impact"],
            "recommendation": recommendation
        })

    # Observations
    total_low_impact_time = sum(
        task["time_allocation"] for task in tasks if task["impact"] != "High Impact"
    )
    total_high_impact_time = sum(
        task["time_allocation"] for task in tasks if task["impact"] == "High Impact")
    observations = {
        "high_impact_time": f"You spend {total_high_impact_time}% of your time on tasks with high impact.",
        "low_impact_time": f"You spend {total_low_impact_time}% of your time on tasks with low or medium impact.",
        "time_spend_areas": time_spend_areas,
    }


    return task_matrix, observations


def generate_gpt_analysis(task_matrix, observations):
    """
    Use GPT to create descriptive bullet points for the report.
    """
    system_prompt = """
    You are a task prioritization expert. 
    Based on the provided Task Prioritization Matrix and observations, create concise and actionable recommendations for a CEO. 
    Include focus areas and tasks to delegate. 
    EXAMPLE ouput:
    {
    "recommendations": [
        "Prioritize strategic planning sessions to ensure long-term growth by allocating dedicated time free from distractions. This will help in setting clear organizational goals and aligning the team to achieve them.",
        "Limit time spent on approving marketing campaigns, as these can be handled by the marketing manager. Delegate this task with clear guidelines and performance metrics to ensure alignment with the company's strategic objectives.",
        "Focus on high-impact tasks such as team performance reviews to identify strengths and areas of improvement within the team, boosting overall productivity and morale.",
        ...,
        ...,
        ...,
        "Reevaluate time spent on managing key clients. Delegate operational aspects to account managers, allowing the CEO to focus on strategic client relationships."
    ],
    "focus_areas": [
        "Strategic planning sessions: These are crucial for setting the organization's vision and ensuring long-term growth.",
        "Team performance reviews: High-priority tasks to enhance team efficiency and identify opportunities for development.",
        ...,
        ...,
        ...,
        "Partnership meetings: Vital for building and maintaining strategic alliances that drive business growth."
    ],
    "delegate_tasks": [
        "Approve marketing campaigns: This task can be delegated to the marketing manager with clear approval guidelines.",
        "Follow up on pending tasks: Assign this responsibility to an administrative assistant or project coordinator to streamline operations.",
        "Operational client management: Delegate day-to-day client interactions to account managers to free up time for strategic priorities.",
        ...,
        ...,
        ...,
        "Routine financial performance reviews: Hand over monthly or routine financial data reviews to the CFO or finance team, focusing only on key insights or anomalies."
    ]
    }

    Output in JSON format:
    {
        "recommendations": ["Recommendation #1", "Recommendation #2", ..., "Recommendation #n"],
        "focus_areas": ["Focus Area #1", "Focus Area #2", ..., "Focus Area #n"],
        "delegate_tasks": ["Task #1", "Task #2", ..., "Task #n"]
    }
    PS: STRICTLY adhere to the output format
    
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({"task_matrix": task_matrix, "observations": observations})}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error generating GPT analysis: {e}")
        return None


def create_pdf(input_data):
    """
    Create a PDF report from the analyzed data and GPT recommendations.
    """
    # Process data
    task_matrix, observations = analyze_tasks(input_data)
    gpt_analysis = generate_gpt_analysis(task_matrix, observations)
    temp_pdf = tempfile.mktemp(".pdf")
    doc = SimpleDocTemplate(temp_pdf, pagesize=letter)

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], alignment=1)
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    # Build story (content)
    story = []

    # Title
    story.append(Paragraph("Time Liberation Matrix Report", title_style))
    story.append(Spacer(1, 12))

    # Task Prioritization Matrix
    story.append(Paragraph("Task Prioritization Matrix:", heading_style))
    table_data = [["Task", "Time Spent", "Urgency", "Impact", "Recommendation"]]
    for task in task_matrix:
        table_data.append([task["task"], task["time_spent"], task["urgency"], task["impact"], task["recommendation"]])
    
    table = Table(table_data, colWidths=[150, 70, 100, 100, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D3D3D3')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))
    try:
        # Observations
        story.append(Paragraph("Observations:", heading_style))
        for key, value in observations.items():
            if isinstance(value, list):
                story.append(Paragraph(f"{key.replace('_', ' ').capitalize()}:", normal_style))
                for item in value:
                    story.append(Paragraph(f"• {item}", normal_style))
            else:
                story.append(Paragraph(value, normal_style))
        story.append(Spacer(1, 12))
    except:
        pass
    try:
        # Recommendations
        story.append(Paragraph("Recommendations:", heading_style))
        if gpt_analysis:
            try:
                for rec in gpt_analysis.get("recommendations", []):
                    story.append(Paragraph(f"• {rec}", normal_style))
                story.append(Spacer(1, 12))
            except:
                pass
            try:
                # Focus Areas
                story.append(Paragraph("Focus Areas:", heading_style))
                for area in gpt_analysis.get("focus_areas", []):
                    story.append(Paragraph(f"• {area}", normal_style))
                story.append(Spacer(1, 12))
            except:
                pass
            try:
                # Delegate Tasks
                story.append(Paragraph("Tasks to Delegate:", heading_style))
                for task in gpt_analysis.get("delegate_tasks", []):
                    story.append(Paragraph(f"• {task}", normal_style))
                story.append(Spacer(1, 12))
            except:
                pass
    except:
        pass

    # Build the PDF
    doc.build(story)
    return temp_pdf

if __name__ == "__main__":
    input_data = {
    "Tasks": [
        {"task": "Review financial performance", "time_allocation": 20, "urgency": "High Urgency", "impact": "High Impact"},
        {"task": "Approve marketing campaigns", "time_allocation": 10, "urgency": "Medium Urgency", "impact": "Low Impact"},
        {"task": "Attend partnership meetings", "time_allocation": 25, "urgency": "High Urgency", "impact": "Medium Impact"},
        {"task": "Team performance reviews", "time_allocation": 15, "urgency": "Medium Urgency", "impact": "High Impact"},
        {"task": "Strategic planning sessions", "time_allocation": 30, "urgency": "High Urgency", "impact": "High Impact"}
    ],
    "Time Spend Areas": [
        "Approving unimportant decisions",
        "Managing key clients",
        "Worry about business future",
        "Following up pending tasks"
    ]
}

    pdf_path = create_pdf(input_data)
    print(f"PDF Report generated at: {pdf_path}")
