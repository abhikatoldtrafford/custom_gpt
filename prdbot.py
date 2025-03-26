import streamlit as st
import requests
import json
import time
from datetime import datetime

# API Base URL
API_BASE_URL = "https://copilotv2.azurewebsites.net/" 

# Initialize session state
if "assistant_id" not in st.session_state:
    st.session_state["assistant_id"] = None
if "session_id" not in st.session_state:
    st.session_state["session_id"] = None
if "vector_store_id" not in st.session_state:
    st.session_state["vector_store_id"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []
if "last_trim" not in st.session_state:
    st.session_state["last_trim"] = None
if "show_advanced" not in st.session_state:
    st.session_state["show_advanced"] = False
if "thread_created_time" not in st.session_state:
    st.session_state["thread_created_time"] = None

# Function to initiate chat with optional context
def initiate_chat(context=None):
    with st.spinner("Creating assistant..."):
        data = {}
        files = {}
        
        # Add context if provided
        if context:
            data["context"] = context
            
        # Add file if provided
        uploaded_file = st.session_state.get("uploaded_file")
        if uploaded_file and not st.session_state["session_id"]:
            files = {"file": uploaded_file}
            
        response = requests.post(f"{API_BASE_URL}/initiate-chat", data=data, files=files)
        
    if response.status_code == 200:
        data = response.json()
        st.session_state["assistant_id"] = data["assistant"]
        st.session_state["session_id"] = data["session"]
        st.session_state["vector_store_id"] = data["vector_store"]
        st.session_state["chat_history"] = []  # Reset chat history on new session
        st.session_state["thread_created_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # If a file was uploaded during initialization, add it to the list
        if uploaded_file and not uploaded_file.name in st.session_state["uploaded_files"]:
            st.session_state["uploaded_files"].append(uploaded_file.name)
            
        st.success("Assistant created successfully!")
        if context:
            st.info(f"Assistant initialized with context: '{context}'")
    else:
        st.error(f"Failed to create assistant. Status code: {response.status_code}")
        try:
            st.error(response.json())
        except:
            st.error("Could not parse error response")

# Function to create a new thread using co-pilot endpoint
def create_new_thread(context=None):
    if not st.session_state["assistant_id"] or not st.session_state["vector_store_id"]:
        st.error("Cannot create a new thread. No assistant or vector store exists.")
        return False
        
    with st.spinner("Creating new thread..."):
        data = {
            "assistant": st.session_state["assistant_id"],
            "vector_store": st.session_state["vector_store_id"]
        }
        
        # Add context if provided
        if context:
            data["context"] = context
            
        response = requests.post(f"{API_BASE_URL}/co-pilot", data=data)
        
    if response.status_code == 200:
        data = response.json()
        # Update only the session ID, keeping assistant and vector store IDs
        st.session_state["session_id"] = data["session"]
        st.session_state["chat_history"] = []  # Reset chat history for new thread
        st.session_state["thread_created_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        st.success("New thread created successfully!")
        if context:
            st.info(f"Thread initialized with context: '{context}'")
        return True
    else:
        st.error(f"Failed to create new thread. Status code: {response.status_code}")
        try:
            st.error(response.json())
        except:
            st.error("Could not parse error response")
        return False

# Function to upload file
def upload_file(file):
    if st.session_state["assistant_id"]:
        with st.spinner("Uploading file..."):
            files = {"file": file}
            data = {"assistant": st.session_state["assistant_id"]}
            
            # Add session ID if available
            if st.session_state["session_id"]:
                data["session"] = st.session_state["session_id"]
                
            response = requests.post(f"{API_BASE_URL}/upload-file", files=files, data=data)
        if response.status_code == 200:
            st.session_state["uploaded_files"].append(file.name)
            st.success(f"File '{file.name}' uploaded successfully!")
            return True
        else:
            st.error(f"Failed to upload file. Status code: {response.status_code}")
            try:
                st.error(response.json())
            except:
                st.error("Could not parse error response")
            return False
    else:
        st.error("Please create an assistant first.")
        return False

# Callback function for file upload
def handle_file_upload():
    uploaded_file = st.session_state.uploaded_file
    if uploaded_file and uploaded_file.name not in st.session_state["uploaded_files"]:
        progress_bar = st.sidebar.progress(0)
        with st.sidebar:
            for percent_complete in range(100):
                time.sleep(0.01)  # Simulate upload time
                progress_bar.progress(percent_complete + 1)
        
        # If no assistant yet, wait until initiation
        if not st.session_state["assistant_id"]:
            st.info("File will be uploaded when assistant is created.")
        else:
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
                    if chunk:
                        word = chunk.decode("utf-8")
                        response_text += word
                        assistant_response_placeholder.markdown(response_text)
                # Append user input and assistant response to chat history
                st.session_state["chat_history"].append({"role": "user", "content": prompt})
                st.session_state["chat_history"].append({"role": "assistant", "content": response_text})
            else:
                st.error(f"Failed to get a response. Status code: {response.status_code}")
                try:
                    st.error(response.text)
                except:
                    st.error("Could not parse error response")
    else:
        st.error("Please create an assistant first.")

# Toggle advanced options
def toggle_advanced():
    st.session_state["show_advanced"] = not st.session_state["show_advanced"]

# Clear chat history but maintain session
def clear_chat_history():
    st.session_state["chat_history"] = []
    st.success("Chat history cleared. Session maintained.")

# Streamlit App Layout
st.title("🛠️ Product Management Bot")

# Sidebar for Assistant Creation and File Upload
with st.sidebar:
    st.header("Setup")
    
    # Context input for assistant creation
    context_input = st.text_area("💡 Initial Context (Optional)", 
        help="Provide initial context for the assistant. This context will be available for all conversations.")
    
    # Create assistant button
    if st.button("🔄 Create Assistant", help="Create a new assistant with optional context"):
        initiate_chat(context=context_input if context_input else None)
    
    # Create new thread button (only shown if assistant already exists)
    if st.session_state["assistant_id"] and st.session_state["vector_store_id"]:
        if st.button("🧵 New Thread", help="Create a new thread with the existing assistant and vector store"):
            create_new_thread(context=context_input if context_input else None)
    
    # File uploader with on_change callback
    uploaded_file = st.file_uploader(
        "📁 Upload a file to assist your chat", 
        type=["txt", "pdf", "docx", 'html', 'xlsx', 'csv', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'], 
        key="uploaded_file",
        on_change=handle_file_upload,
        help="Upload a file to provide additional context"
    )
    
    # Display Uploaded Files
    if st.session_state["uploaded_files"]:
        st.subheader("📂 Uploaded Files")
        for file in st.session_state["uploaded_files"]:
            st.markdown(f"- {file}")
    
    # Display current thread info if available
    if st.session_state["thread_created_time"]:
        st.subheader("🧵 Current Thread")
        st.info(f"Created: {st.session_state['thread_created_time']}")
    
    # Advanced options toggle
    st.button("⚙️ Advanced Options", on_click=toggle_advanced,
        help="Show or hide advanced options for testing thread trimming and file cleanup")
    
    # Advanced options
    if st.session_state["show_advanced"]:
        st.subheader("🧰 Advanced Options")
        
        # Clear chat history option
        if st.button("🧹 Clear Chat History", help="Clear chat history but maintain session"):
            clear_chat_history()
        
        # Display current IDs
        st.subheader("🔑 Current IDs")
        st.code(f"Assistant ID: {st.session_state['assistant_id']}")
        st.code(f"Session ID: {st.session_state['session_id']}")
        st.code(f"Vector Store ID: {st.session_state['vector_store_id']}")

# Chat Interface
st.subheader("💬 Chat with the Assistant")

# Display info about context if available
if context_input and st.session_state["session_id"]:
    st.info("This conversation has context information. Ask questions that might relate to the context!")

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
