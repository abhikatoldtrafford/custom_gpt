import streamlit as st
import json

def main():
    st.set_page_config(page_title="CEO Mandate Generator", page_icon="📑")

    st.title("CEO Mandate Consolidation Tool")
    st.markdown("""
    ### Purpose:
    Consolidate insights from multiple GPT outputs into a single, actionable CEO Mandate document.
    """)

    st.header("Upload GPT Outputs")
    st.info("Upload the JSON outputs from the following tools:")
    st.markdown("""
    - **Strategic Priorities Compass GPT**
    - **Leadership Trust Barometer GPT**
    - **Time Liberation Matrix GPT**
    - **P&L Power Insight GPT**
    """)

    # File uploaders for each GPT output
    strategic_priorities_file = st.file_uploader(
        "Upload Strategic Priorities Compass GPT Output (JSON)", type="json", key="strategic_priorities"
    )
    trust_barometer_file = st.file_uploader(
        "Upload Leadership Trust Barometer GPT Output (JSON)", type="json", key="trust_barometer"
    )
    time_liberation_file = st.file_uploader(
        "Upload Time Liberation Matrix GPT Output (JSON)", type="json", key="time_liberation"
    )
    pnl_power_file = st.file_uploader(
        "Upload P&L Power Insight GPT Output (JSON)", type="json", key="pnl_power"
    )

    # Parse and store uploaded files
    outputs = {}
    if strategic_priorities_file:
        outputs["Strategic Priorities"] = json.load(strategic_priorities_file)
    if trust_barometer_file:
        outputs["Leadership Trust Barometer"] = json.load(trust_barometer_file)
    if time_liberation_file:
        outputs["Time Liberation Matrix"] = json.load(time_liberation_file)
    if pnl_power_file:
        outputs["P&L Power Insight"] = json.load(pnl_power_file)

    # Display consolidated insights
    if outputs:
        st.header("Consolidated Insights")
        for section, data in outputs.items():
            st.subheader(section)
            st.json(data)

        # Generate CEO Mandate Button
        if st.button("Generate CEO Mandate"):
            st.subheader("Actionable CEO Mandate")
            mandate = {
                "Strategic Priorities": outputs.get("Strategic Priorities", {}),
                "Leadership Trust Barometer": outputs.get("Leadership Trust Barometer", {}),
                "Time Liberation Matrix": outputs.get("Time Liberation Matrix", {}),
                "P&L Power Insight": outputs.get("P&L Power Insight", {})
            }

            st.json(mandate)

            # Save Mandate as JSON
            json_filename = "ceo_mandate.json"
            with open(json_filename, "w") as f:
                json.dump(mandate, f, indent=4)

            st.download_button(
                label="Download CEO Mandate Document",
                data=json.dumps(mandate, indent=4),
                file_name=json_filename,
                mime="application/json"
            )

    else:
        st.warning("Please upload outputs from the required GPT tools to generate the CEO Mandate.")

if __name__ == "__main__":
    main()
