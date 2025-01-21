import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

# API Base URL
API_BASE_URL = "https://copilot-updated.azurewebsites.net/"  # Replace with your actual API URL

# Initialize session state
if "assistant_id" not in st.session_state:
    st.session_state["assistant_id"] = None
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []

# Function to upload files and create an assistant
def upload_files_and_create_assistant(files):
    """Upload files and create an assistant for data analysis."""
    try:
        # Prepare files for upload
        files_to_upload = [("files", file) for file in files]
        
        # Call the /data-analysis endpoint
        response = requests.post(
            f"{API_BASE_URL}/data-analysis",
            files=files_to_upload,
            data={"user_input": "Initialize data analysis."}  # Initial query to analyze files
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state["assistant_id"] = data["assistant_id"]
            st.session_state["thread_id"] = data["thread_id"]
            st.session_state["uploaded_files"] = files  # Store file objects
            st.success("Files uploaded and assistant created successfully!")
        else:
            st.error(f"Failed to upload files and create assistant. Error: {response.text}")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Function to send a message and get a response
def send_message(user_input):
    """Send a user message and get the assistant's response."""
    if not st.session_state["assistant_id"] or not st.session_state["thread_id"]:
        st.error("Please upload files and create an assistant first.")
        return

    try:
        # Call the /data-analysis endpoint with the user's input
        response = requests.post(
            f"{API_BASE_URL}/data-analysis",
            data={
                "user_input": user_input,
                "assistant_id": st.session_state["assistant_id"],
                "thread_id": st.session_state["thread_id"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assistant_response = data["response"]
            
            # Display the assistant's response
            for item in assistant_response:
                if item["type"] == "text":
                    with st.chat_message("assistant"):
                        st.markdown(item["content"])
                    st.session_state["chat_history"].append({"role": "assistant", "content": item["content"]})
                elif item["type"] == "image":
                    # Decode the base64 image
                    image_data = base64.b64decode(item["content"])
                    image = Image.open(BytesIO(image_data))
                    
                    # Display the image
                    with st.chat_message("assistant"):
                        st.image(image, caption="Generated Image", use_column_width=True)
                    
                    # Store the image in chat history
                    st.session_state["chat_history"].append({"role": "assistant", "content": f"![Generated Image](data:image/png;base64,{item['content']})"})
        else:
            st.error(f"Failed to get a response. Error: {response.text}")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Streamlit App Layout
st.title("📊 Data Analysis Assistant")

# Sidebar for file upload and assistant creation
with st.sidebar:
    st.header("📁 File Upload")
    uploaded_files = st.file_uploader(
        "Upload your data files",
        type=["csv", "xlsx", "txt", "pdf"],  # Supported file types
        accept_multiple_files=True
    )
    
    if st.button("🚀 Start Analysis"):
        if uploaded_files:
            with st.spinner("Uploading files and creating assistant..."):
                upload_files_and_create_assistant(uploaded_files)
        else:
            st.error("Please upload at least one file.")

    # Display uploaded files
    if st.session_state["uploaded_files"]:
        st.subheader("📂 Uploaded Files")
        for file in st.session_state["uploaded_files"]:
            st.markdown(f"- {file.name}")  # Use file.name to get the file name

# Chat Interface
st.subheader("💬 Chat with the Assistant")

# Display chat history
for chat in st.session_state["chat_history"]:
    with st.chat_message(chat["role"]):
        if chat["content"].startswith("![Generated Image]"):
            st.image(chat["content"].split("(")[1].rstrip(")"), caption="Generated Image", use_column_width=True)
        else:
            st.markdown(chat["content"])

# User input
user_input = st.chat_input("Ask about your data...")
if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state["chat_history"].append({"role": "user", "content": user_input})
    
    # Get assistant response
    send_message(user_input)
