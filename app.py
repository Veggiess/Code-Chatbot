from flask import Flask, request, jsonify, render_template
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.tools.retriever import create_retriever_tool
from langgraph.prebuilt import chat_agent_executor
from dotenv import load_dotenv
from datetime import datetime
import os
import logging
import requests
import bs4
import sqlite3

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Initialize the model
model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Set environment variables
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize components
memory = None  # Memory is not used in this file-based approach
search = TavilySearchResults(max_results=2)

# Load and process documents
bs4_strainer = bs4.SoupStrainer(class_=("post-title", "post-header", "post-content"))
loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs={"parse_only": bs4_strainer},
)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, add_start_index=True
)
all_splits = text_splitter.split_documents(docs)

vectorstore = Chroma.from_documents(documents=all_splits, embedding=OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})

retriever_tool = create_retriever_tool(
    retriever,
    "langsmith_search",
    "Search for information about LangSmith. For any questions about LangSmith, you must use this tool!",
)

tools = [search, retriever_tool]

# Create agent executor
agent_executor = chat_agent_executor.create_tool_calling_executor(model, tools, checkpointer=memory)

# Config with required thread_id
config = {"configurable": {"thread_id": "abc123"}}

# Initialize Flask app
app = Flask(__name__)

# Database file path
DATABASE = 'app_data.db'

# Function to create a connection to the database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To access rows as dictionaries
    return conn

# Create tables for users and chat history
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Function to load user data from the database
def load_user_data(email):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user

# Function to save new user data to the database
def save_user_data(username, email, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, password))
    conn.commit()
    conn.close()

# Function to load chat history from the database
def load_chat_history(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY timestamp ASC', (user_id,))
    messages = []
    rows = c.fetchall()
    for row in rows:
        if row['role'] == 'User':
            messages.append(HumanMessage(content=row['content']))
        elif row['role'] == 'AI':
            messages.append(AIMessage(content=row['content']))
    conn.close()
    return messages

# Function to save a message to the database
def save_message_to_db(user_id, role, content):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)', (user_id, role, content))
    conn.commit()
    conn.close()

# Function to send code execution request to separate server
def execute_code_remotely(language, code):
    try:
        url = f"http://127.0.0.1:5001/execute"
        payload = {"language": language, "code": code}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get("result", "No result returned from server.")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return str(e)

# Function to load ICL examples from file
def load_icl_examples(file_path):
    messages = []
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith("[User]: "):
                    content = line[len("[User]: "):].strip()
                    messages.append(HumanMessage(content=content))
                elif line.startswith("[AI]: "):
                    content = line[len("[AI]: "):].strip()
                    messages.append(AIMessage(content=content))
    return messages

# Define the main route
@app.route('/')
def index():
    return render_template('index.html')

# Define the route to process user input
@app.route('/process', methods=['POST'])
def process():
    try:
        user_input = request.json.get('input')
        username = request.json.get('username')
        email = request.json.get('email')
        
        if not user_input or not username or not email:
            return jsonify({'error': 'Invalid input'}), 400
        
        logging.debug(f"User input received: {user_input}")

        # Load or create user
        user = load_user_data(email)
        if not user:
            save_user_data(username, email, None)  # Password is not set initially
            user = load_user_data(email)

        user_id = user['id']

        # Load previous chat history
        messages = load_chat_history(user_id)

        # Load ICL examples
        icl_examples = load_icl_examples('icl_examples.txt')

        # Add in-context examples to the beginning of the messages
        messages = icl_examples + messages

        # Add user input to chat history
        usr_msg = HumanMessage(content=user_input)
        messages.append(usr_msg)
        save_message_to_db(user_id, "User", user_input)

        logging.debug(f"Invoking agent with messages: {messages}")

        if user_input.startswith("python:"):
            code = user_input[len("python:"):].strip()
            result = execute_code_remotely("python", code)
            ai_msg_content = f"Execution result:\n{result}"
        elif user_input.startswith("java:"):
            code = user_input[len("java:"):].strip()
            result = execute_code_remotely("java", code)
            ai_msg_content = f"Execution result:\n{result}"
        else:
            response = agent_executor.invoke({"messages": messages}, config=config)
            ai_msg_content = response["messages"][-1].content
        
        logging.debug(f"AI response: {ai_msg_content}")

        ai_msg = AIMessage(content=ai_msg_content)
        messages.append(ai_msg)
        save_message_to_db(user_id, "AI", ai_msg.content)

        return jsonify({'result': ai_msg.content})
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return jsonify({'error': 'Failed to process request'}), 500

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    
    user = load_user_data(email)
    
    if user:
        return jsonify({'error': 'Email already registered'}), 400
    
    save_user_data(username, email, password)
    
    return jsonify({'success': True})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    
    user = load_user_data(email)
    
    if not user or user['password'] != password:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    return jsonify({'success': True, 'user_id': user['id']})

if __name__ == '__main__':
    app.run(debug=True)
