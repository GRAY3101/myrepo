from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

class LoginDaten(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(200), unique=False, nullable=False)
    userNach = db.Column(db.String(200), unique=False, nullable=False)
    userEmail = db.Column(db.String(400), unique=True, nullable=False)
    userPass = db.Column(db.String(30), unique=False, nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(200), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route("/", methods=['GET', 'POST'])
def admin():
    admin_email = 'admin@login.com'
    existing_admin = LoginDaten.query.filter_by(userEmail=admin_email).first()
    if not existing_admin:
        admin = LoginDaten(
            userName='ADMIN',
            userNach='ADMIN',
            userEmail=admin_email,
            userPass='0000'
        )
        db.session.add(admin)
        db.session.commit()
        daten = LoginDaten.query.order_by(LoginDaten.created_at).all()
        return render_template('reg.html', data=daten)
    elif request.method== 'POST':
        new_login = LoginDaten(
            userName=request.form['userName'],
            userNach=request.form['userNach'],
            userEmail=request.form['userEmail'],
            userPass=request.form['userPass']
        )
        
        email = LoginDaten.query.filter_by(userEmail=request.form['userEmail']).all()
        print(email)
        if not email:
            db.session.add(new_login)
            db.session.commit()
            return redirect(url_for('next', userName=request.form['userName']))
        else:
            return render_template('reg.html',emailVor=True)
    else:
        return render_template('reg.html')
        

@app.route("/anmelden", methods=['GET', 'POST'])
def weiter():
    return render_template('anmelden.html')

@app.route("/registrieren", methods=['GET', 'POST'])
def regi():
    return render_template('reg.html')

@app.route('/check', methods=['GET', 'POST'])
def check():
    if request.method == 'POST':
        input_userEmail = request.form.get('userEmail')
        input_passwort = request.form.get('userPass')
        user = LoginDaten.query.filter_by(userEmail=input_userEmail, userPass=input_passwort).first()
        if not input_userEmail == "":
            if user:
                return redirect(url_for('next', userName=user.userName))
            else:
                return render_template('anmelden.html', falsch=True)
        else:
            return render_template('anmelden.html', falsch=True)
    else:
        return "Method not allowed"

@app.route("/chat", methods=['GET', 'POST'])
def next():
    userName = request.args.get('userName', '')
    if request.method == 'POST':
        new_message = Message(
            user=userName,
            content=request.form['content']
        )
        db.session.add(new_message)
        db.session.commit()
    messages = Message.query.order_by(Message.created_at).all()
    return render_template('index.html', nachricht=messages, name=userName)

@socketio.on('send_message')
def handle_send_message_event(data):
    userName = data['userName']
    content = data['content']
    new_message = Message(user=userName, content=content)
    db.session.add(new_message)
    db.session.commit()
    emit('receive_message', {'userName': userName, 'content': content}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
