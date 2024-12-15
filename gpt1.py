import streamlit as st
from openai import OpenAI 
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import tempfile
import json
# Set up OpenAI API 
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)
def create_priority_table(input_data, report_data):
    """
    Create a priority table using the 'detailed_priority_breakdown' section of report_data.
    This function ignores the old method of deriving data from 'top_strategic_priorities', 
    'business_goals', and 'key_oppertunities', and instead uses the structured JSON provided 
    in 'detailed_priority_breakdown'.

    Handles missing data gracefully by using "N/A".
    Uses Paragraph with a wrap style for better text fitting.
    """

    styles = getSampleStyleSheet()
    wrap_style = styles['Normal']
    wrap_style.fontSize = 8  # Reduce font size for better fit
    wrap_style.leading = 10  # Adjust line spacing

    # Retrieve detailed priority breakdown data
    breakdown_data = report_data.get("detailed_priority_breakdown", [])

    # Prepare table header with Paragraphs for wrapping
    table_data = [[
        Paragraph("Rank", wrap_style),
        Paragraph("Priority", wrap_style),
        Paragraph("Strategic Goal Alignment", wrap_style),
        Paragraph("Action Plan", wrap_style)
    ]]

    # Iterate through each breakdown entry
    for entry in breakdown_data:
        rank = str(entry.get("rank", "N/A"))
        priority = entry.get("priority", "N/A")
        alignment = entry.get("strategic_goal_alignment", "N/A")
        action_plan = entry.get("action_plan", "N/A")

        # Wrap text in Paragraphs
        rank_paragraph = Paragraph(rank, wrap_style)
        priority_paragraph = Paragraph(priority, wrap_style)
        alignment_paragraph = Paragraph(alignment, wrap_style)
        action_plan_paragraph = Paragraph(action_plan, wrap_style)

        table_data.append([
            rank_paragraph,
            priority_paragraph,
            alignment_paragraph,
            action_plan_paragraph
        ])

    # Create the table with adjusted widths if needed
    table = Table(table_data, colWidths=[40, 180, 180, 180])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D3D3D3')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
    ]))

    return table


def create_pdf(report_data, input_data):
    """
    Create a PDF from the GPT-generated JSON report
    """
    # Create a temporary file
    temp_pdf = tempfile.mktemp(".pdf")
    
    # Create PDF document
    doc = SimpleDocTemplate(temp_pdf, pagesize=letter)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Build story (content)
    story = []
    
    # Title
    story.append(Paragraph("Leadership Priorities Report", title_style))
    story.append(Spacer(1, 12))
    
    try:
        # Top Strategic Priorities
        story.append(Paragraph("Top Strategic Priorities:", heading_style))
        for priority in report_data.get('top_strategic_priorities', []):
            story.append(Paragraph(f"• {priority.get('priority', 'N/A')}: {priority.get('rationale', 'N/A')}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass
    
    try:
        # Insert the priority table
        priority_table = create_priority_table(input_data, report_data)
        story.append(Spacer(1, 12))
        story.append(Paragraph("Detailed Priority Breakdown:", heading_style))
        story.append(Spacer(1, 12))
        story.append(priority_table)
        story.append(Spacer(1, 12))
    except:
        pass
    try:
        # key oppertunities
        story.append(Paragraph("Key Opportunities:", heading_style))
        for item in report_data.get('key_oppertunities', []):
            story.append(Paragraph(f"• {item}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass

    try:
        # Non-Negotiables
        story.append(Paragraph("Non-Negotiables:", heading_style))
        for item in report_data.get('non_negotiables', []):
            story.append(Paragraph(f"• {item}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass
    
    try:
        # Observations
        story.append(Paragraph("Observations:", heading_style))
        observations = report_data.get('observations', {})
        story.append(Spacer(1, 12))
    except:
        pass
    
    try:
        # Time Allocation Misalignment
        story.append(Paragraph("Time Allocation Misalignment:", heading_style))
        story.append(Paragraph(observations.get('time_allocation_misalignment', 'No specific misalignment noted.'), normal_style))
        story.append(Spacer(1, 12))
    except:
        pass
    
    try:
        # Recommended Adjustments
        story.append(Paragraph("Recommended Adjustments:", heading_style))
        for adjustment in observations.get('recommended_adjustments', []):
            story.append(Paragraph(f"• {adjustment}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass
    
    try:
        story.append(Paragraph("Next Steps:", heading_style))
        for adjustment in observations.get('next_steps', []):
            story.append(Paragraph(f"• {adjustment}", normal_style))
    except:
        pass
    
    # Build PDF
    doc.build(story)
    
    return temp_pdf

def create_pdf_old(report_data):
    """
    Create a PDF from the GPT-generated JSON report
    """
    # Create a temporary file
    temp_pdf = tempfile.mktemp(".pdf")
    
    # Create PDF document
    doc = SimpleDocTemplate(temp_pdf, pagesize=letter)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Build story (content)
    story = []
    
    # Title
    story.append(Paragraph("Leadership Priorities Report", title_style))
    story.append(Spacer(1, 12))
    
    # Top Strategic Priorities
    story.append(Paragraph("Top Strategic Priorities:", heading_style))
    for priority in report_data.get('top_strategic_priorities', []):
        story.append(Paragraph(f"• {priority['priority']}: {priority['rationale']}", normal_style))
    story.append(Spacer(1, 12))
    
    # Non-Negotiables
    story.append(Paragraph("Non-Negotiables:", heading_style))
    for item in report_data.get('non_negotiables', []):
        story.append(Paragraph(f"• {item}", normal_style))
    story.append(Spacer(1, 12))
    
    # Observations
    story.append(Paragraph("Observations:", heading_style))
    observations = report_data.get('observations', {})
    
    # Time Allocation Misalignment
    story.append(Paragraph("Time Allocation Misalignment:", heading_style))
    story.append(Paragraph(observations.get('time_allocation_misalignment', 'No specific misalignment noted.'), normal_style))
    story.append(Spacer(1, 12))
    
    # Recommended Adjustments
    story.append(Paragraph("Recommended Adjustments:", heading_style))
    for adjustment in observations.get('recommended_adjustments', []):
        story.append(Paragraph(f"• {adjustment}", normal_style))
    
    story.append(Paragraph("Next Steps:", heading_style))
    for adjustment in observations.get('next_steps', []):
        story.append(Paragraph(f"• {adjustment}", normal_style))
    
    # Build PDF
    doc.build(story)
    
    return temp_pdf


def generate_leadership_report(input_data):
    system_prompt = """
    You are a strategic leadership advisor.  
    Using the CEO’s 'job_description', 'business_goals', current 'focus_areas', and 'time_percentage', analyze and rank the top 7 strategic priorities based on alignment with business objectives and potential impact. Incorporate insights from the P&L Power Insight GPT and provide actionable recommendations for realignment."

    Processing Requirements
        • Parse job descriptions to infer overarching strategic responsibilities.
        • Use key business goals to prioritize focus areas and assess their alignment with time allocation.
        • Incorporate P&L insights to ensure financial priorities align with stated strategic goals.
        • Highlight misalignments and suggest reallocation strategies for time and focus.

    Ranking Criteria:
        1. Alignment with Business Goals: Match priorities with selected goals.
        2. Impact Potential: Prioritize actions driving measurable growth or efficiency.
        3. Time Allocation Efficiency: Identify misalignments in focus areas and suggest reallocations.
        4. Strategic Importance: Highlight priorities essential for long-term growth.
    
    Output a Leadership Priorities Report (json) with the following strict format:
    {
        "top_strategic_priorities": [
            {"priority": "Priority #1", "rationale": "Explanation"},
            {"priority": "Priority #2", "rationale": "Explanation"},
            {"priority": "Priority #3", "rationale": "Explanation"},
            ...,
            ...,
            ...,
            {"priority": "Priority #n", "rationale": "Explanation"},
        "key_oppertunities": [
            "Expand x to drive x% revenue growth.",
            "Automate x processes to reduce operational costs by x%",
            ...,
            ...,
            ...,
            "Develop x to reduce CEO time on tactical issues by x%",
        ],
        "non_negotiables": [
            "Oversee x for y.",
            "Ensure x and y are done",
            ...,
            ...,
        ],
        "observations": {
            "time_allocation_misalignment": "You spend x% of your time doing y, which contributes to only z% of your business goals.",
            "recommended_adjustments": [
                "Shift x% of your time for doing y which contributes to only z% of your profit",
                "Increase your time for task x by y% ",
                ...,
                ...,
                ...,
                "Decreasing your time for task x in favour of task y is recommended"
            ],
            "next_steps": [
                "Focus on Priority: Begin doing x,y and z for expansion",
                "Address Time Misalignments: Reduce/Optimize/Increase your time spend on x/y low/high impact areas.",
                ...,
                ...,
                ...,
                "Develop a Roadmap: Plan execution for <top_strategic_priorities> over the next quarter"
            ],
        },
        "detailed_priority_breakdown": [
            {
                "rank": 1,
                "priority": "top_strategic_priority 1",
                "strategic_goal_alignment": "insert goal according to priority",
                "action_plan": "insert appropriate action plan."
            },
            {
                "rank": 2,
                "priority": "top_strategic_priority 2",
                "strategic_goal_alignment": "insert goal according to priority",
                "action_plan": "insert appropriate action plan."
            },
            ...,
            ...,

            {
                "rank": n,
                "priority": "top_strategic_priority n",
                "strategic_goal_alignment": "insert goal according to priority",
                "action_plan": "insert appropriate action plan."
            },
        ]
    }
    
    PS: STRICTLY adhere to the output format
    PS: Your response should be HIGHLY correlated and dependent on input. Dont make any numbers up.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(input_data)}
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating report: {e}")
        return None

def main():
    st.title("Strategic Priorities Compass")
    
    # Job Description with prepopulated CEO role
    job_description = st.text_area(
        "Describe your current role in your organization. What are your main responsibilities?",
        value="As the CEO, I oversee strategic planning, build partnerships, manage financial performance, and drive innovation.",
        help="Example: Oversee strategic planning, build partnerships, manage financial performance, and drive innovation."
    )
    
    # Business Goals Multi-Select
    business_goals_options = [
        "Increase revenue",
        "Improve profit margins",
        "Expand market share",
        "Launch new products/services",
        "Build leadership capacity",
        "Optimize operational efficiency",
        "Prepare for IPO",
        "Prepare for exit"
    ]
    business_goals = st.multiselect(
        "Select the top 3-5 goals you want to achieve in the next 12-18 months.",
        business_goals_options,
        default=["Increase revenue", "Improve profit margins", "Expand market share", "Launch new products/services", "Build leadership capacity", "Optimize operational efficiency", "Prepare for IPO", "Prepare for exit"]
    )
    
    # Current Focus Areas (up to 5)
    st.subheader("Current Focus Areas")
    focus_areas = []
    num_focus_areas = 5
    for i in range(num_focus_areas):
        focus_area = st.text_input(f"Focus Area {i+1}", key=f"focus_{i}")
        if focus_area.strip():
            focus_areas.append(focus_area.strip())
    
    # Time Allocation with sliders
    st.subheader("Time Allocation")
    time_allocations = []
    total_time = 0
    for focus in focus_areas:
        time_allocation = st.slider(
            f"Allocate % time for '{focus}'",
            min_value=0,
            max_value=100,
            value=20,  # Default value set to 20%
            step=1,
            key=f"time_{focus}"
        )
        time_allocations.append({
            "focus_area": focus,
            "time_percentage": time_allocation
        })
        total_time += time_allocation
    
    # Display total time allocation
    st.write(f"**Total Time Allocation: {total_time}%**")
    if total_time != 100:
        st.warning("Total time allocation should sum up to 100%. Please adjust the sliders.")
    
    # Submit Button
    if st.button("Generate Leadership Priorities Report"):
        # if total_time != 100:
        #     st.error("Total time allocation must sum up to 100%. Please adjust the sliders.")
        
        input_data = {
                "job_description": job_description,
                "business_goals": business_goals,
                "focus_areas": time_allocations
            }
            
            # Generate report
        raw_response = generate_leadership_report(input_data)
            
        if raw_response:
                # Display raw GPT response
            st.text_area("Raw GPT Response", raw_response, height=200)
                
                # Try to create PDF
            try:
                pdf_path = create_pdf(json.loads(raw_response), input_data)
                # pdf_path = create_pdf(json.loads(raw_response))
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="Download Report PDF",
                        data=pdf_file,
                        file_name="leadership_priorities_report.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.warning(f"PDF generation failed. Attempting to regenerate JSON: {e}")
                
                # Attempt to regenerate JSON
                try:
                    st.info("Sending the response back to GPT for regeneration...")
                    regenerated_response = generate_leadership_report(json.loads(raw_response))
                    if regenerated_response:
                        st.text_area("Regenerated GPT Response", regenerated_response, height=200)
                        # Attempt PDF creation again
                        try:
                            pdf_path = create_pdf(json.loads(regenerated_response))
                            with open(pdf_path, "rb") as pdf_file:
                                st.download_button(
                                    label="Download Report PDF (Regenerated)",
                                    data=pdf_file,
                                    file_name="leadership_priorities_report.pdf",
                                    mime="application/pdf"
                                )
                        except Exception as e:
                            st.warning(f"Second PDF generation failed. Saving as text: {e}")
                            # Fallback to text file
                            txt_path = "leadership_priorities_report.txt"
                            with open(txt_path, "w") as txt_file:
                                txt_file.write(regenerated_response)
                            with open(txt_path, "rb") as txt_file:
                                st.download_button(
                                    label="Download Report TXT",
                                    data=txt_file,
                                    file_name="leadership_priorities_report.txt",
                                    mime="text/plain"
                                )
                    else:
                        st.error("Failed to regenerate response from GPT.")
                except Exception as e:
                    st.error(f"Regeneration attempt failed: {e}")
                    # Final fallback to text file
                    txt_path = "leadership_priorities_report.txt"
                    with open(txt_path, "w") as txt_file:
                        txt_file.write(raw_response)
                    with open(txt_path, "rb") as txt_file:
                        st.download_button(
                            label="Download Report TXT",
                            data=txt_file,
                            file_name="leadership_priorities_report.txt",
                            mime="text/plain"
                        )

if __name__ == "__main__":
    main()