import streamlit as st
import pandas as pd
import json
from gpt4_backend import create_pl_pdf

def calculate_financials(revenue, cogs, overhead):
    """
    Helper function to calculate financial metrics.
    """
    gross_profit = [r * (1 - c / 100) for r, c in zip(revenue, cogs)]
    net_profit = [gp - (r * o / 100) for gp, r, o in zip(gross_profit, revenue, overhead)]
    break_even = [r if gp - (r * o / 100) >= 0 else None for gp, r, o in zip(gross_profit, revenue, overhead)]
    return gross_profit, net_profit, break_even

def main():
    st.set_page_config(page_title="P&L Summary Tool", page_icon="📊")
    st.title("P&L Summary and Financial Insights Tool")
    st.markdown("""
    ### Analyze your P&L trends to identify strengths and bottlenecks.
    Add as many years as required to dynamically calculate financial insights.
    """)

    # Input Section
    st.header("Financial Inputs")

    # Dynamic Years Input
    years = st.text_input("Enter years separated by commas (e.g., 2020,2021,2022):", "2020,2021,2022")
    years = [year.strip() for year in years.split(",") if year.strip()]

    # Create empty lists for inputs
    revenue, cogs, overhead = [], [], []

    # Input in columns
    st.subheader("Input Financial Data")
    for year in years:
        col1, col2, col3 = st.columns(3)

        # Revenue Input
        with col1:
            revenue.append(st.number_input(f"Revenue ($M) for {year}", min_value=0.0, value=5.0, step=0.1, key=f"revenue_{year}") * 1e6)

        # COGS Input
        with col2:
            cogs.append(st.number_input(f"COGS (%) for {year}", min_value=0.0, max_value=100.0, value=40.0, step=0.1, key=f"cogs_{year}"))

        # Overhead Input
        with col3:
            overhead.append(st.number_input(f"SG&A (%) for {year}", min_value=0.0, max_value=100.0, value=15.0, step=0.1, key=f"overhead_{year}"))

    # Calculations
    gross_profit, net_profit, break_even = calculate_financials(revenue, cogs, overhead)

    # Output Section
    st.header("Financial Summary")
    df = pd.DataFrame({
        "Year": years,
        "Revenue ($M)": [r / 1e6 for r in revenue],
        "COGS (%)": cogs,
        "Gross Profit ($M)": [gp / 1e6 for gp in gross_profit],
        "Overhead (SG&A %)": overhead,
        "Net Profit ($M)": [np / 1e6 for np in net_profit],
        "Break Even Point ($M)": [be / 1e6 if be is not None else "N/A" for be in break_even],
    })

    st.dataframe(df)

    # Download as JSON
    output_json = {
        "Financial Summary": df.to_dict(orient="records")
    }

    # Generate Report Button
    if st.button("Generate Results"):
        survey_data = output_json
        # Call the create_pdf function
        try:
            pdf_path = create_pl_pdf(survey_data)
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="Download Report",
                    data=pdf_file,
                    file_name="ProfitAndLoss.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Failed to generate reports: {e}")

if __name__ == "__main__":
    main()
