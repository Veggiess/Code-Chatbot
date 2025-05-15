from flask import Flask, request, jsonify
import subprocess
import os
import io
import sys
import re
from datetime import datetime
import sqlite3

app = Flask(__name__)

# Database file path
DATABASE = 'app_data.db'

# Function to create a connection to the database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To access rows as dictionaries
    return conn

# Create tables for chat history
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Function to save execution results to the database
def save_message_to_db(user_id, role, content):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)', (user_id, role, content))
    conn.commit()
    conn.close()

# Function to execute Python code
def execute_python_code(code):
    try:
        old_stdout = sys.stdout
        sys.stdout = new_stdout = io.StringIO()
        exec(code, {})
        result = new_stdout.getvalue()
    except Exception as e:
        result = str(e)
    finally:
        sys.stdout = old_stdout
    return result

# Function to execute Java code
def execute_java_code(code):
    try:
        match = re.search(r'public\s+class\s+(\w+)', code)
        if not match:
            return "Error: No public class found in the Java code."
        
        class_name = match.group(1)
        file_name = f"{class_name}.java"
        
        with open(file_name, "w") as file:
            file.write(code)
        
        compile_process = subprocess.run(["javac", file_name], capture_output=True, text=True)
        if compile_process.returncode != 0:
            return compile_process.stderr
        
        run_process = subprocess.run(["java", class_name], capture_output=True, text=True)
        if run_process.returncode != 0:
            return run_process.stderr
        
        return run_process.stdout
    except Exception as e:
        return str(e)
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
        class_file = f"{class_name}.class"
        if os.path.exists(class_file):
            os.remove(class_file)

@app.route('/execute', methods=['POST'])
def execute():
    try:
        data = request.json
        language = data.get("language")
        code = data.get("code")
        user_id = data.get("user_id")  # Expecting user_id to be sent in the request

        if not user_id or not language or not code:
            return jsonify({"error": "Invalid input"}), 400

        if language == "python":
            result = execute_python_code(code)
        elif language == "java":
            result = execute_java_code(code)
        else:
            return jsonify({"error": "Unsupported language"}), 400

        # Save the execution result to the database as an AI message
        save_message_to_db(user_id, "AI", result)

        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
