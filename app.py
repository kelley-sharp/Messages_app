from flask import Flask, request, url_for, render_template, redirect
from flask_modus import Modus
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
import psycopg2

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://localhost/messages_app"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

db = SQLAlchemy(app)
modus = Modus(app)
toolbar = DebugToolbarExtension(app)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    picture_url = db.Column(db.Text)
    messages = db.relationship("Message", backref="user")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# class Tag(db.Model):
#     __tablename__ = "tags"

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.Text, unique=True)
#     messages = db.relationship(
#         'Message',
#         secondary=message_tag_table,
#         cascade="all delete",
#         backref=db.backref('tags'))

db.create_all()


@app.route("/")
def root():
    return redirect(url_for('show_users_index'))


@app.route("/users")
def show_users_index():
    users = User.query.all()
    return render_template("users/index.html", users=users)


@app.route("/users/new")
def show_add_user_form():
    return render_template("users/new.html")


@app.route("/users", methods=["POST"])
def create_user():
    new_user = User(
        first_name=request.values.get('first_name'),
        last_name=request.values.get('last_name'),
        picture_url=request.values.get('profile_picture'))

    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('show_users_index'))


@app.route("/users/<int:user_id>")
def show_user(user_id):
    found_user = User.query.get(user_id)
    return render_template("users/show_user.html", user=found_user)


@app.route("/users/<int:user_id>/messages")
def show_messages_index(user_id):
    found_user = User.query.get(user_id)
    return render_template('messages/index.html', user=found_user)