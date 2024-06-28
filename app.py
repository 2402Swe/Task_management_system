from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = b'525htgrd3ss'

# MongoDB configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URI)
db = client.todo_database
users_collection = db.users
tasks_collection = db.tasks

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        return User(str(user['_id']), user['username'], user['email'], user['password'])
    return None

@app.route('/')
@login_required
def index():
    tasks = tasks_collection.find({"user_id": current_user.id})
    return render_template('index.html', tasks=tasks)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        users_collection.insert_one({'username': username, 'email': email, 'password': password})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            user_obj = User(str(user['_id']), user['username'], user['email'], user['password'])
            login_user(user_obj)
            return redirect(url_for('index'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        new_task = {'title': title, 'description': description, 'completed': False, 'user_id': current_user.id}
        tasks_collection.insert_one(new_task)
        return redirect(url_for('index'))
    return render_template('add_task.html')

@app.route('/edit/<task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = tasks_collection.find_one({'_id': ObjectId(task_id), 'user_id': current_user.id})
    if request.method == 'POST':
        updated_task = {
            'title': request.form['title'],
            'description': request.form['description'],
            'completed': 'completed' in request.form
        }
        tasks_collection.update_one({'_id': ObjectId(task_id)}, {'$set': updated_task})
        return redirect(url_for('index'))
    return render_template('edit_task.html', task=task)

@app.route('/delete/<task_id>')
@login_required
def delete_task(task_id):
    tasks_collection.delete_one({'_id': ObjectId(task_id), 'user_id': current_user.id})
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
