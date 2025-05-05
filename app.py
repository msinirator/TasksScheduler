from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import os


app = Flask(__name__)

# Get the directory of the current file
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

dbPath = 'sqlite:///' + os.path.join(basedir, 'database.db')
engine = create_engine(dbPath)
                       
db = SQLAlchemy(app)


class Task_db(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    dueDate = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<Task {self.name}>'

class User_db(db.Model):
    __tablename__ = 'users'
    userID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userName = db.Column(db.String(20), nullable=False)
    userPass = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<User {self.userName}>'
    

class Task:

    def __init__(self,name,status,dueDate):
        self.name = name
        self.status = status
        self.dueDate = dueDate


# app = Flask(__name__)
# tasks = []


@app.route('/')
def home():
    return render_template('login.html')
    # return render_template('index.html', tasks = tasks)

@app.route('/signIn')
def signIn():

    userName = request.args['userName']
    userPass = request.args['userPass']
    
    stmt = select(User_db).where(User_db.userName == userName).where(User_db.userPass == userPass)
    # query = db.session.query('select * from users Where userName = ' + userName)

    session = Session(engine)
    results = session.execute(stmt)

    # for result in results:
    #     print(result.User.userPass)
    

    if results.first():
        tasks = Task_db.query.all()
        return render_template('tasks.html', tasks = tasks, taskCount = len(tasks))
    else:
        return render_template('login.html', message = "Login failed")
    

@app.route('/signUp', methods=['POST'])
def signUp():
    userName = request.form['userName']
    userPass = request.form['userPass']

    new_user = User_db(userName=userName,userPass=userPass)
    db.session.add(new_user)
    db.session.commit()
    return render_template('login.html', message = "Registration Succesfull")


@app.route('/add', methods=['POST'])
def add_task():

    taskName = request.form['taskName']
    taskDueDate = request.form['taskDueDate']

    new_task = Task_db(name=taskName, dueDate=taskDueDate, status="Pending")
    db.session.add(new_task)
    db.session.commit()

    tasks = Task_db.query.all()
    return render_template('tasks.html', tasks = tasks, taskCount = len(tasks))


    # taskName = request.form['taskName']
    # taskDueDate = request.form['taskDueDate']

    # myTask = Task(taskName, "pending", taskDueDate)
    # tasks.append(myTask)

    # return render_template('index.html', tasks = tasks)


@app.route('/delete/<int:task_id>')
def delete_task(task_id):

    task = Task_db.query.get(task_id)
    db.session.delete(task)
    db.session.commit()

    tasks = Task_db.query.all()
    return render_template('tasks.html', tasks = tasks, taskCount = len(tasks))

    # if 0 <= task_id < len(tasks):
    #     tasks.pop(task_id)

    # return render_template('index.html', tasks = tasks)


@app.route('/edit/<int:task_id>', methods=['GET','POST'])
def edit_task(task_id):

    task = Task_db.query.get(task_id)

    if request.method == 'POST':

        task.name = request.form['taskName']
        db.session.commit()

        tasks = Task_db.query.all()
        return render_template('tasks.html', tasks = tasks, taskCount = len(tasks))

    return render_template('edit.html', task = task)


@app.route('/complete/<int:task_id>')
def complete_task(task_id):

    task = Task_db.query.get(task_id)
    task.status = "Completed"

    db.session.commit()

    tasks = Task_db.query.all()
    return render_template('tasks.html', tasks = tasks, taskCount = len(tasks))


    # myTask = tasks[task_id]
    # myTask.status = "Completed"

    # return render_template('index.html', tasks = tasks)


@app.route('/clearAll', methods=['POST'])
def clearTasks():
    
    tasks = Task_db.query.all()

    for task in tasks:
        db.session.delete(task)

    db.session.commit()

    tasks = Task_db.query.all()
    return render_template('tasks.html', tasks = tasks, taskCount = len(tasks))



if __name__ == '__main__':
    app.run(debug = True)



