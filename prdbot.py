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
if "last_assistant_message" not in st.session_state:
    st.session_state["last_assistant_message"] = ""  # Store last assistant message for download
if "next_question_suggestions" not in st.session_state:
    st.session_state["next_question_suggestions"] = []  # Store 2 next question suggestions
if "selected_suggestion" not in st.session_state:
    st.session_state["selected_suggestion"] = None

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
def create_new_thread():
    if not st.session_state["assistant_id"] or not st.session_state["vector_store_id"]:
        st.error("Cannot create a new thread. No assistant or vector store exists.")
        return False
        
    with st.spinner("Creating new session..."):
        data = {
            "assistant": st.session_state["assistant_id"],
            "vector_store": st.session_state["vector_store_id"]
        }
        
        response = requests.post(f"{API_BASE_URL}/co-pilot", data=data)
        
    if response.status_code == 200:
        data = response.json()
        # Get the new thread ID
        thread_id = data["session"]
        st.session_state["session_id"] = thread_id
        
        # Generate thread name automatically
        thread_name = f"Session {st.session_state['thread_name_counter']}"
        st.session_state["thread_name_counter"] += 1
            
        # Store thread info
        thread_created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state["threads"][thread_id] = {
            "name": thread_name,
            "created_at": thread_created_time,
            "context": ""  # No context for new sessions
        }
        
        # Initialize chat history for this thread
        st.session_state["chat_history"][thread_id] = []
        st.session_state["active_thread"] = thread_id
        
        st.success(f"New session '{thread_name}' created successfully!")
        return True
    else:
        st.error(f"Failed to create new session. Status code: {response.status_code}")
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

# Function to generate next question suggestions
def generate_next_question_suggestions(user_message, assistant_response):
    """Generate 2 suggested next questions based on the conversation"""
    try:
        # Use a simple prompt to generate short, relevant follow-up questions
        prompt = f"""Based on this conversation:
User: {user_message}
Assistant: {assistant_response}

Generate 2 different natural follow-up questions, each in 4-5 words that would be relevant to continue this conversation. Separate them with '|' character. Just the questions, nothing else."""
        
        # Make API call to generate suggestions
        params = {
            "session": st.session_state["session_id"],
            "assistant": st.session_state["assistant_id"],
            "prompt": prompt,
        }
        
        response = requests.get(f"{API_BASE_URL}/chat", params=params)
        
        if response.status_code == 200:
            data = response.json()
            suggestion_text = data.get("response", "").strip()
            # Split by | character
            suggestions = suggestion_text.split('|')
            # Ensure each suggestion is roughly 4-5 words
            formatted_suggestions = []
            for suggestion in suggestions[:2]:  # Take only first 2
                suggestion = suggestion.strip()
                words = suggestion.split()
                if len(words) > 7:
                    suggestion = " ".join(words[:5]) + "..."
                if suggestion:
                    formatted_suggestions.append(suggestion)
            
            # Ensure we have exactly 2 suggestions
            while len(formatted_suggestions) < 2:
                formatted_suggestions.append("Continue this topic")
            
            return formatted_suggestions[:2]
        else:
            return ["Continue this topic", "Ask another question"]
    except Exception as e:
        st.error(f"Error generating next questions: {e}")
        return ["Continue this topic", "Ask another question"]

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
                    
                    # Store the last assistant message for download
                    st.session_state["last_assistant_message"] = response_text
                    
                    # Store conversation in chat history
                    if thread_id not in st.session_state["chat_history"]:
                        st.session_state["chat_history"][thread_id] = []
                    st.session_state["chat_history"][thread_id].append({"role": "user", "content": prompt})
                    st.session_state["chat_history"][thread_id].append({"role": "assistant", "content": response_text})
                    
                    # Generate next question suggestions
                    next_suggestions = generate_next_question_suggestions(prompt, response_text)
                    st.session_state["next_question_suggestions"] = next_suggestions
                    
                    # Force rerun to show download and suggestions immediately
                    st.rerun()
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
        
        # New thread creation section - simplified
        st.divider()
        st.subheader("🧵 Create New Thread")
        
        # Create new session button
        if st.button("➕ New Session", help="Create a new session"):
            create_new_thread()
    
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

# Download button for last assistant message
if st.session_state["last_assistant_message"]:
    col1, col2 = st.columns([0.9, 0.1])
    with col2:
        st.download_button(
            label="⬇️",
            data=st.session_state["last_assistant_message"],
            file_name=f"assistant_response_{current_thread_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            help="Download last assistant response"
        )

# Display next question suggestions
if st.session_state["next_question_suggestions"]:
    
    # Use columns to display suggestions side by side
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(st.session_state["next_question_suggestions"][0], 
                    key="suggestion_1",
                    use_container_width=True):
            st.session_state.selected_suggestion = st.session_state["next_question_suggestions"][0]
            st.rerun()
    
    with col2:
        if st.button(st.session_state["next_question_suggestions"][1], 
                    key="suggestion_2",
                    use_container_width=True):
            st.session_state.selected_suggestion = st.session_state["next_question_suggestions"][1]
            st.rerun()

# User Input
user_input = st.chat_input(placeholder="Or type your own message...")

# Handle suggestion click
if st.session_state.selected_suggestion:
    user_input = st.session_state.selected_suggestion
    st.session_state.selected_suggestion = None

if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    # Process and display assistant response with streaming
    send_message_streaming(user_input)

# Optional: Add some spacing at the bottom
st.markdown("<br><br>", unsafe_allow_html=True)
