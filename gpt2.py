import streamlit as st
import json, os
from gpt2_backend import generate_leadership_report  # Importing the function as requested
import io
import zipfile
# Function to create survey UI
def survey_ui(title, questions, prefill_scores, tab):
    with tab:
        st.subheader(title)
        responses = {}
        for i, question in enumerate(questions):
            score = st.slider(
                f"{i + 1}. {question}",
                min_value=0,
                max_value=10,
                value=prefill_scores[i],
                step=1,
                key=f"{title}_{i}"
            )
            responses[str(i)] = {"question": question, "score": score}
        return responses

def main():
    # Prefill default values for survey questions
    delegation_dynamics_questions = [
        "Tasks delegated within the organization are communicated with clear expectations and well-defined outcomes.",
        "Team members are consistently given the resources and authority they need to successfully complete delegated tasks.",
        "The CEO spends most of their time on high-impact, strategic activities rather than operational details.",
        "Team members feel confident taking ownership of delegated tasks without requiring frequent follow-up from the CEO.",
        "Repetitive or low-priority tasks are reassigned, automated, or eliminated to allow the CEO to focus on strategic goals.",
        "The delegation process ensures timely and constructive feedback on performance to ensure continuous improvement.",
        "Tasks are assigned based on the skills and expertise of the person handling them, rather than being retained unnecessarily by the CEO.",
        "There is a clear process to identify which tasks should remain with the CEO and which should be delegated.",
        "The CEO actively works on developing the leadership team’s decision-making capacity to reduce reliance on themselves as the chief problem solver.",
        "Delegation within the organization is viewed as an opportunity to develop leadership skills and increase team capacity."
    ]

    trust_dynamics_questions = [
        "There is mutual trust between the CEO and the leadership team to take ownership of responsibilities and deliver results.",
        "The CEO trusts team members to deliver high-quality results without requiring constant follow-up or micromanagement.",
        "The CEO empowers team members to make decisions independently without fear of being second-guessed.",
        "Mistakes are handled constructively, seen as opportunities for learning and improvement rather than assigning blame.",
        "There is a strong culture of accountability where everyone delivers on their commitments without the CEO needing to intervene frequently.",
        "The CEO delegates authority along with responsibility, ensuring team members feel ownership over their roles.",
        "Delegated tasks are rarely escalated back to the CEO unless absolutely necessary.",
        "The CEO spends minimal time resolving operational issues because team members handle them effectively.",
        "Team members feel trusted by the CEO to take initiatives aligned with organizational goals without excessive oversight.",
        "The CEO demonstrates confidence in the leadership team by empowering them to solve problems and achieve outcomes autonomously."
    ]

    st.title("Trust and Delegation Effectiveness Survey")
    st.info("Rate on a scale of 0 to 10, where 0 = Strongly Disagree and 10 = Strongly Agree.")

    # Tabs for CEO and Leadership Team
    ceo_tab, team_tab = st.tabs(["CEO Survey", "Leadership Team Survey"])

    # Prefilled default scores
    default_scores_ceo = [9] * 10
    default_scores_team = [7] * 10

    # CEO Survey
    ceo_delegation_responses = survey_ui(
        "Delegation Dynamics (CEO)", delegation_dynamics_questions, default_scores_ceo, ceo_tab
    )
    ceo_trust_responses = survey_ui(
        "Trust Dynamics (CEO)", trust_dynamics_questions, default_scores_ceo, ceo_tab
    )

    # Leadership Team Survey
    team_delegation_responses = survey_ui(
        "Delegation Dynamics (Team)", delegation_dynamics_questions, default_scores_team, team_tab
    )
    team_trust_responses = survey_ui(
        "Trust Dynamics (Team)", trust_dynamics_questions, default_scores_team, team_tab
    )

    # Submit Button
    if st.button("Generate Survey Results"):
        survey_data = {
            "CEO Input": {
                "Delegation Dynamics": ceo_delegation_responses,
                "Trust Dynamics": ceo_trust_responses
            },
            "Leadership Team": {
                "Delegation Dynamics": team_delegation_responses,
                "Trust Dynamics": team_trust_responses
            }
        }

        # Call the generate_leadership_report function
        try:
            pdf_path1, pdf_path2 = generate_leadership_report(survey_data)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                zf.write(pdf_path1, arcname="Survey_Report.pdf")
                zf.write(pdf_path2, arcname="Trust_Report.pdf")
            zip_buffer.seek(0)

            # Provide download button for the ZIP file
            st.download_button(
                label="Download Reports (ZIP)",
                data=zip_buffer,
                file_name="Reports.zip",
                mime="application/zip"
            )
            
        except Exception as e:
            st.error(f"Failed to generate reports: {e}")

if __name__ == "__main__":
    main()



#add first last name, phone email in ceo form