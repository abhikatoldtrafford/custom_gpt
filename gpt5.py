import streamlit as st
import json
import pymupdf
from gpt5_backend import create_report
def ocr_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    
    # Extract text from each page
    pages_text = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        pages_text.append({
            "page_number": page_num,
            "text": text
        })
    
    # Create JSON output
    output = {
        "pages": pages_text
    }
    
    return output
def main():
    st.set_page_config(page_title="CEO Mandate Generator", page_icon="📑")

    st.title("CEO Mandate Consolidation Tool")

    st.header("Upload PDFs")
    default_paths = {
        "strategic_priorities": "files/leadership_priorities_report.pdf",
        "trust_barometer": "files/Trust_Report.pdf",
        "time_liberation": "files/TimeLiberationMatrixReport.pdf",
        "pnl_power": "files/ProfitAndLoss.pdf"
    }
    # File uploaders for each GPT output
    strategic_priorities_file = st.file_uploader(
        "Upload Leadership Priority Report (PDF)", type="PDF", key="strategic_priorities"
    )
    trust_barometer_file = st.file_uploader(
        "Upload Leadership Trust Report (PDF)", type="PDF", key="trust_barometer"
    )
    time_liberation_file = st.file_uploader(
        "Upload Time Liberation Matrix (PDF)", type="PDF", key="time_liberation"
    )
    pnl_power_file = st.file_uploader(
        "Upload Profit and Loss Insight (PDF)", type="PDF", key="pnl_power"
    )

    # Parse and store uploaded files
    outputs = {}
    if strategic_priorities_file:
        outputs["Strategic Priorities"] = ocr_pdf(strategic_priorities_file)
    else:
        outputs["Strategic Priorities"] = ocr_pdf(default_paths["strategic_priorities"])
    if trust_barometer_file:
        outputs["Leadership Trust Barometer"] = ocr_pdf(trust_barometer_file)
    else:
        outputs["Leadership Trust Barometer"] = ocr_pdf(default_paths["trust_barometer"])
    if time_liberation_file:
        outputs["Time Liberation Matrix"] = ocr_pdf(time_liberation_file)
    else:
        outputs["Time Liberation Matrix"] = ocr_pdf(default_paths["time_liberation"])

    if pnl_power_file:
        outputs["P&L Power Insight"] = ocr_pdf(pnl_power_file)
    else:
        outputs["P&L Power Insight"] = ocr_pdf(default_paths["pnl_power"])
    # Display consolidated insights
    if st.button("Generate CEO Mandate"):
        survey_data = outputs
        # Call the create_pdf function
        try:
            pdf_path = create_report(survey_data)
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="Download Report",
                    data=pdf_file,
                    file_name="CEOMandate.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Failed to generate reports: {e}")
    else:
        st.warning("Please upload outputs from the required PDFs to generate the CEO Mandate.")

if __name__ == "__main__":
    main()
