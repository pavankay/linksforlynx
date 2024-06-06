from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from bson.objectid import ObjectId
from datetime import datetime
from flask_paginate import Pagination, get_page_parameter
import os
import base64

app = Flask(__name__)
app.secret_key = '4b3403665fea6c6628d7f6c02b8d93e1'  # Replace with your generated secret key

# MongoDB configuration
DB_NAME = "LinksforLynx"
USER_COLLECTION = "users"
PROJECT_COLLECTION = "projects"
app.config["MONGO_URI"] = f"mongodb+srv://pavan:PsxriMfTSYLltWgK@lfl.rvewoyg.mongodb.net/{DB_NAME}?retryWrites=true&w=majority"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'LinksforLynxautoemailsender@gmail.com'  # Use your actual Gmail address
app.config['MAIL_PASSWORD'] = os.getenv('PASSWORD')  # Use your generated App Password
app.config['MAIL_DEFAULT_SENDER'] = 'LinksforLynxautoemailsender@gmail.com'  # Ensure this matches MAIL_USERNAME

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

def generate_confirmation_token(email):
    return s.dumps(email, salt='email-confirm-salt')

def confirm_token(token, expiration=3600):
    try:
        email = s.loads(token, salt='email-confirm-salt', max_age=expiration)
    except:
        return False
    return email

def send_email(to, subject, template):
    msg = Message(subject, recipients=[to], html=template)
    try:
        mail.send(msg)
        print(f"Sending email to: {to}") 
    except Exception as e:
        print(f"Failed to send email to {to}. Error: {e}")

# Custom filter to convert ObjectId to string
@app.template_filter('to_str')
def to_str(value):
    return str(value)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username').lower()
        email = request.form.get('email').lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        user_collection = mongo.db[USER_COLLECTION]
        user = user_collection.find_one({"email": email})

        if user:
            flash('Email address already exists', 'danger')
            return redirect(url_for('signup'))

        user_collection.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password,
            "confirmed": False  # Add a confirmed field
        })

        token = generate_confirmation_token(email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(email, subject, html)

        session['user'] = username
        flash('A confirmation email has been sent via email.', 'success')
        return redirect(url_for('unconfirmed'))

    return render_template('signup.html')

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('index'))

    user_collection = mongo.db[USER_COLLECTION]
    user = user_collection.find_one({"email": email})

    if user['confirmed']:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user_collection.update_one({"email": email}, {"$set": {"confirmed": True}})
        flash('You have confirmed your account. Thanks!', 'success')

    return redirect(url_for('login'))

@app.route('/resend')
def resend_confirmation():
    if 'user' in session:
        user_collection = mongo.db[USER_COLLECTION]
        user = user_collection.find_one({"username": session['user']})
        if user and not user['confirmed']:
            token = generate_confirmation_token(user['email'])
            confirm_url = url_for('confirm_email', token=token, _external=True)
            html = render_template('activate.html', confirm_url=confirm_url)
            subject = "Please confirm your email"
            send_email(user['email'], subject, html)
            flash('A new confirmation email has been sent.', 'success')
            return redirect(url_for('unconfirmed'))
    flash('Invalid request or user not logged in.', 'danger')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')

        user_collection = mongo.db[USER_COLLECTION]
        user = user_collection.find_one({"email": email})

        if user and bcrypt.check_password_hash(user['password'], password):
            if not user['confirmed']:
                flash('Please confirm your email address first.', 'danger')
                return redirect(url_for('unconfirmed'))
            session['user'] = user['username']
            return redirect(url_for('my_projects'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/unconfirmed')
def unconfirmed():
    if 'user' in session:
        user_collection = mongo.db[USER_COLLECTION]
        user = user_collection.find_one({"username": session['user']})
        if user['confirmed']:
            return redirect(url_for('my_projects'))
    flash('Please confirm your account!', 'warning')
    return render_template('unconfirmed.html')

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if 'user' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        iframe_code = request.form.get('iframe_code')

        # Debug print for iframe code
        print(f"Full iframe HTML code: {iframe_code}")

        # Placeholder screenshot
        screenshot_base64 = None

        project_collection = mongo.db[PROJECT_COLLECTION]
        project_id = project_collection.insert_one({
            "username": session['user'],
            "title": title,
            "description": description,
            "iframe_code": iframe_code,
            "screenshot": screenshot_base64,
            "comments": []  # Initialize an empty comments list
        }).inserted_id

        print(f"New project created with ID: {project_id}")

        flash('Project added successfully', 'success')
        return redirect(url_for('my_projects'))

    return render_template('add_project.html')

@app.route('/my_projects')
def my_projects():
    if 'user' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 5
    project_collection = mongo.db[PROJECT_COLLECTION]
    projects = list(project_collection.find({"username": session['user']}).skip((page - 1) * per_page).limit(per_page))
    total = project_collection.count_documents({"username": session['user']})

    pagination = Pagination(page=page, total=total, record_name='projects', per_page=per_page)

    # Debug print for projects
    print(f"Projects retrieved for user {session['user']}: {projects}")

    return render_template('projects.html', projects=projects, pagination=pagination)

@app.route('/all_projects')
def all_projects():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 5
    project_collection = mongo.db[PROJECT_COLLECTION]
    projects = list(project_collection.find().skip((page - 1) * per_page).limit(per_page))
    total = project_collection.count_documents({})

    pagination = Pagination(page=page, total=total, record_name='projects', per_page=per_page)

    # Debug print for all projects
    print(f"All projects retrieved: {projects}")

    return render_template('all_projects.html', projects=projects, pagination=pagination)

@app.route('/project/<project_id>', methods=['GET', 'POST'])
def project_details(project_id):
    project_collection = mongo.db[PROJECT_COLLECTION]
    project = project_collection.find_one({"_id": ObjectId(project_id)})
    
    if not project:
        flash('Project not found', 'danger')
        return redirect(url_for('my_projects'))

    if request.method == 'POST':
        if 'user' not in session:
            flash('You need to login first', 'danger')
            return redirect(url_for('login'))

        comment = request.form.get('comment')
        if comment:
            comment_data = {
                "username": session['user'],
                "comment": comment,
                "timestamp": datetime.utcnow()
            }
            project_collection.update_one({"_id": ObjectId(project_id)}, {"$push": {"comments": comment_data}})
            flash('Comment added successfully', 'success')
            return redirect(url_for('project_details', project_id=project_id))

    comments = project.get('comments', [])
    print(f"Project title: {project['title']}, iframe HTML: {project['iframe_code']}")  # Debug print for iframe code

    return render_template('project_details.html', project=project, comments=comments)

@app.route('/delete_project/<project_id>', methods=['POST'])
def delete_project(project_id):
    if 'user' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    project_collection = mongo.db[PROJECT_COLLECTION]
    project = project_collection.find_one({"_id": ObjectId(project_id)})

    if project and project['username'] == session['user']:
        project_collection.delete_one({"_id": ObjectId(project_id)})
        flash('Project deleted successfully', 'success')
    else:
        flash('You do not have permission to delete this project', 'danger')

    return redirect(url_for('my_projects'))

@app.route('/edit_project/<project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    if 'user' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    project_collection = mongo.db[PROJECT_COLLECTION]
    project = project_collection.find_one({"_id": ObjectId(project_id)})

    if not project or project['username'] != session['user']:
        flash('You do not have permission to edit this project', 'danger')
        return redirect(url_for('my_projects'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        iframe_code = request.form.get('iframe_code')

        # Debug print for iframe code
        print(f"Full iframe HTML code: {iframe_code}")

        # Placeholder screenshot
        screenshot_base64 = None

        project_collection.update_one({"_id": ObjectId(project_id)}, {"$set": {
            "title": title,
            "description": description,
            "iframe_code": iframe_code,
            "screenshot": screenshot_base64
        }})

        flash('Project updated successfully', 'success')
        return redirect(url_for('my_projects'))

    return render_template('edit_project.html', project=project)

@app.route('/add_comment/<project_id>', methods=['POST'])
def add_comment(project_id):
    if 'user' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    content = request.form.get('content')
    author = session['user']
    timestamp = datetime.now()

    comment = {
        "author": author,
        "content": content,
        "timestamp": timestamp
    }

    project_collection = mongo.db[PROJECT_COLLECTION]
    project_collection.update_one(
        {"_id": ObjectId(project_id)},
        {"$push": {"comments": comment}}
    )

    flash('Comment added successfully', 'success')
    return redirect(url_for('project_details', project_id=project_id))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
