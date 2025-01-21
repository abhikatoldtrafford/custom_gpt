import os
import time
import streamlit as st
from openai import AzureOpenAI

# --------------------------------------------------------------------------
# 1. Setup
# --------------------------------------------------------------------------

def create_client():
    return AzureOpenAI(
        azure_endpoint=st.secrets['AZURE_ENDPOINT'],
        api_key=st.secrets['AZURE_API_KEY'],
        api_version=st.secrets['AZURE_API_VERSION'],
    )

client = create_client()

# Temporary directory to store downloaded files
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# 2. Helper Functions
# --------------------------------------------------------------------------
def create_assistant_with_files(files):
    """Create an assistant with access to uploaded files."""
    try:
        file_ids = []
        for f in files:
            with st.spinner(f"Uploading {f.name}..."):
                uploaded_file = client.files.create(file=f, purpose="assistants")
                file_ids.append(uploaded_file.id)

        # Create an assistant with detailed instructions
        new_assistant = client.beta.assistants.create(
            instructions=(
                "You are a data analyst with access to multiple files. "
                "Use Python (pandas, openpyxl, or relevant libraries) to read and analyze these files. "
                "When asked about their contents, read the actual data and provide stats or relevant info. "
                "Format numbers appropriately and give brief interpretations."
            ),
            model="gpt-4",
            tools=[{"type": "code_interpreter"}],
            tool_resources={"code_interpreter": {"file_ids": file_ids}},
            name="Data Analyst"
        )
        return new_assistant, file_ids
    except Exception as e:
        st.error(f"Error creating assistant: {str(e)}")
        return None, None

def create_new_thread():
    """Create a new conversation thread."""
    try:
        return client.beta.threads.create()
    except Exception as e:
        st.error(f"Error creating thread: {str(e)}")
        return None

def add_message_and_run_assistant(thread_id, assistant_id, user_input):
    """Add a user message and run the assistant."""
    try:
        # Add the user message
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=(
                f"Analyze the data to answer: {user_input}\n"
                "Always use the actual files in your response. If asked about statistics, "
                "show the calculations. Format numbers appropriately with commas and decimals."
            )
        )
        
        # Wait for completion
        with st.spinner("Analyzing your request..."):
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                if run_status.status == "completed":
                    break
                elif run_status.status in ["failed", "cancelled", "expired"]:
                    raise Exception(f"Run failed with status: {run_status.status}")
                time.sleep(1)
            
        # Get the latest assistant message
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for msg in messages.data:
            if msg.role == "assistant":
                for content in msg.content:
                    if hasattr(content, 'text'):
                        return content.text.value
                    elif hasattr(content, 'image_file'):
                        # Handle image files
                        file_id = content.image_file.file_id
                        file_data = client.files.content(file_id)
                        file_bytes = file_data.read()
                        return file_bytes
        return "No response received from assistant."
    
    except Exception as e:
        st.error(f"Error in processing: {str(e)}")
        return None

def clear_chat():
    """Clear the chat history and reset session state."""
    st.session_state.chat_history = []
    st.session_state.files_loaded = False
    st.session_state.assistant_id = None
    st.session_state.thread_id = None
    st.success("Chat cleared! You can start a new session.")

# --------------------------------------------------------------------------
# 3. Streamlit UI
# --------------------------------------------------------------------------
st.set_page_config(page_title="Data Analyzer", layout="centered")
st.title("📊 Data Analysis Assistant")

# Initialize session state
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "files_loaded" not in st.session_state:
    st.session_state.files_loaded = False

# Sidebar for file upload and session management
st.sidebar.header("📁 Data Upload")
uploaded_files = st.sidebar.file_uploader(
    "Upload your data files",
    type=None,  # Accept any file type
    accept_multiple_files=True
)

# Start new session or clear chat
if st.sidebar.button("🔄 Start New Analysis Session"):
    clear_chat()

# Process uploaded files
if uploaded_files and not st.session_state.files_loaded:
    with st.spinner("Processing your files..."):
        assistant, file_ids = create_assistant_with_files(uploaded_files)
        if assistant and file_ids:
            st.session_state.assistant_id = assistant.id
            thread = create_new_thread()
            if thread:
                st.session_state.thread_id = thread.id
                st.session_state.files_loaded = True
                # Initialize with data analysis
                initial_response = add_message_and_run_assistant(
                    thread.id,
                    assistant.id,
                    "Analyze the structure of these files and describe their contents."
                )
                if initial_response:
                    st.session_state.chat_history.append({"role": "assistant", "content": initial_response})
                st.success("Files processed successfully!")

# Display current file status
if st.session_state.files_loaded:
    st.sidebar.success("✅ Files loaded and ready for analysis")
else:
    st.sidebar.info("⚠️ Please upload one or more files to begin analysis")

# Chat interface
if st.session_state.files_loaded and st.session_state.assistant_id and st.session_state.thread_id:
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], str):
                st.write(message["content"])
            elif isinstance(message["content"], bytes):
                st.image(message["content"], caption="Generated Image", use_container_width=True)
    
    # User input
    user_input = st.chat_input("Ask about your data...")
    if user_input:
        # Show user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        
        # Get assistant response
        response = add_message_and_run_assistant(
            st.session_state.thread_id,
            st.session_state.assistant_id,
            user_input
        )
        
        if response:
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                if isinstance(response, str):
                    st.write(response)
                elif isinstance(response, bytes):
                    st.image(response, caption="Generated Image", use_container_width=True)
else:
    st.info("👆 Please upload files in the sidebar to begin analysis (or click 'Start New Analysis Session').")

# Clear chat button
if st.session_state.chat_history:
    if st.sidebar.button("🧹 Clear Chat"):
        clear_chat()
