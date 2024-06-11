from flask import Flask, request, render_template, jsonify, session, send_from_directory, redirect, url_for, Response

import requests
import os
import shutil

app = Flask(__name__)

# Secret key for session management (change this to a secure value)
app.secret_key = 'your_secret_key'

# ChatPDF API key
API_KEY = 'sec_ceIvxemRi0BBWuHl1wDFWDBmAl3yh57b'

# Directory for storing uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to delete files in the upload folder
def clear_upload_folder():
    if os.path.exists(UPLOAD_FOLDER):
        files = os.listdir(UPLOAD_FOLDER)
        for file in files:
            file_path = os.path.join(UPLOAD_FOLDER, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

# Clear upload folder when the app starts
clear_upload_folder()

# Function to add a PDF to ChatPDF using the API

def add_pdf_to_chatpdf(file_path):
    url = 'https://api.chatpdf.com/v1/sources/add-file'
    headers = {'x-api-key': API_KEY}
    files = [('file', ('file.pdf', open(file_path, 'rb'), 'application/pdf'))]
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()['sourceId']
    else:
        return None

# Function to send a message to a PDF using the ChatPDF API


def send_message_to_pdf(source_id, message):
    url = 'https://api.chatpdf.com/v1/chats/message'
    headers = {'x-api-key': API_KEY, 'Content-Type': 'application/json'}
    data = {
        'sourceId': source_id,
        'messages': [{'role': 'user', 'content': message}]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['content']
    else:
        return None

# Function to read users from the text file
def read_users():
    users = {}
    with open('C:/Users/tusha/Desktop/FINALFINAL/Final/Final/users.txt', 'r') as file:
        for line in file:
            username, password = line.strip().split(',')
            users[username] = password
    return users

# Function to write users to the text file
def write_user(username, password):
    with open('users.txt', 'a') as file:
        file.write(f"{username},{password}\n")

# Your existing code...

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = read_users()
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = read_users()
        if username in users:
            return "Username already exists!"
        write_user(username, password)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))


@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' in request.files:
        pdf_file = request.files['file']
        if pdf_file.filename != '':
            # Ensure the 'uploads' directory exists
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            else:
                # If the directory exists, remove existing files
                files = os.listdir(UPLOAD_FOLDER)
                for file in files:
                    file_path = os.path.join(UPLOAD_FOLDER, file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        return jsonify({'status': 'error', 'message': 'Failed to clear directory'})

            # Save the uploaded PDF to the 'uploads' directory
            file_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
            pdf_file.save(file_path)

            # Add the PDF to ChatPDF and get the source ID
            source_id = add_pdf_to_chatpdf(file_path)

            if source_id:
                # Store the source_id and filename in the session
                session['source_id'] = source_id
                return jsonify({'status': 'success', 'source_id': source_id, 'filename': pdf_file.filename})
            else:
                return jsonify({'status': 'error', 'message': 'Failed to add PDF to ChatPDF'})
        else:
            return jsonify({'status': 'error', 'message': 'No file selected'})
    else:
        return jsonify({'status': 'error', 'message': 'File field not found'})

@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/chat', methods=['POST'])
def chat():
    message = request.form.get('message')

    if 'source_id' in session:
        source_id = session['source_id']
        if message:
            # Open a connection to the ChatPDF API
            url = 'https://api.chatpdf.com/v1/chats/message'
            headers = {'x-api-key': API_KEY, 'Content-Type': 'application/json'}
            data = {
                'sourceId': source_id,
                'messages': [{'role': 'user', 'content': message}]
            }
            response = requests.post(url, headers=headers, json=data, stream=True)

            if response.status_code == 200:
                # Set up streaming response to send back to the client
                def generate():
                    max_chunk_size = 1024
                    for chunk in response.iter_content(max_chunk_size):
                        yield chunk

                return Response(generate(), content_type='text/event-stream')
            else:
                return jsonify({'status': 'error', 'message': 'Failed to send message to PDF'})
    else:
        return jsonify({'status': 'error', 'message': 'No source ID found in session'})


if __name__ == '__main__':
    app.run(debug=True)
