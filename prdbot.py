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
    st.session_state["chat_history"] = {}  # Changed to dict to store history per thread
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []
if "show_advanced" not in st.session_state:
    st.session_state["show_advanced"] = False
if "threads" not in st.session_state:
    st.session_state["threads"] = {}  # Store info about all threads
if "active_thread" not in st.session_state:
    st.session_state["active_thread"] = None  # Current active thread ID
if "thread_name_counter" not in st.session_state:
    st.session_state["thread_name_counter"] = 1  # Counter for default thread names
if "should_rename_thread" not in st.session_state:
    st.session_state["should_rename_thread"] = False

# Function to initiate chat with optional context
def initiate_chat(context=None, thread_name=None):
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
        thread_id = data["session"]
        st.session_state["session_id"] = thread_id
        st.session_state["vector_store_id"] = data["vector_store"]
        
        # Generate thread name if not provided
        if not thread_name:
            thread_name = f"Thread {st.session_state['thread_name_counter']}"
            st.session_state["thread_name_counter"] += 1
        
        # Store thread info
        thread_created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state["threads"][thread_id] = {
            "name": thread_name,
            "created_at": thread_created_time,
            "context": context if context else ""
        }
        
        # Initialize chat history for this thread
        st.session_state["chat_history"][thread_id] = []
        st.session_state["active_thread"] = thread_id
        
        # If a file was uploaded during initialization, add it to the list
        if uploaded_file and not uploaded_file.name in st.session_state["uploaded_files"]:
            st.session_state["uploaded_files"].append(uploaded_file.name)
            
        st.success("Assistant created successfully!")
        if context:
            st.info(f"Thread initialized with context: '{context}'")
    else:
        st.error(f"Failed to create assistant. Status code: {response.status_code}")
        try:
            st.error(response.json())
        except:
            st.error("Could not parse error response")

# Function to create a new thread using co-pilot endpoint
def create_new_thread(context=None, thread_name=None):
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
        # Get the new thread ID
        thread_id = data["session"]
        st.session_state["session_id"] = thread_id
        
        # Generate thread name if not provided
        if not thread_name:
            thread_name = f"Thread {st.session_state['thread_name_counter']}"
            st.session_state["thread_name_counter"] += 1
            
        # Store thread info
        thread_created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state["threads"][thread_id] = {
            "name": thread_name,
            "created_at": thread_created_time,
            "context": context if context else ""
        }
        
        # Initialize chat history for this thread
        st.session_state["chat_history"][thread_id] = []
        st.session_state["active_thread"] = thread_id
        
        st.success(f"New thread '{thread_name}' created successfully!")
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

# Function to switch between threads
def switch_thread():
    selected_thread = st.session_state.get("thread_selector")
    if selected_thread and selected_thread in st.session_state["threads"]:
        st.session_state["session_id"] = selected_thread
        st.session_state["active_thread"] = selected_thread

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
# Function to handle conversation with streaming
def send_message_streaming(prompt):
    thread_id = st.session_state["session_id"]
    if thread_id:
        params = {
            "session": thread_id,
            "assistant": st.session_state["assistant_id"],
            "prompt": prompt,
        }
        # Placeholder for assistant's response
        assistant_response_placeholder = st.chat_message("assistant").empty()
        response_text = ""
        with st.spinner("Assistant is typing..."):
            try:
                response = requests.get(f"{API_BASE_URL}/conversation", params=params, stream=True)
                if response.status_code == 200:
                    # Parse SSE (Server-Sent Events) stream
                    for line in response.iter_lines():
                        if line:
                            line_str = line.decode("utf-8").strip()
                            
                            # Check for [DONE] signal
                            if line_str == "data: [DONE]":
                                break
                            
                            # Check if line starts with "data: "
                            if line_str.startswith("data: "):
                                try:
                                    # Extract JSON payload
                                    json_str = line_str[6:]  # Remove "data: " prefix
                                    chunk_data = json.loads(json_str)
                                    
                                    # Extract content from the stream
                                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                                        delta = chunk_data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            content = delta["content"]
                                            response_text += content
                                            # Update the UI with the accumulated text
                                            assistant_response_placeholder.markdown(response_text)
                                            
                                except json.JSONDecodeError as e:
                                    st.error(f"Error parsing JSON: {str(e)}\nLine: {line_str}")
                                    continue
                    
                    # Store conversation in chat history
                    if thread_id not in st.session_state["chat_history"]:
                        st.session_state["chat_history"][thread_id] = []
                    st.session_state["chat_history"][thread_id].append({"role": "user", "content": prompt})
                    st.session_state["chat_history"][thread_id].append({"role": "assistant", "content": response_text})
                else:
                    st.error(f"Failed to get a response. Status code: {response.status_code}")
                    try:
                        st.error(response.text)
                    except:
                        st.error("Could not parse error response")
            except Exception as e:
                st.error(f"Error in streaming response: {str(e)}")
    else:
        st.error("Please create an assistant and thread first.")

# Toggle advanced options
def toggle_advanced():
    st.session_state["show_advanced"] = not st.session_state["show_advanced"]

# Clear chat history but maintain session
def clear_chat_history():
    thread_id = st.session_state["session_id"]
    if thread_id and thread_id in st.session_state["chat_history"]:
        st.session_state["chat_history"][thread_id] = []
        st.success("Chat history cleared for current thread. Session maintained.")
    else:
        st.error("No active thread to clear.")

# Set flag to rename thread when button is clicked
def trigger_rename_thread():
    st.session_state["should_rename_thread"] = True

# Streamlit App Layout
st.title("🛠️ Product Management Bot")

# Sidebar for Assistant Creation, Thread Management, and File Upload
with st.sidebar:
    st.header("Setup")
    
    # Assistant creation section
    if not st.session_state["assistant_id"]:
        # Create assistant button
        if st.button("🔄 Create Assistant", help="Create a new assistant with optional context"):
            initiate_chat(
                context= '',
                thread_name=None
            )
    
    # Thread management section (only shown if assistant already exists)
    else:
        st.subheader("🧵 Thread Management")
        
        # Thread selection - show if we have multiple threads
        if len(st.session_state["threads"]) > 0:
            thread_options = {}
            for thread_id, info in st.session_state["threads"].items():
                thread_options[thread_id] = f"{info['name']} ({info['created_at']})"
            
            # Get current thread ID for default selection
            current_thread_id = st.session_state["active_thread"]
            
            # Thread selector
            st.selectbox(
                "Select Thread", 
                options=list(thread_options.keys()),
                format_func=lambda x: thread_options[x],
                index=list(thread_options.keys()).index(current_thread_id) if current_thread_id in thread_options else 0,
                key="thread_selector",
                on_change=switch_thread
            )
            
            # Display current thread context if available
            if current_thread_id and current_thread_id in st.session_state["threads"]:
                thread_context = st.session_state["threads"][current_thread_id].get("context", "")
                if thread_context:
                    st.info(f"Current thread context: '{thread_context}'")
            
            # Thread renaming
            thread_id = st.session_state["active_thread"]
            if thread_id and thread_id in st.session_state["threads"]:
                new_name = st.text_input("Rename Current Thread:", 
                                        value=st.session_state["threads"][thread_id]["name"])
                
                if st.button("✏️ Rename Thread"):
                    if new_name.strip():
                        st.session_state["threads"][thread_id]["name"] = new_name
                        st.success(f"Thread renamed to '{new_name}'")
                        st.rerun()
        
        # New thread creation section
        st.divider()
        st.subheader("🧵 Create New Thread")
        
        # Context for new thread
        new_thread_context = st.text_area("💡 Thread Context", 
            help="Context specific to this new thread conversation")
        
        # Thread name input
        new_thread_name = st.text_input("🏷️ Thread Name", 
            placeholder=f"Default: Thread {st.session_state['thread_name_counter']}",
            help="Give a name to this thread for easier identification")
        
        # Create new thread button
        if st.button("➕ New Thread", help="Create a new thread with the existing assistant"):
            create_new_thread(
                context=new_thread_context if new_thread_context else None,
                thread_name=new_thread_name if new_thread_name else None
            )
    
    # File uploader (available for both new and existing assistants)
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
    
    # Advanced options toggle
    st.button("⚙️ Advanced Options", on_click=toggle_advanced,
        help="Show or hide advanced options")
    
    # Advanced options
    if st.session_state["show_advanced"]:
        st.subheader("🧰 Advanced Options")
        
        # Clear chat history option
        if st.button("🧹 Clear Current Thread History", help="Clear chat history but maintain session"):
            clear_chat_history()
        
        # Display current IDs
        st.subheader("🔑 Current IDs")
        st.code(f"Assistant ID: {st.session_state['assistant_id']}")
        st.code(f"Active Thread ID: {st.session_state['session_id']}")
        st.code(f"Vector Store ID: {st.session_state['vector_store_id']}")
        st.code(f"Total Threads: {len(st.session_state['threads'])}")

# Chat Interface
st.subheader("💬 Chat with the Assistant")

# Get current thread ID and name
current_thread_id = st.session_state["session_id"]
current_thread_name = "No active thread"
if current_thread_id and current_thread_id in st.session_state["threads"]:
    current_thread_name = st.session_state["threads"][current_thread_id]["name"]

# Display current thread name
if current_thread_id:
    st.markdown(f"**Current Thread: {current_thread_name}**")

# Display Chat History for current thread
if current_thread_id and current_thread_id in st.session_state["chat_history"]:
    for chat in st.session_state["chat_history"][current_thread_id]:
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
