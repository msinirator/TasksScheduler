from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import os
import json


#AWS bucket
import boto3
# import logging


# logging.basicConfig(filename='app.log',level=logging.INFO)

#AWS bucket
bucketName = "taskscheduler-bucket"

#AWS Secret
def get_db_secret(secret_name, region_name='us-east-2'):
    client = boto3.client('secretmanager', region_name=region_name)
    response = client.get_secret_value(SecredId=secret_name)

    secret = response['SecretString']
    return json.loads(secret)

#AWS secret
#Fetch credentials from secrets manager
secret = get_db_secret('prod/rds/mydb')


app = Flask(__name__)

# Get the directory of the current file
basedir = os.path.abspath(os.path.dirname(__file__))

#AWS secret
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{secret['username']}:{secret['password']}@{secret['host']}/{secret['dbName']}"
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


#AWS secret
dbPath = f"mysql+pymysql://{secret['username']}:{secret['password']}@{secret['host']}/{secret['dbName']}"
# dbPath = 'sqlite:///' + os.path.join(basedir, 'database.db')
engine = create_engine(dbPath)
                       
db = SQLAlchemy(app)





#AWS bucket
def upload_to_s3(file_path, s3_key):

    s3 = boto3.client('s3')
    
    try:
        s3.upload_file(file_path, bucketName, s3_key)
        print(f"File {file_path} uploaded to S3 bucket {bucketName} with key {s3_key}")
        # logging.info(f"File {file_path} uploaded to S3 bucket {bucketName} with key {s3_key}")
        return f"https://{bucketName}.s3.amazonaws.com/{s3_key}"

    except Exception as e:
        print(e)
        # logging.error(f"Error uploading file to S3: {e}")


class Task_db(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    dueDate = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    attach_url = db.Column(db.String(20), nullable=False)
    attach_name = db.Column(db.String(20), nullable=False)

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


@app.before_request
def create_tables():
    db.create_all()

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

    #AWS bucket
    file = request.files['fileName']
    
    attach_url = ""
    attach_name = ""

    if file:
        # logging.info(f"Received file: {file}")
        print((f"Received file: {file}"))
        attach_name = file.filename

        file_path = os.path.join(basedir, file.filename)
        file.save(file_path)
        
        attach_url = upload_to_s3(file_path, file.filename)
        os.remove(file_path)
    else:
        print("No file received")
        # logging.info("No file received")


    taskName = request.form['taskName']
    taskDueDate = request.form['taskDueDate']

    new_task = Task_db(name=taskName, dueDate=taskDueDate, status="Pending", attach_url=attach_url, attach_name=attach_name)
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
    app.run(host='0.0.0.0', debug=True)
    # app.run(debug = True)



