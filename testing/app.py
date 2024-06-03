from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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
        username = request.form.get('username')
        email = request.form.get('email')
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
            "password": hashed_password
        })

        session['user'] = username
        flash('Account created successfully', 'success')
        return redirect(url_for('my_projects'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user_collection = mongo.db[USER_COLLECTION]
        user = user_collection.find_one({"email": email})

        if user and bcrypt.check_password_hash(user['password'], password):
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

def take_screenshot(iframe_code):
    # Create a temporary HTML file with the iframe
    with open('temp.html', 'w') as f:
        f.write(f"<html><body>{iframe_code}</body></html>")

    # Set up Selenium to use Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get('file://' + os.path.abspath('temp.html'))
    
    # Wait for the iframe to load completely
    try:
        # Switch to the iframe
        driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))
        # Wait for a specific element within the iframe to be visible
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, "body"))
        )
        # Switch back to the default content
        driver.switch_to.default_content()
    except Exception as e:
        print(f"Error waiting for iframe to load: {e}")
    
    # Take screenshot
    screenshot = driver.get_screenshot_as_png()
    
    # Close the driver
    driver.quit()
    
    # Remove the temporary file
    os.remove('temp.html')
    
    return screenshot

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

        screenshot = take_screenshot(iframe_code)
        screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')

        project_collection = mongo.db[PROJECT_COLLECTION]
        project_id = project_collection.insert_one({
            "username": session['user'],
            "title": title,
            "description": description,
            "iframe_code": iframe_code,
            "screenshot": screenshot_base64
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

    project_collection = mongo.db[PROJECT_COLLECTION]
    projects = list(project_collection.find({"username": session['user']}))

    # Debug print for projects
    print(f"Projects retrieved for user {session['user']}: {projects}")

    return render_template('projects.html', projects=projects)

@app.route('/all_projects')
def all_projects():
    project_collection = mongo.db[PROJECT_COLLECTION]
    projects = list(project_collection.find())

    # Debug print for all projects
    print(f"All projects retrieved: {projects}")

    return render_template('all_projects.html', projects=projects)

@app.route('/project/<project_id>')
def project_details(project_id):
    print(f"Fetching project details for project_id: {project_id}")  # Debug statement
    project_collection = mongo.db[PROJECT_COLLECTION]
    project = project_collection.find_one({"_id": ObjectId(project_id)})
    
    if not project:
        flash('Project not found', 'danger')
        return redirect(url_for('my_projects'))

    print(f"Project title: {project['title']}, iframe HTML: {project['iframe_code']}")  # Debug print for iframe code

    return render_template('project_details.html', project=project)

if __name__ == '__main__':
    app.run(debug=True)
