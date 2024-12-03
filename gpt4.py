import streamlit as st
import pandas as pd
import json

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
    ### Analyze your P&L trends over the last 3 years to identify strengths and bottlenecks.
    """)

    # Input Section
    st.header("Financial Inputs")
    years = ["2020", "2021", "2022"]

    # Revenue Input
    st.subheader("Revenue")
    revenue = [
        st.number_input(f"Annual Revenue in M({year})", min_value=0.0, value=5.0 if year == "2020" else 6.0 if year == "2021" else 7.5, step=0.1) * 1e6
        for year in years
    ]

    # COGS Input
    st.subheader("Cost of Goods Sold (COGS %)")
    cogs = [
        st.slider(f"COGS Percentage ({year})", min_value=0, max_value=100, value=40 if year == "2020" else 38 if year == "2021" else 44, step=1)
        for year in years
    ]

    # Overhead Costs (SG&A)
    st.subheader("Overhead Costs (SG&A %)")
    overhead = [
        st.slider(f"Overhead Percentage ({year})", min_value=0, max_value=100, value=15 if year == "2020" else 16 if year == "2021" else 18, step=1)
        for year in years
    ]

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
    output = {
        "Financial Summary": df.to_dict(orient="records")
    }

    st.subheader("Download Financial Summary")
    json_filename = "financial_summary.json"
    st.download_button(
        label="Download JSON",
        data=json.dumps(output, indent=4),
        file_name=json_filename,
        mime="application/json"
    )

if __name__ == "__main__":
    main()
