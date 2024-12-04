import streamlit as st
from openai import OpenAI 
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import json
# Set up OpenAI API 
api_key = st.secrets["OPENAI_API_KEY"]
#api_key = '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'
client = OpenAI(api_key=api_key)
def create_pdf(report_data):
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
    You are a strategic leadership advisor. Analyze the CEO’s strategic priorities, current focus areas, and time allocation to identify gaps between their stated goals and current activities. Provide recommendations to realign focus with strategic objectives. 

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
        ],
        "non_negotiables": [
            "Non-negotiable #1",
            "Non-negotiable #2",
            ...,
            ...,
            ...,
            "Non-negotiable #n"
        ],
        "observations": {
            "time_allocation_misalignment": "Detailed observation about time allocation",
            "recommended_adjustments": [
                "Adjustment recommendation #1",
                "Adjustment recommendation #2",
                ...,
                ...,
                ...,
                "Adjustment recommendation #n"
            ],
            "next_steps": [
                "Next_steps #1",
                "Next_steps #2",
                ...,
                ...,
                ...,
                "Next steps #n"
            ],
        }
    }
    PS: STRICTLY adhere to the output format
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
        "Get the business ready for an IPO",
        "Get the business ready for an exit"
    ]
    business_goals = st.multiselect(
        "Select your key business goals",
        business_goals_options,
        default=["Increase revenue", "Improve profit margins", "Build leadership capacity"]
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
                pdf_path = create_pdf(json.loads(raw_response))
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
