import InvokeAgent as agenthelper
import streamlit as st
import json
import pandas as pd
import uuid
from PIL import Image, ImageOps, ImageDraw
import re
from collections import Counter
import os

# Function to load user credentials
def load_credentials():
    if os.path.exists('credentials.json'):
        with open('credentials.json', 'r') as f:
            return json.load(f)
    return {"users": []}

# Function to check credentials
def check_credentials(userid, password):
    credentials = load_credentials()
    for user in credentials["users"]:
        if user["userid"] == userid and user["password"] == password:
            return True
    return False

# Streamlit page configuration
st.set_page_config(page_title="Data Warehoue (DWH) Query Agent", page_icon="🤖", layout="wide")

# CSS to set the gradient background
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #100929 0%, #090B5D 100%);
        background-attachment: fixed;
        color: white;
    }
    /* Make all text white */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Authentication state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# Login form
if not st.session_state['authenticated']:
    st.title("Login")
    userid = st.text_input("User ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_credentials(userid, password):
            st.session_state['authenticated'] = True
            st.session_state['userid'] = userid
            st.rerun()
        else:
            st.error("Invalid User ID or password")
    st.stop()

# Function to extract sql query from response
def extract_queries(log_content):
    # Regular expression pattern to match <query>...</query>
    pattern = re.compile(r'<query>(.*?)</query>', re.DOTALL)
    
    # Find all matches
    matches = pattern.findall(log_content)
    
    # Create list of dictionaries
    queries_list = [{"query": match.strip()} for match in matches]
    
    return queries_list

# Removing duplicated queries
# def remove_consecutive_duplicates(queries_list):
#     # Remove consecutive duplicate queries
#     unique_queries = []
#     previous_query = None
#     for query in queries_list:
#         if query['query'] != previous_query:
#             unique_queries.append(query)
#         previous_query = query['query']
#     return unique_queries

def remove_duplicates(queries_list):
    # Remove all duplicates, preserving the order of first occurrence
    seen = set()
    unique_queries = []
    for query in queries_list:
        if query['query'] not in seen:
            unique_queries.append(query)
            seen.add(query['query'])
    return unique_queries


def count_unique_queries(queries_list):
    # Count occurrences of each query
    query_counter = Counter(query['query'] for query in queries_list)
    
    # Create a list of dictionaries with query and count
    counted_queries = [{"query": query, "count": count} for query, count in query_counter.items()]
    
    return counted_queries

# Function to parse and format response
def format_response(response_body):
    try:
        # Try to load the response as JSON
        data = json.loads(response_body)
        # If it's a list, convert it to a DataFrame for better visualization
        if isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return response_body
    except json.JSONDecodeError as e:
        response=f"Apologies, an error occured transforming the response: {str(e)}. Please rerun the application."
        print(response)
        # If response is not JSON, return as is
        return response_body



@st.cache_data
def generate_schema_questions(show_output=False):
    prompt = f"""
    User ID: {st.session_state['userid']}
    What are some of the questions that I can ask. Only show the questions in text format in natural language. Don't show the SQL query.

    Please generate a list of 10-15 natural language questions that can be asked based on the schema. The questions should cover different aspects of the data, such as filtering, aggregation, joining tables, and so on. Make sure the questions are clear, concise, and relevant to the given schema.
    """

    event = {
        "sessionId": st.session_state['session_id'],
        "question": prompt,
        "systemPrompt": f"User ID: {st.session_state['userid']}"  # Include username in system prompt
    }
    response = agenthelper.lambda_handler(event, None)

    try:
        if response and 'body' in response and response['body']:
            response_data = json.loads(response['body'])
        else:
            if show_output:
                st.write("Invalid or empty response received")
    except json.JSONDecodeError as e:
        if show_output:
            st.write(f"JSON decoding error: {e}")
        response_data = None

    try:
        the_response = response_data['trace_data']
    except:
        the_response = "Apologies, but an error occurred. Please rerun the application"

    return the_response



# Session State Management
if 'history' not in st.session_state:
    st.session_state['history'] = []
    st.session_state['schema_questions'] = None
    st.session_state['session_id'] = str(uuid.uuid4())

if 'queries' not in st.session_state:
    st.session_state['queries'] = []

# Generate and display schema-based questions (run only once)
if st.session_state['schema_questions'] is None:
    st.session_state['schema_questions'] = generate_schema_questions(show_output=False)


# Title
st.write("## Analytics with Amazon Redshift and Amazon Bedrock")

st.write("### Welcome to the Data Warehouse (DWH) Chat Agent!")
st.write("This app allows you to enter natural language queries and get SQL queries results from Amazon Redshift")

st.write("### Possible Questions Based on the Schema")
st.write(st.session_state['schema_questions'])

# Sidebar for user input
st.sidebar.title("Trace Data")

# Function to extract SQL query from trace data
def extract_sql_query(trace_data):
    try:
        sql_query = trace_data.split("SQL Query:")[1].strip()
        return sql_query
    except IndexError:
        return "No SQL query found in the trace data."

# Session State Management
if 'history' not in st.session_state:
    st.session_state['history'] = []

# Clear history button
clear_history_button = st.button("Clear History")
if clear_history_button:
    st.session_state['history'] = []

# Display conversation history
st.write("### Conversation History")

chat_container = st.container()  # Create a container for conversation history

# Display the entire conversation history
with chat_container:
    for message in st.session_state['history']:
        if message['role'] == 'user':
            with chat_container.chat_message(message['role']):
                st.markdown(message['text'])
        else:
            with chat_container.chat_message(message['role']):
                st.markdown(message['text'])

# Display a text box for input
prompt = st.chat_input("Enter your natural language query here:")

# Display a button to end the session
end_session_button = st.button("End Session")

# Handling user input and responses
if prompt:
    # Update the conversation history with the user's question
    st.session_state['history'].append({"role": "user", "text": prompt})

    with chat_container.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Processing your query..."):
        event = {
            "sessionId": st.session_state['session_id'],
            "question": f"User ID: {st.session_state['userid']}\n{prompt}"
        }
        response = agenthelper.lambda_handler(event, None)

    try:
        if response and 'body' in response and response['body']:
            response_data = json.loads(response['body'])
        else:
            st.write("Invalid or empty response received")
    except json.JSONDecodeError as e:
        st.write("JSON decoding error:", e)
        response_data = None

    try:
        all_data = format_response(response_data['response'])
        the_response = response_data['trace_data']
    except KeyError as e:
        all_data = "..."
        # the_response = f"Apologies, but an error occurred while accessing the response data. The key '{e.args[0]}' was not found in the response. Please rerun the application."
        the_response = f"Apologies, I didn't get that. Can you please rephrase your question? {str(e)}"
    except Exception as e:
        all_data = "..."
        the_response = f"Apologies, but an error occurred: {str(e)}. Please rerun the application."
    # Truncate response_data if it's longer than 1000 characters
    truncated_response_data = str(response_data)
    st.session_state['queries'] = extract_queries(truncated_response_data)

    if len(truncated_response_data) > 10000:
        truncated_response_data = "..." + truncated_response_data[-10000:]

    # Display truncated response data in the sidebar
    st.sidebar.text_area("Truncated Response Data", value=truncated_response_data, height=300)
    
    st.sidebar.divider()
    # recent_queries = st.session_state['queries']
    # st.sidebar.text_area("Recent Queries",value=st.session_state['queries'])
    
    # # Remove consecutive duplicates
    # unique_queries_list = remove_duplicates(st.session_state['queries'])
    
    # Count unique queries
    counted_queries_list = count_unique_queries(st.session_state['queries'])
    
    # Prepare the queries for display in the sidebar
    queries_text = "\n\n".join([f"{query['query']} (Count: {query['count']})" for query in counted_queries_list])
    
    # Create a container with a fixed width
    with st.sidebar.container():   
        st.sidebar.markdown("### Recent Queries")
        if st.session_state['queries']:
            # st.sidebar.text_area("Recent Queries",queries_text,height=250)
            st.sidebar.markdown(queries_text)
            # st.sidebar.text_area.table(st.session_state['queries'])
        else:
            st.sidebar.markdown("*No queries found in the trace file.*")
            # st.sidebar.text_area("Recent Queries","No queries found in the trace file.",height=250)


    # Add the bot's response to the conversation history
    st.session_state['history'].append({"role": "assistant", "text": the_response})

    with chat_container.chat_message("assistant"):
        st.markdown(the_response)

    st.session_state['trace_data'] = the_response

if end_session_button:
    event = {
        "sessionId": st.session_state['session_id'],
        "question": "placeholder to end session",
        "endSession": True
    }
    agenthelper.lambda_handler(event, None)
    st.session_state['history'].clear()
    chat_container.empty()  # Clear the conversation history display