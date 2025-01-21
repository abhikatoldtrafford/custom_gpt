import streamlit as st
import requests
import json
import time

# API Base URL
API_BASE_URL = "https://copilot-updated.azurewebsites.net/" 
API_BASE_URL = "https://copilot-updated-f6facehxewaceyfq.eastus-01.azurewebsites.net"
# Initialize session state
if "assistant_id" not in st.session_state:
    st.session_state["assistant_id"] = None
if "session_id" not in st.session_state:
    st.session_state["session_id"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []

# Function to initiate chat
def initiate_chat():
    with st.spinner("Creating assistant..."):
        response = requests.post(f"{API_BASE_URL}/initiate-chat")
    if response.status_code == 200:
        data = response.json()
        st.session_state["assistant_id"] = data["assistant"]
        st.session_state["session_id"] = data["session"]
        st.session_state["chat_history"] = []  # Reset chat history on new session
        st.session_state["uploaded_files"] = []  # Clear uploaded files
        st.success("Assistant created successfully!")
    else:
        st.error("Failed to create assistant. Check server logs.")

# Function to upload file
def upload_file(file):
    if st.session_state["assistant_id"]:
        with st.spinner("Uploading file..."):
            files = {"file": file}
            data = {"assistant": st.session_state["assistant_id"]}
            response = requests.post(f"{API_BASE_URL}/upload-file", files=files, data=data)
        if response.status_code == 200:
            st.session_state["uploaded_files"].append(file.name)
            st.success(f"File '{file.name}' uploaded successfully!")
        else:
            st.error("Failed to upload file. Check server logs.")
    else:
        st.error("Please create an assistant first.")

# Callback function for file upload
def handle_file_upload():
    uploaded_file = st.session_state.uploaded_file
    if uploaded_file and uploaded_file.name not in st.session_state["uploaded_files"]:
        progress_bar = st.sidebar.progress(0)
        with st.sidebar:
            for percent_complete in range(100):
                time.sleep(0.02)  # Simulate upload time
                progress_bar.progress(percent_complete + 1)
        upload_file(uploaded_file)
        progress_bar.empty()
        

# Function to handle conversation with streaming
def send_message_streaming(prompt):
    if st.session_state["session_id"]:
        params = {
            "session": st.session_state["session_id"],
            "assistant": st.session_state["assistant_id"],
            "prompt": prompt,
        }
        # Placeholder for assistant's response
        assistant_response_placeholder = st.chat_message("assistant").empty()
        response_text = ""
        with st.spinner("Assistant is typing..."):
            response = requests.get(f"{API_BASE_URL}/conversation", params=params, stream=True)
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=1024):
                    word = chunk.decode("utf-8")
                    response_text += word
                    assistant_response_placeholder.markdown(response_text)
                # Append user input and assistant response to chat history
                st.session_state["chat_history"].append({"role": "user", "content": prompt})
                st.session_state["chat_history"].append({"role": "assistant", "content": response_text})
            else:
                st.error("Failed to get a response. Check server logs.")
    else:
        st.error("Please create an assistant first.")

# Streamlit App Layout
st.title("🛠️ Product Management Bot")

# Sidebar for Assistant Creation and File Upload
with st.sidebar:
    st.header("Setup")
    if st.button("🔄 Create Assistant"):
        initiate_chat()
    
    # File uploader with on_change callback
    uploaded_file = st.file_uploader(
        "📁 Upload a file to assist your chat", 
        type=["txt", "pdf", "docx", 'html', 'xlsx', 'csv'], 
        key="uploaded_file",
        on_change=handle_file_upload
    )
    
    # Display Uploaded Files
    if st.session_state["uploaded_files"]:
        st.subheader("📂 Uploaded Files")
        for file in st.session_state["uploaded_files"]:
            st.markdown(f"- {file}")

# Chat Interface
st.subheader("💬 Chat with the Assistant")

# Display Chat History
for chat in st.session_state["chat_history"]:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# User Input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    # Process and display assistant response with streaming
    send_message_streaming(user_input)

# Optional: Add some spacing at the bottom
st.markdown("<br><br>", unsafe_allow_html=True)
