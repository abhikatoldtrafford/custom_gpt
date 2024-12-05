import streamlit as st
import os
import json
import tempfile
import numpy as np
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as ReportLabImage,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from openai import OpenAI 
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)


def calculate_metrics(input_data):
    """
    Calculate detailed metrics from the input JSON data.
    """
    metrics = {}
    try:
        # Extract CEO scores
        ceo_delegation_scores = []
        ceo_trust_scores = []
        try:
            for key in input_data['CEO Input']['Delegation Dynamics']:
                try:
                    score = input_data['CEO Input']['Delegation Dynamics'][key]['score']
                    ceo_delegation_scores.append(score)
                except Exception as e:
                    print(f"Error extracting CEO Delegation Dynamics score for key {key}: {e}")
            ceo_delegation_avg = np.mean(ceo_delegation_scores)
        except Exception as e:
            print(f"Error calculating ceo_delegation_avg: {e}")
            ceo_delegation_avg = 'N/A'

        try:
            for key in input_data['CEO Input']['Trust Dynamics']:
                try:
                    score = input_data['CEO Input']['Trust Dynamics'][key]['score']
                    ceo_trust_scores.append(score)
                except Exception as e:
                    print(f"Error extracting CEO Trust Dynamics score for key {key}: {e}")
            ceo_trust_avg = np.mean(ceo_trust_scores)
        except Exception as e:
            print(f"Error calculating ceo_trust_avg: {e}")
            ceo_trust_avg = 'N/A'

        # Extract Team scores
        team_delegation_scores = []
        team_trust_scores = []
        try:
            for key in input_data['Leadership Team']['Delegation Dynamics']:
                try:
                    score = input_data['Leadership Team']['Delegation Dynamics'][key]['score']
                    team_delegation_scores.append(score)
                except Exception as e:
                    print(f"Error extracting Team Delegation Dynamics score for key {key}: {e}")
            team_delegation_avg = np.mean(team_delegation_scores)
        except Exception as e:
            print(f"Error calculating team_delegation_avg: {e}")
            team_delegation_avg = 'N/A'

        try:
            for key in input_data['Leadership Team']['Trust Dynamics']:
                try:
                    score = input_data['Leadership Team']['Trust Dynamics'][key]['score']
                    team_trust_scores.append(score)
                except Exception as e:
                    print(f"Error extracting Team Trust Dynamics score for key {key}: {e}")
            team_trust_avg = np.mean(team_trust_scores)
        except Exception as e:
            print(f"Error calculating team_trust_avg: {e}")
            team_trust_avg = 'N/A'

        # Calculate Gaps
        try:
            if isinstance(ceo_delegation_avg, (int, float)) and isinstance(team_delegation_avg, (int, float)):
                delegation_gap = ceo_delegation_avg - team_delegation_avg
            else:
                delegation_gap = 'N/A'
        except Exception as e:
            print(f"Error calculating delegation_gap: {e}")
            delegation_gap = 'N/A'

        try:
            if isinstance(ceo_trust_avg, (int, float)) and isinstance(team_trust_avg, (int, float)):
                trust_gap = ceo_trust_avg - team_trust_avg
            else:
                trust_gap = 'N/A'
        except Exception as e:
            print(f"Error calculating trust_gap: {e}")
            trust_gap = 'N/A'

        metrics = {
            'ceo_delegation_scores': ceo_delegation_scores,
            'ceo_trust_scores': ceo_trust_scores,
            'team_delegation_scores': team_delegation_scores,
            'team_trust_scores': team_trust_scores,
            'ceo_delegation_avg': ceo_delegation_avg,
            'ceo_trust_avg': ceo_trust_avg,
            'team_delegation_avg': team_delegation_avg,
            'team_trust_avg': team_trust_avg,
            'delegation_gap': delegation_gap,
            'trust_gap': trust_gap
        }
    except Exception as e:
        print(f"Error in calculate_metrics: {e}")
        metrics = {
            'ceo_delegation_scores': [],
            'ceo_trust_scores': [],
            'team_delegation_scores': [],
            'team_trust_scores': [],
            'ceo_delegation_avg': 'N/A',
            'ceo_trust_avg': 'N/A',
            'team_delegation_avg': 'N/A',
            'team_trust_avg': 'N/A',
            'delegation_gap': 'N/A',
            'trust_gap': 'N/A'
        }

    return metrics

def generate_gpt_analysis(input_data, metrics, summary_data):
    """
    Generate comprehensive analysis using GPT.
    """
    # Prepare system prompt with detailed context
    
    system_prompt = """
You are an expert organizational consultant. Analyze the results of two surveys on Trust and Delegation Effectiveness conducted with the CEO and the leadership team. Your analysis should include the following:

## **summary_of_results**
    summarize the matrics, input data and summary_data. Provide critical assessment
## **analysis_of_gaps**
    Find out if Significant Gaps in Trust and Delegation Effectiveness.
## **recommendations**
    Provide actionable recommendations to address significant gaps: mention action and priority
## **next_steps**: Create a roadmap to address flagged issues: Short-term, Mid-term and Long term goals.
## **final_observation**
    Provide a concise observation summarizing the overall analysis: 
### Output Format
Output a JSON in the following strict format:
{
    "summary_of_results": [
            "Data Summary #1",
            "Data Summary #2",
            ...,
            ...,
            ...,
            "Data Summary #n"
    ],
    "outliers": [
            "Point #1",
            "Point #2",
            ...,
            ...,
            ...,
            "Point #n"
    ],
    "analysis_of_gaps": [
            "Gap analysis #1",
            "Gap analysis #2",
            ...,
            ...,
            ...,
            "Gap analysis #n"
    ],
    "recommendations": [
            "CEO mandate recommendations #1",
            "CEO mandate recommendations #2",
            ...,
            ...,
            ...,
            "CEO mandate recommendations #n"
    ],
    "next_steps": [
            "next steps for short-term/mid-term/long-term #1",
            "next steps for short-term/mid-term/long-term #2",
            ...,
            ...,
            ...,
            "next steps for short-term/mid-term/long-term #2"
    ],
    "final_observation": [
            "Analytical Summary #1",
            "Analytical Summary #2",
            ...,
            ...,
            ...,
            "Analytical Summary #n"
    ]}

**Important Notes**:
- Always include the keys: summary_of_results, outliers, analysis_of_gaps, recommendations, next_steps, final_observation.
- STRICTLY adhere to the output format and ensure the output is valid JSON.
- For any section where data is not available or meaningful, explicitly state "No data available" or similar.

"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({"input_data": input_data, "metrics": metrics, "summary_data": summary_data})}
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating report: {e}")
        return None
def generate_gpt_analysis2(input_data, metrics, summary_data):
        system_prompt = """
            You are an expert leadership consultant. Analyze the survey results for Trust and Delegation Effectiveness conducted with the CEO and the leadership team. Provide a detailed report that includes:

            ## **Strategic Priorities**
            1. Identify and rank the top three strategic priorities based on the survey findings.
            2. Provide a rationale for each priority.

            ## **Delegation and Trust Analysis**
            ### Delegation Dynamics:
            - Current Status: Summarize CEO and team scores related to delegation.
            - Key Gaps:
                - Red-Level Issues: Critical gaps requiring immediate action.
                - Orange-Level Issues: Moderate gaps needing attention.
                - Green-Level Strengths: Areas of alignment and strength.
            ### Trust Dynamics:
            - Current Status: Summarize CEO and team scores related to trust.
            - Key Gaps:
                - Red-Level Issues: Critical gaps requiring immediate action.
                - Orange-Level Issues: Moderate gaps needing attention.
                - Green-Level Strengths: Areas of alignment and strength.

            ## **Recommendations**
            1. Provide three actionable recommendations for improving delegation and trust.
            2. Include action items and assign a priority (High/Medium/Low).

            ## **Next Steps**
            1. Immediate Actions: Quick wins to address significant gaps.
            2. Mid-Term Goals: Steps to ensure sustained progress over the next few months.
            3. Long-Term Strategy: Plans to achieve enduring alignment and growth.

            ## **Heatmap Summary**
            ### Delegation Scores:
            - Include a table summarizing CEO and team scores, gaps, and their significance (Red/Orange/Green).
            ### Trust Scores:
            - Include a table summarizing CEO and team scores, gaps, and their significance (Red/Orange/Green).

            ## **Final Observation**
            - Provide a concise observation summarizing the overall analysis and its implications.

            ### **Output Format**
            Output a JSON in the following strict format:
            {
                "strategic_priorities": [
                    {"priority": "<Priority #1>", "rationale": "<Rationale for Priority #1>"},
                    {"priority": "<Priority #2>", "rationale": "<Rationale for Priority #2>"},
                    {"priority": "<Priority #3>", "rationale": "<Rationale for Priority #3>"}
                ],
                "delegation_dynamics": {
                    "current_status": "<Summary of delegation scores>",
                    "key_gaps": {
                        "red_issues": ["<Critical issue 1>", "<Critical issue 2>"],
                        "orange_issues": ["<Moderate issue 1>", "<Moderate issue 2>"],
                        "green_strengths": ["<Strength 1>", "<Strength 2>"]
                    }
                },
                "trust_dynamics": {
                    "current_status": "<Summary of trust scores>",
                    "key_gaps": {
                        "red_issues": ["<Critical issue 1>", "<Critical issue 2>"],
                        "orange_issues": ["<Moderate issue 1>", "<Moderate issue 2>"],
                        "green_strengths": ["<Strength 1>", "<Strength 2>"]
                    }
                },
                "recommendations": [
                    {"action": "<Recommendation #1>", "priority": "<High/Medium/Low>"},
                    {"action": "<Recommendation #2>", "priority": "<High/Medium/Low>"},
                    {"action": "<Recommendation #3>", "priority": "<High/Medium/Low>"}
                ],
                "next_steps": {
                    "immediate_actions": ["<Action #1>", "<Action #2>"],
                    "mid_term_goals": ["<Goal #1>", "<Goal #2>"],
                    "long_term_strategy": ["<Strategy #1>", "<Strategy #2>"]
                },
                "heatmap_summary": {
                    "delegation_scores": [
                        {"aspect": "<Aspect>", "ceo_score": "<Score>", "team_avg": "<Average>", "gap": "<Gap>", "level": "<Red/Orange/Green>"}
                    ],
                    "trust_scores": [
                        {"aspect": "<Aspect>", "ceo_score": "<Score>", "team_avg": "<Average>", "gap": "<Gap>", "level": "<Red/Orange/Green>"}
                    ]
                },
                "final_observation": "<Summarize overall analysis>"
            }

            **Important Notes**:
            - Always include all keys in the JSON structure.
            - Explicitly mention "No data available" for sections with missing data.
            """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps({"input_data": input_data, "metrics": metrics, "summary_data": summary_data})}
                ],
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Error generating report: {e}")
            return None
def generate_heatmaps(metrics):
    """
    Generate heatmaps and bar charts for delegation and trust scores.
    """
    # Create temporary files for images
    delegation_heatmap_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
    trust_heatmap_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name

    # Delegation Heatmap
    try:
        if isinstance(metrics['ceo_delegation_scores'], list) and isinstance(metrics['team_delegation_scores'], list):
            plt.figure(figsize=(10, 6))
            data = [metrics['ceo_delegation_scores'], metrics['team_delegation_scores']]
            plt.imshow(data, cmap='coolwarm', aspect='auto')
            plt.colorbar(label='Scores')
            plt.yticks([0,1], ['CEO', 'Team'])
            plt.title('Delegation Dynamics Heatmap')
            plt.savefig(delegation_heatmap_file, bbox_inches='tight')
            plt.close()
        else:
            raise ValueError("Delegation scores are not available.")
    except Exception as e:
        print(f"Error generating delegation heatmap: {e}")
        # Create a placeholder image
        plt.figure(figsize=(5, 1))
        plt.text(0.5, 0.5, 'Delegation Heatmap Not Available', horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(delegation_heatmap_file, bbox_inches='tight')
        plt.close()

    # Trust Heatmap
    try:
        if isinstance(metrics['ceo_trust_scores'], list) and isinstance(metrics['team_trust_scores'], list):
            plt.figure(figsize=(10, 6))
            data = [metrics['ceo_trust_scores'], metrics['team_trust_scores']]
            plt.imshow(data, cmap='coolwarm', aspect='auto')
            plt.colorbar(label='Scores')
            plt.yticks([0,1], ['CEO', 'Team'])
            plt.title('Trust Dynamics Heatmap')
            plt.savefig(trust_heatmap_file, bbox_inches='tight')
            plt.close()
        else:
            raise ValueError("Trust scores are not available.")
    except Exception as e:
        print(f"Error generating trust heatmap: {e}")
        # Create a placeholder image
        plt.figure(figsize=(5, 1))
        plt.text(0.5, 0.5, 'Trust Heatmap Not Available', horizontalalignment='center', verticalalignment='center')
        plt.axis('off')
        plt.savefig(trust_heatmap_file, bbox_inches='tight')
        plt.close()

    return delegation_heatmap_file, trust_heatmap_file

def create_pdf_survey(input_data, metrics, gpt_analysis, delegation_heatmap_file, trust_heatmap_file):
    """
    Create a comprehensive PDF report.
    """
    # Create temporary PDF file
    temp_pdf = tempfile.mktemp(".pdf")
    doc = SimpleDocTemplate(temp_pdf, pagesize=letter)
    gpt_analysis = json.loads(gpt_analysis)
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], alignment=1)
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], spaceAfter=6)
    normal_style = styles['Normal']
    bullet_style = styles['Bullet']

    # Build story (content)
    story = []

    # Title
    story.append(Paragraph("Trust and Delegation Effectiveness Survey Analysis", title_style))
    story.append(Spacer(1, 12))

    # Summary of Results
    story.append(Paragraph("Summary of Results", heading_style))

    wrap_style = styles['Normal']
    wrap_style.fontSize = 8  # Reduce font size for better fit
    wrap_style.leading = 10  # Adjust line spacing

    data = [
    [
        Paragraph('Statement', wrap_style),
        Paragraph('CEO Score', wrap_style),
        Paragraph('Team Score', wrap_style),
        Paragraph('Gap', wrap_style),
        Paragraph('Significant Gap?', wrap_style),
        Paragraph('Observations', wrap_style)
    ]
]

    for key in input_data['CEO Input']['Delegation Dynamics']:
        ceo_question = input_data['CEO Input']['Delegation Dynamics'][key]
        team_question = input_data['Leadership Team']['Delegation Dynamics'][key]
        ceo_score = ceo_question['score']
        team_score = team_question['score']
        gap = ceo_score - team_score
        significant_gap = 'Yes' if abs(gap) > 2 else 'No'
        observation = "Weak perception of clarity." if significant_gap == 'Yes' else "No significant misalignment."

        # Use Paragraph for wrapping text in the 'Statement' and 'Observations' columns
        statement_paragraph = Paragraph(ceo_question['question'], wrap_style)
        observation_paragraph = Paragraph(observation, wrap_style)

        data.append([
            statement_paragraph,
            ceo_score,
            f"{team_score:.1f}",
            f"{gap:.1f}",
            significant_gap,
            observation_paragraph
        ])

    # Adjust column widths to allocate more space for the 'Statement' and 'Observations' columns
    table = Table(data, colWidths=[200, 40, 60, 40, 60, 140])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D3D3D3')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
    ]))

    # Add the table to the story
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph("---", normal_style))
    story.append(Spacer(1, 12))

    # # Outliers Section
    # story.append(Paragraph("Outliers", heading_style))
    # # Since individual team member scores are not provided, this section is left empty.
    # story.append(Paragraph("Leadership Team Scores with Significant Deviations", styles['Heading3']))
    # story.append(Paragraph("No outlier data available.", normal_style))
    # story.append(Spacer(1, 12))

    # story.append(Paragraph("---", normal_style))
    # story.append(Spacer(1, 12))

    # Heatmaps
    story.append(Paragraph("Delegation Dynamics Heatmap", heading_style))
    story.append(Spacer(1, 12))
    story.append(ReportLabImage(delegation_heatmap_file, width=400, height=200))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Trust Dynamics Heatmap", heading_style))
    story.append(Spacer(1, 12))
    story.append(ReportLabImage(trust_heatmap_file, width=400, height=200))
    story.append(Spacer(1, 12))

    story.append(Paragraph("---", normal_style))
    story.append(Spacer(1, 12))
    
    try:
        story.append(Paragraph("Summary", heading_style))
        for item in gpt_analysis.get('summary_of_results', []):
            story.append(Paragraph(f"• {item}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass
    try:
        story.append(Paragraph("Outlier assessment", heading_style))
        for item in gpt_analysis.get('outliers', []):
            story.append(Paragraph(f"• {item}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass
    try:
        story.append(Paragraph("Analysis of Gaps", heading_style))
        for item in gpt_analysis.get('analysis_of_gaps', []):
            story.append(Paragraph(f"• {item}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass

    # Recommendations
    try:
        story.append(Paragraph("Recommendations for the CEO’s Mandate", heading_style))
        for item in gpt_analysis.get('recommendations', []):
            story.append(Paragraph(f"• {item}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass
    # Next Steps
    try:
        story.append(Paragraph("Next Steps", heading_style))
        for item in gpt_analysis.get('next_steps', []):
            story.append(Paragraph(f"• {item}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass

    # Final Observation
    try:
        story.append(Paragraph("Final Observation", heading_style))
        for item in gpt_analysis.get('final_observation', []):
            story.append(Paragraph(f"• {item}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass

    # Build PDF
    doc.build(story)

    return temp_pdf
def create_pdf_trust(report_data):
    """
    Create a PDF from the GPT-generated JSON report.
    """
    # Create a temporary file
    temp_pdf = tempfile.mktemp(".pdf")
    report_data = json.loads(report_data)
    # Create PDF document
    doc = SimpleDocTemplate(temp_pdf, pagesize=letter)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], alignment=1)
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    bullet_style = ParagraphStyle('BulletStyle', parent=normal_style, bulletIndent=20)

    # Build story (content)
    story = []

    # Title
    story.append(Paragraph("Leadership Trust Report", title_style))
    story.append(Spacer(1, 12))
    try:
        # Top Strategic Priorities
        story.append(Paragraph("Top Strategic Priorities:", heading_style))
        for priority in report_data.get('strategic_priorities', []):
            story.append(Paragraph(f"• <b>{priority['priority']}</b>: {priority['rationale']}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass
    try:
        # Delegation and Trust Analysis
        story.append(Paragraph("Delegation and Trust Analysis:", heading_style))

        # Delegation Dynamics
        delegation = report_data.get('delegation_dynamics', {})
        story.append(Paragraph("Delegation Dynamics - Current Status:", heading_style))
        story.append(Paragraph(delegation.get('current_status', 'No data available'), normal_style))
        story.append(Spacer(1, 12))
    except:
        pass
    try:
        # Delegation Gaps
        gaps = delegation.get('key_gaps', {})
        story.append(Paragraph("Delegation Dynamics - Key Gaps:", heading_style))
        story.append(Paragraph("<b>Red-Level Issues:</b>", normal_style))
        for issue in gaps.get('red_issues', []):
            story.append(Paragraph(f"• {issue}", bullet_style))
        
        story.append(Paragraph("<b>Orange-Level Issues:</b>", normal_style))
        for issue in gaps.get('orange_issues', []):
            story.append(Paragraph(f"• {issue}", bullet_style))
        
        story.append(Paragraph("<b>Green-Level Strengths:</b>", normal_style))
        for strength in gaps.get('green_strengths', []):
            story.append(Paragraph(f"• {strength}", bullet_style))
        story.append(Spacer(1, 12))
    except:
        pass

    try:
        # Trust Dynamics
        trust = report_data.get('trust_dynamics', {})
        story.append(Paragraph("Trust Dynamics - Current Status:", heading_style))
        story.append(Paragraph(trust.get('current_status', 'No data available'), normal_style))
        
        # Trust Gaps
        gaps = trust.get('key_gaps', {})
        story.append(Paragraph("Trust Dynamics - Key Gaps:", heading_style))
        story.append(Paragraph("<b>Red-Level Issues:</b>", normal_style))
        for issue in gaps.get('red_issues', []):
            story.append(Paragraph(f"• {issue}", bullet_style))
        
        story.append(Paragraph("<b>Orange-Level Issues:</b>", normal_style))
        for issue in gaps.get('orange_issues', []):
            story.append(Paragraph(f"• {issue}", bullet_style))
        
        story.append(Paragraph("<b>Green-Level Strengths:</b>", normal_style))
        for strength in gaps.get('green_strengths', []):
            story.append(Paragraph(f"• {strength}", bullet_style))
        story.append(Spacer(1, 12))
    except:
        pass
    
    try:
        # Recommendations
        story.append(Paragraph("Recommendations:", heading_style))
        for rec in report_data.get('recommendations', []):
            story.append(Paragraph(f"• <b>{rec['action']}</b> - Priority: {rec['priority']}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass
    try:
        # Next Steps
        story.append(Paragraph("Next Steps:", heading_style))
        next_steps = report_data.get('next_steps', {})
        
        story.append(Paragraph("<b>Immediate Actions:</b>", normal_style))
        for action in next_steps.get('immediate_actions', []):
            story.append(Paragraph(f"• {action}", bullet_style))
        
        story.append(Paragraph("<b>Mid-Term Goals:</b>", normal_style))
        for goal in next_steps.get('mid_term_goals', []):
            story.append(Paragraph(f"• {goal}", bullet_style))
        
        story.append(Paragraph("<b>Long-Term Strategy:</b>", normal_style))
        for strategy in next_steps.get('long_term_strategy', []):
            story.append(Paragraph(f"• {strategy}", bullet_style))
        story.append(Spacer(1, 12))
    except:
        pass

    try:
        # Heatmap Summary
        story.append(Paragraph("Heatmap Summary:", heading_style))
        heatmap = report_data.get('heatmap_summary', {})
        
        story.append(Paragraph("<b>Delegation Scores:</b>", normal_style))
        for score in heatmap.get('delegation_scores', []):
            story.append(Paragraph(
                f"• {score['aspect']}: CEO Score: {score['ceo_score']}, Team Avg: {score['team_avg']}, Gap: {score['gap']}, Level: {score['level']}",
                normal_style
            ))

        story.append(Paragraph("<b>Trust Scores:</b>", normal_style))
        for score in heatmap.get('trust_scores', []):
            story.append(Paragraph(
                f"• {score['aspect']}: CEO Score: {score['ceo_score']}, Team Avg: {score['team_avg']}, Gap: {score['gap']}, Level: {score['level']}",
                normal_style
            ))
        story.append(Spacer(1, 12))
    except:
        pass

    try:
        # Final Observation
        story.append(Paragraph("Final Observation:", heading_style))
        story.append(Paragraph(report_data.get('final_observation', 'No observation available'), normal_style))
        story.append(Spacer(1, 12))
    except:
        pass

    # Build the PDF
    doc.build(story)

    return temp_pdf

def generate_leadership_report(input_data):
    """
    Generate a comprehensive leadership report.
    """
    # Calculate metrics
    metrics = calculate_metrics(input_data)
    summary_data = [['Statement', 'CEO Score', 'Team Avg. Score', 'Gap', 'Significant Gap?', 'Observations']]

    for key in input_data['CEO Input']['Delegation Dynamics']:
        ceo_question = input_data['CEO Input']['Delegation Dynamics'][key]
        team_question = input_data['Leadership Team']['Delegation Dynamics'][key]
        ceo_score = ceo_question['score']
        team_score = team_question['score']
        gap = ceo_score - team_score
        significant_gap = 'Yes' if abs(gap) > 2 else 'No'
        observation = "Weak perception of clarity." if significant_gap == 'Yes' else "No significant misalignment."
        summary_data.append([
            ceo_question['question'],
            ceo_score,
            f"{team_score:.1f}",
            f"{gap:.1f}",
            significant_gap,
            observation
        ])

    # Generate GPT Analysis
    gpt_analysis1 = generate_gpt_analysis(input_data, metrics, summary_data)
    if not gpt_analysis1:
        print("Failed to generate GPT analysis.")
        return None
    gpt_analysis2 = generate_gpt_analysis2(input_data, metrics, summary_data)
    if not gpt_analysis2:
        print("Failed to generate GPT analysis.")
        return None
    # Generate Heatmaps
    delegation_heatmap_file, trust_heatmap_file = generate_heatmaps(metrics)

    # Create PDF
    pdf_path1 = create_pdf_survey(input_data, metrics, gpt_analysis1, delegation_heatmap_file, trust_heatmap_file)
    pdf_path2 = create_pdf_trust(gpt_analysis2)
    return pdf_path1, pdf_path2


if __name__ == "__main__":
    input_data = {
    "CEO Input":{
        "Delegation Dynamics":{
            "0":{
                "question":"Tasks delegated within the organization are communicated with clear expectations and well-defined outcomes.",
                "score":5
            },
            "1":{
                "question":"Team members are consistently given the resources and authority they need to successfully complete delegated tasks.",
                "score":7
            },
            "2":{
                "question":"The CEO spends most of their time on high-impact, strategic activities rather than operational details.",
                "score":7
            },
            "3":{
                "question":"Team members feel confident taking ownership of delegated tasks without requiring frequent follow-up from the CEO.",
                "score":7
            },
            "4":{
                "question":"Repetitive or low-priority tasks are reassigned, automated, or eliminated to allow the CEO to focus on strategic goals.",
                "score":7
            },
            "5":{
                "question":"The delegation process ensures timely and constructive feedback on performance to ensure continuous improvement.",
                "score":7
            },
            "6":{
                "question":"Tasks are assigned based on the skills and expertise of the person handling them, rather than being retained unnecessarily by the CEO.",
                "score":9
            },
            "7":{
                "question":"There is a clear process to identify which tasks should remain with the CEO and which should be delegated.",
                "score":7
            },
            "8":{
                "question":"The CEO actively works on developing the leadership team’s decision-making capacity to reduce reliance on themselves as the chief problem solver.",
                "score":7
            },
            "9":{
                "question":"Delegation within the organization is viewed as an opportunity to develop leadership skills and increase team capacity.",
                "score":3
            }
        },
        "Trust Dynamics":{
            "0":{
                "question":"There is mutual trust between the CEO and the leadership team to take ownership of responsibilities and deliver results.",
                "score":7
            },
            "1":{
                "question":"The CEO trusts team members to deliver high-quality results without requiring constant follow-up or micromanagement.",
                "score":7
            },
            "2":{
                "question":"The CEO empowers team members to make decisions independently without fear of being second-guessed.",
                "score":7
            },
            "3":{
                "question":"Mistakes are handled constructively, seen as opportunities for learning and improvement rather than assigning blame.",
                "score":7
            },
            "4":{
                "question":"There is a strong culture of accountability where everyone delivers on their commitments without the CEO needing to intervene frequently.",
                "score":7
            },
            "5":{
                "question":"The CEO delegates authority along with responsibility, ensuring team members feel ownership over their roles.",
                "score":7
            },
            "6":{
                "question":"Delegated tasks are rarely escalated back to the CEO unless absolutely necessary.",
                "score":7
            },
            "7":{
                "question":"The CEO spends minimal time resolving operational issues because team members handle them effectively.",
                "score":7
            },
            "8":{
                "question":"Team members feel trusted by the CEO to take initiatives aligned with organizational goals without excessive oversight.",
                "score":7
            },
            "9":{
                "question":"The CEO demonstrates confidence in the leadership team by empowering them to solve problems and achieve outcomes autonomously.",
                "score":7
            }
        }
    },
    "Leadership Team":{
        "Delegation Dynamics":{
            "0":{
                "question":"Tasks delegated within the organization are communicated with clear expectations and well-defined outcomes.",
                "score":2
            },
            "1":{
                "question":"Team members are consistently given the resources and authority they need to successfully complete delegated tasks.",
                "score":2
            },
            "2":{
                "question":"The CEO spends most of their time on high-impact, strategic activities rather than operational details.",
                "score":6
            },
            "3":{
                "question":"Team members feel confident taking ownership of delegated tasks without requiring frequent follow-up from the CEO.",
                "score":6
            },
            "4":{
                "question":"Repetitive or low-priority tasks are reassigned, automated, or eliminated to allow the CEO to focus on strategic goals.",
                "score":8
            },
            "5":{
                "question":"The delegation process ensures timely and constructive feedback on performance to ensure continuous improvement.",
                "score":6
            },
            "6":{
                "question":"Tasks are assigned based on the skills and expertise of the person handling them, rather than being retained unnecessarily by the CEO.",
                "score":6
            },
            "7":{
                "question":"There is a clear process to identify which tasks should remain with the CEO and which should be delegated.",
                "score":6
            },
            "8":{
                "question":"The CEO actively works on developing the leadership team’s decision-making capacity to reduce reliance on themselves as the chief problem solver.",
                "score":10
            },
            "9":{
                "question":"Delegation within the organization is viewed as an opportunity to develop leadership skills and increase team capacity.",
                "score":6
            }
        },
        "Trust Dynamics":{
            "0":{
                "question":"There is mutual trust between the CEO and the leadership team to take ownership of responsibilities and deliver results.",
                "score":6
            },
            "1":{
                "question":"The CEO trusts team members to deliver high-quality results without requiring constant follow-up or micromanagement.",
                "score":2
            },
            "2":{
                "question":"The CEO empowers team members to make decisions independently without fear of being second-guessed.",
                "score":6
            },
            "3":{
                "question":"Mistakes are handled constructively, seen as opportunities for learning and improvement rather than assigning blame.",
                "score":6
            },
            "4":{
                "question":"There is a strong culture of accountability where everyone delivers on their commitments without the CEO needing to intervene frequently.",
                "score":4
            },
            "5":{
                "question":"The CEO delegates authority along with responsibility, ensuring team members feel ownership over their roles.",
                "score":6
            },
            "6":{
                "question":"Delegated tasks are rarely escalated back to the CEO unless absolutely necessary.",
                "score":6
            },
            "7":{
                "question":"The CEO spends minimal time resolving operational issues because team members handle them effectively.",
                "score":5
            },
            "8":{
                "question":"Team members feel trusted by the CEO to take initiatives aligned with organizational goals without excessive oversight.",
                "score":6
            },
            "9":{
                "question":"The CEO demonstrates confidence in the leadership team by empowering them to solve problems and achieve outcomes autonomously.",
                "score":6
            }
        }
    }
}
    pdf_path1, pdf_path2 = generate_leadership_report(input_data)
    print(pdf_path1, pdf_path2)

