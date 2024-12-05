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


def calculate_pl_metrics(input_data):
    """
    Analyze P&L trends and calculate key metrics.
    """
    financial_summary = input_data.get("Financial Summary", [])
    metrics = []

    try:
        for record in financial_summary:
            year = record.get("Year")
            revenue = record.get("Revenue ($M)", 0)
            cogs_percent = record.get("COGS (%)", 0)
            cogs = revenue * (cogs_percent / 100)
            gross_profit = record.get("Gross Profit ($M)", revenue - cogs)
            overhead_percent = record.get("Overhead (SG&A %)", 0)
            overhead = revenue * (overhead_percent / 100)
            net_profit = record.get("Net Profit ($M)", gross_profit - overhead)
            break_even_point = record.get("Break Even Point ($M)", overhead)

            metrics.append({
                "Year": year,
                "Revenue": revenue,
                "COGS": cogs,
                "Gross Profit": gross_profit,
                "Overhead": overhead,
                "Net Profit": net_profit,
                "Break Even Point": break_even_point,
                "COGS (%)": cogs_percent,
                "Overhead (SG&A %)": overhead_percent,
            })
    except:
        pass

    return metrics


def generate_gpt_pl_analysis(input_data, metrics):
    """
    Use GPT to generate observations, recommendations, next steps, and key trends.
    """
    system_prompt = """
    You are a financial insights expert. Analyze the provided P&L metrics to identify key trends, observations, recommendations, and next steps. Your goal is to highlight critical financial insights that can guide decision-making.
    
    ** EXAMPLE **
    {
    "key_trends": {
        "RevenueGrowth": [
            "2020: $5M → 2021: $6M (+20% growth)",
            "2021: $6M → 2022: $7.5M (+25% growth)",
            "2020: $5M → 2022: $7.5M (+50% growth overall)",
            "Steady year-over-year growth suggests increasing demand and effective sales strategies, particularly in 2021-2022 where growth accelerated."
        ],
        "CostGrowth": [
            "2020: $4M → 2021: $4.5M (+12.5% growth)",
            "2021: $4.5M → 2022: $6.8M (+51.1% growth)",
            "2020: $4M → 2022: $6.8M (+70% growth overall)",
            "Costs grew significantly between 2021 and 2022, indicating inefficiencies or rising input prices that need closer review."
        ],
        "ProfitMargin": [
            "2020: 20% → 2021: 15% (-25%)",
            "2021: 15% → 2022: 9.3% (-38%)",
            "2020: 20% → 2022: 9.3% (-53% overall)",
            "Profit margin has been steadily declining, with a sharper drop in 2021-2022 due to increasing overhead and COGS."
        ],
        "BreakEvenPoint": [
            "2020: $2M → 2021: $2.5M (+25% increase)",
            "2021: $2.5M → 2022: $3M (+20% increase)",
            "2020: $2M → 2022: $3M (+50% increase overall)",
            "The higher break-even point year-over-year suggests rising fixed costs and lower contribution margins, highlighting the need for cost control measures."
        ]}
    },
    "observations": [
        "Profit margins are declining, indicating that cost controls or pricing strategies need to be reviewed.",
        "The company is becoming more reliant on high sales volume to maintain profitability.",
        "Break-even analysis shows a higher risk threshold, requiring careful monitoring of fixed costs."
    ],
    "recommendations": [
        "Focus on cost optimization strategies to reduce COGS and SG&A expenses.",
        "Review pricing strategies to increase profit margins without reducing sales volume.",
        "Explore automation and process efficiencies to reduce operational overhead."
    ],
    "next_steps": [
        "Conduct a detailed cost analysis to identify inefficiencies and renegotiate supplier contracts.",
        "Implement a pricing review to explore opportunities for value-based pricing.",
        "Develop a roadmap to streamline SG&A expenses through automation and restructuring.",
        "Set up quarterly financial reviews to monitor progress and adjust strategies dynamically."
    ]
}



    Output JSON format:
    {
        "key_trends": ["RevenueGrowth": ["Trend 1", "Trend 2", ...., "Trend n"],
                        "CostGrowth": ["Trend 1", "Trend 2", ...., "Trend n"],
                        "ProfitMargin": ["Trend 1", "Trend 2", ...., "Trend n"],
                        "BreakEvenPoint": ["Trend 1", "Trend 2", ...., "Trend n"],
        "observations": ["Observation 1", "Observation 2", ..., "Observation n"],
        "recommendations": ["Recommendation 1", "Recommendation 2", ..., "Recommendation n"],
        "next_steps": ["Next Step 1", "Next Step 2", ..., "Next Step n"]
    }
    PS: PS: STRICTLY adhere to the output format
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({"input_data": input_data, "metrics": metrics})}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except:
        return None

def create_pl_pdf(input_data):
    """
    Create a PDF report for P&L analysis.
    """
    metrics = calculate_pl_metrics(input_data)
    gpt_analysis = generate_gpt_pl_analysis(input_data, metrics)
    temp_pdf = tempfile.mktemp(".pdf")
    doc = SimpleDocTemplate(temp_pdf, pagesize=letter)

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], alignment=1)
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    bullet_style = ParagraphStyle('BulletStyle', parent=normal_style)
    # Build story (content)
    story = []

    # Title
    try:
        story.append(Paragraph("Profit and Loss Power Insight Report", title_style))
        story.append(Spacer(1, 12))
    except:
        pass

    # P&L Table
    try:
        story.append(Paragraph("Profit and Loss Metrics Table:", heading_style))
        
        # Define wrap style for table content
        wrap_style = styles['Normal']
        wrap_style.fontSize = 8  # Set font size for better readability
        wrap_style.leading = 10  # Adjust line spacing

        # Create the table header
        table_data = [
            [
                Paragraph("Year", wrap_style),
                Paragraph("Revenue ($M)", wrap_style),
                Paragraph("COGS (%)", wrap_style),
                Paragraph("Gross Profit ($M)", wrap_style),
                Paragraph("Overhead (SG&A %)", wrap_style),
                Paragraph("Net Profit ($M)", wrap_style),
                Paragraph("Break Even Point ($M)", wrap_style),
            ]
        ]

        # Add rows for each metric
        for metric in metrics:
            try:
                table_data.append([
                    Paragraph(metric.get("Year", "N/A"), wrap_style),
                    Paragraph(f"${metric.get('Revenue', 0):.2f}", wrap_style),
                    Paragraph(f"{metric.get('COGS (%)', 0)}%", wrap_style),
                    Paragraph(f"${metric.get('Gross Profit', 0):.2f}", wrap_style),
                    Paragraph(f"{metric.get('Overhead (SG&A %)', 0)}%", wrap_style),
                    Paragraph(f"${metric.get('Net Profit', 0):.2f}", wrap_style),
                    Paragraph(f"${metric.get('Break Even Point', 0):.2f}", wrap_style),
                ])
            except:
                pass

        # Create the table
        table = Table(table_data, colWidths=[60, 80, 60, 100, 80, 80, 80])
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
    except:
        pass

    try:
        # Trends
        trends = gpt_analysis.get('key_trends', {})
        story.append(Paragraph("Key Finalcial Trends:", heading_style))
        story.append(Paragraph("<b>Revenue Growth:</b>", normal_style))
        try:
            for issue in trends.get('RevenueGrowth', []):
                story.append(Paragraph(f"• {issue}", bullet_style))
        except:
            pass
        
        try:
            story.append(Paragraph("<b>Cost Growth:</b>", normal_style))
            for issue in trends.get('CostGrowth', []):
                story.append(Paragraph(f"• {issue}", bullet_style))
        except:
            pass    
        
        try:
            story.append(Paragraph("<b>Profit Margin:</b>", normal_style))
            for strength in trends.get('ProfitMargin', []):
                story.append(Paragraph(f"• {strength}", bullet_style))
        except:
            pass
        try:
            story.append(Paragraph("<b>Break Even Point:</b>", normal_style))
            for strength in trends.get('BreakEvenPoint', []):
                story.append(Paragraph(f"• {strength}", bullet_style))
        except:
            pass
        story.append(Spacer(1, 12))
    except:
        pass
    # Observations
    try:
        story.append(Paragraph("Observations:", heading_style))
        for obs in gpt_analysis.get("observations", []):
            story.append(Paragraph(f"• {obs}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass

    # Recommendations
    try:
        story.append(Paragraph("Recommendations:", heading_style))
        for rec in gpt_analysis.get("recommendations", []):
            story.append(Paragraph(f"• {rec}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass

    # Next Steps
    try:
        story.append(Paragraph("Next Steps:", heading_style))
        for step in gpt_analysis.get("next_steps", []):
            story.append(Paragraph(f"• {step}", normal_style))
        story.append(Spacer(1, 12))
    except:
        pass

    # Build the PDF
    try:
        doc.build(story)
    except:
        pass

    return temp_pdf


if __name__ == "__main__":
    input_data = {"Financial Summary": [
        {
            "Year": "2020",
            "Revenue ($M)": 5.0,
            "COGS (%)": 40,
            "Gross Profit ($M)": 3.0,
            "Overhead (SG&A %)": 15,
            "Net Profit ($M)": 2.25,
            "Break Even Point ($M)": 5.0
        },
        {
            "Year": "2021",
            "Revenue ($M)": 6.0,
            "COGS (%)": 38,
            "Gross Profit ($M)": 3.72,
            "Overhead (SG&A %)": 16,
            "Net Profit ($M)": 2.76,
            "Break Even Point ($M)": 6.0
        },
        {
            "Year": "2022",
            "Revenue ($M)": 7.5,
            "COGS (%)": 44,
            "Gross Profit ($M)": 4.2,
            "Overhead (SG&A %)": 18,
            "Net Profit ($M)": 2.85,
            "Break Even Point ($M)": 7.5
        }
    ]
}
    # Generate PDF
    pdf_path = create_pl_pdf(input_data)
    print(f"PDF Report generated at: {pdf_path}")
