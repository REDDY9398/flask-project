from flask import Flask, redirect, render_template, request, session, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash  # Added for hashing

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Add secret key for sessions

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///project.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Routes
@app.route('/')
def home():
    return render_template('decoration.html')

@app.route('/home', methods=['GET', 'POST'])
def register():
    message = ""

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            message = "❌ Passwords do not match"
        else:
            hashed_password = generate_password_hash(password)  # Hash password
            user = User(username=username, email=email, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            message = "✅ Registered Successfully"

    return render_template('index.html', message=message)

@app.route('/manager', methods=['GET','POST'])
def manager():
    users = []
    message = ""

    if request.method == 'POST':
        key = request.form['key']

        if key == "1234":
            session['is_manager'] = True
            users = User.query.all()
            message = "✅ Manager access granted"
        else:
            session.pop('is_manager', None)
            message = "❌ Wrong Key"

    elif session.get('is_manager'):
        users = User.query.all()

    return render_template('manager.html', users=users, message=message)

@app.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('is_manager'):
        abort(403)

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect('/manager')

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):  # Check hashed password
            session['user_id'] = user.id
            return redirect('/dashboard')
        else:
            message = "❌ Invalid Login"

    return render_template('login.html', message=message)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    tasks_data = [
        {
            'id': task.id,
            'title': task.title,
            'category': task.category,
            'priority': task.priority,
            'due_date': task.due_date,
            'status': task.status,
        }
        for task in tasks
    ]
    return render_template('dashboard.html', tasks=tasks, tasks_json=tasks_data)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    category = db.Column(db.String(100))
    priority = db.Column(db.String(50))
    due_date = db.Column(db.String(50))
    status = db.Column(db.String(50), default="Active")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/add-task', methods=['POST'])
def add_task():
    title = request.form['title']
    category = request.form['category']
    priority = request.form['priority']
    due_date = request.form['due_date']

    task = Task(title=title, category=category, priority=priority, due_date=due_date, user_id=session['user_id'])

    db.session.add(task)
    db.session.commit()

    return redirect('/dashboard')

@app.route('/forgot', methods=['GET', 'POST', 'PATCH'])
def forgot():
    message = ""

    if request.method == 'PATCH':
        data = request.get_json() or {}
        email = data.get('email', '')
        new_password = data.get('new_password', '')
        confirm = data.get('confirm', '')

        user = User.query.filter_by(email=email).first()

        if not user:
            return {'status': 'error', 'message': '❌ Email not found'}, 404
        elif new_password != confirm:
            return {'status': 'error', 'message': '❌ Passwords do not match'}, 400

        user.password = generate_password_hash(new_password)
        db.session.commit()
        return {'status': 'success', 'message': '✅ Password Updated Successfully'}

    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        confirm = request.form['confirm']

        user = User.query.filter_by(email=email).first()

        if not user:
            message = "❌ Email not found"
        elif new_password != confirm:
            message = "❌ Passwords do not match"
        else:
            hashed_password = generate_password_hash(new_password)  # Hash new password
            user.password = hashed_password
            db.session.commit()
            message = "✅ Password Updated Successfully"

    return render_template('forgot.html', message=message)

# Run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # creates DB + table

    app.run(debug=True, port=5000)