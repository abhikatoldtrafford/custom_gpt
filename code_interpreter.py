import streamlit as st
import requests
import base64
from io import BytesIO
import time

# API Configuration
API_BASE_URL = "https://analyticsgpt.azurewebsites.net"
HEADERS = {"Content-Type": "application/json"}

# Initialize session state
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

def initiate_chat_session():
    """Create a new assistant and session"""
    try:
        response = requests.post(f"{API_BASE_URL}/initiate-chat")
        if response.status_code == 200:
            data = response.json()
            st.session_state.assistant_id = data["assistant_id"]
            st.success("New chat session created!")
            return True
        else:
            st.error("Failed to create session")
            return False
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return False

def handle_file_upload(uploaded_file):
    """Handle file upload to backend"""
    if st.session_state.assistant_id:
        try:
            files = {"file": uploaded_file.getvalue()}
            response = requests.post(
                f"{API_BASE_URL}/upload-file",
                files={"file": (uploaded_file.name, uploaded_file.getvalue())}
            )
            if response.status_code == 200:
                st.session_state.uploaded_files.append(uploaded_file.name)
                return True
            else:
                st.error("File upload failed")
                return False
        except Exception as e:
            st.error(f"Upload error: {str(e)}")
            return False
    else:
        st.error("Please create a session first")
        return False

def display_response(response):
    """Display response content with proper formatting"""
    for item in response:
        if item["type"] == "text":
            st.markdown(item["content"])
        elif item["type"] == "image":
            try:
                image_data = base64.b64decode(item["content"])
                st.image(image_data, caption="Generated Visualization", use_container_width=True)
            except Exception as e:
                st.error(f"Failed to display image: {str(e)}")

def send_message(prompt):
    """Send message to backend and handle response"""
    if not st.session_state.assistant_id:
        st.error("Please create a session first")
        return

    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            data={"prompt": prompt}
        )
        
        if response.status_code == 200:
            chat_data = response.json()
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.chat_history.append({"role": "assistant", "content": chat_data["response"]})
        else:
            st.error(f"API Error: {response.text}")

    except Exception as e:
        st.error(f"Connection error: {str(e)}")

# Streamlit UI Layout
st.set_page_config(page_title="AnalyticsGPT", layout="wide")
st.title("📊 Data Analysis Assistant")

# Sidebar Controls
with st.sidebar:
    st.header("Session Management")
    
    if st.button("🔄 Start New Session"):
        if initiate_chat_session():
            st.session_state.chat_history = []
            st.session_state.uploaded_files = []
    
    st.header("📁 File Upload")
    uploaded_file = st.file_uploader(
        "Upload data files (CSV, Excel)",
        type=["csv", "xlsx"],
        key="file_uploader"
    )
    
    if uploaded_file and (uploaded_file.name not in st.session_state.uploaded_files):
        with st.spinner(f"Uploading {uploaded_file.name}..."):
            if handle_file_upload(uploaded_file):
                st.success(f"{uploaded_file.name} uploaded successfully!")
    
    if st.session_state.uploaded_files:
        st.subheader("Uploaded Files")
        for fname in st.session_state.uploaded_files:
            st.markdown(f"- `{fname}`")

# Main Chat Interface
st.subheader("💬 Analysis Chat")

# Display Chat History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], list):
            display_response(message["content"])
        else:
            st.markdown(message["content"])

# User Input
user_input = st.chat_input("Ask about your data...")
if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            send_message(user_input)
            # Display latest response
            if st.session_state.chat_history[-1]["role"] == "assistant":
                display_response(st.session_state.chat_history[-1]["content"])

# Add some footer spacing
st.markdown("<br><br>", unsafe_allow_html=True)
