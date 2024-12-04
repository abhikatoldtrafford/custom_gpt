import streamlit as st
import json

def main():
    st.set_page_config(page_title="CEO Task Prioritization", page_icon="📋")
    
    st.title("CEO Task Categorization and Prioritization Tool")
    st.markdown("""
    ### Strategic Task Management Dashboard
    This tool helps you analyze and optimize your time allocation and task priorities.
    """)

    # Prefilled tasks
    prefilled_tasks = [
        "Review financial performance",
        "Approve marketing campaigns",
        "Attend partnership meetings",
        "Team performance reviews",
        "Strategic planning sessions"
    ]

    # Initialize session state for tasks if not exists
    if 'tasks' not in st.session_state:
        st.session_state.tasks = [
            {"task": task, "time_allocation": 10, "urgency": "Medium Urgency", "impact": "Medium Impact"}
            for task in prefilled_tasks
        ]

    # Create two columns for Task List and Current Time Spend
    task_col, time_col = st.columns(2)

    # Task List Input
    with task_col:
        st.header("Task List")
        st.info("List up to 15 tasks you handle daily or weekly in your role.")
        
        # Task Input with Dynamic Addition
        new_task = st.text_input("Enter a new task:", key="new_task_input")
        add_task_button = st.button("Add Task")

        if add_task_button and new_task.strip() and len(st.session_state.tasks) < 15:
            st.session_state.tasks.append({
                "task": new_task.strip(),
                "time_allocation": 10,  # Default value
                "urgency": "Medium Urgency",  # Default value
                "impact": "Medium Impact"  # Default value
            })

        # Display Current Tasks with Remove Option
        st.subheader("Current Tasks")
        for i, task in enumerate(st.session_state.tasks):
            col1, col2 = st.columns([10, 1])
            with col1:
                st.markdown(f"**{i + 1}. {task['task']}**")
            with col2:
                if st.button("❌", key=f"remove_task_{i}"):
                    st.session_state.tasks.pop(i)
                    st.experimental_rerun()

    # Current Time Spend Input
    with time_col:
        st.header("Time Spend Analysis")
        st.info("Select areas where you spend more than 10% of your time.")
        
        time_spend_options = [
            "Approving unimportant decisions", 
            "Following up pending tasks", 
            "Managing key clients",
            "Micromanaging", 
            "Worry about business future"
        ]
        
        current_time_spend = st.multiselect(
            "Time Consumption Areas:",
            options=time_spend_options,
            default=[]
        )

    # Task Details for Each Added Task
    st.header("Task Priority Details")
    for i, task in enumerate(st.session_state.tasks):
        st.markdown(f"#### Task {i + 1}: {task['task']}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            task['time_allocation'] = st.slider(
                "Time Allocation (%)",
                min_value=0,
                max_value=100,
                value=task['time_allocation'],
                key=f"time_alloc_{i}"
            )
        
        with col2:
            task['urgency'] = st.selectbox(
                "Urgency Level",
                options=["High Urgency", "Medium Urgency", "Low Urgency"],
                index=["High Urgency", "Medium Urgency", "Low Urgency"].index(task['urgency']),
                key=f"urgency_{i}"
            )
        
        with col3:
            task['impact'] = st.selectbox(
                "Strategic Impact",
                options=["High Impact", "Medium Impact", "Low Impact"],
                index=["High Impact", "Medium Impact", "Low Impact"].index(task['impact']),
                key=f"impact_{i}"
            )

    # Generate Report Button
    if st.button("Generate Strategic Task Report"):
        output = {
            "Tasks": st.session_state.tasks,
            "Time Spend Areas": current_time_spend
        }
        
        # Display JSON Output
        st.subheader("Strategic Task Report")
        st.json(output)
        
        # Save JSON File
        json_filename = "strategic_task_report.json"
        with open(json_filename, "w") as f:
            json.dump(output, f, indent=4)
        
        st.download_button(
            label="Download Task Report",
            data=json.dumps(output, indent=4),
            file_name=json_filename,
            mime="application/json"
        )

if __name__ == "__main__":
    main()