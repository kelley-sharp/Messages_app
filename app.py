from flask import Flask, request, url_for, render_template, redirect, session
from flask_modus import Modus
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired, ValidationError
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://localhost/messages_app"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt()
modus = Modus(app)
toolbar = DebugToolbarExtension(app)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    picture_url = db.Column(db.Text)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    messages = db.relationship("Message", backref="user")

    @classmethod
    def register(cls, username, password):
        """Register a user, hashing their password."""
        hashed = bcrypt.generate_password_hash(password)
        hashed_utf8 = hashed.decode("utf8")
        return cls(username=username, password=hashed_utf8)

    @classmethod
    def authenticate(cls, username, password):
        """Validate that user exists & password is correct.

        Return user if valid; else return False.
        """

        user = User.query.filter_by(username=username).first()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                return user

        return False


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.Text)
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


message_tag_table = db.Table(
    'message_tags',
    db.Column('message_id', db.Integer, db.ForeignKey('messages.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')))


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    messages = db.relationship(
        'Message',
        secondary=message_tag_table,
        # cascade="all delete",
        backref=db.backref('tags'))


db.create_all()


class addMessageForm(FlaskForm):
    def my_length_check(form, field):
        if len(field.data) > 60:
            raise ValidationError('Field must be under 60 characters long')

    name = StringField("Your Name", validators=[InputRequired()])
    content = StringField(
        "Your Message", validators=[InputRequired(), my_length_check])


@app.route("/")
def root():
    return redirect(url_for('show_users_index'))


@app.route("/users")
def show_users_index():
    users = User.query.all()
    logged_in = bool(session.get('user_id'))
    return render_template(
        "users/index.html", users=users, logged_in=logged_in)


@app.route("/users/new")
def show_add_user_form():
    return render_template("users/new.html")


@app.route("/users", methods=["POST"])
def create_user():
    if request.method == "POST":
        new_user = User.register(
            username=request.values.get('username'),
            password=request.form.get("password"))
        new_user.first_name = request.values.get('first_name'),
        new_user.last_name = request.values.get('last_name'),
        new_user.picture_url = request.values.get('profile_picture')
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('users/new.html')


@app.route('/register', methods=['GET'])
def register():
    return render_template("users/new.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Produce login form or handle login."""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.authenticate(username, password)  # <User> or False
        if user:
            session["user_id"] = user.id
            return redirect(url_for("show_users_index"))
        else:
            return "INVALID CREDENTIALS"

    return render_template("users/login.html")


@app.route('/logout', methods=['GET'])
def logout():
    del session["user_id"]
    return redirect(url_for('show_users_index'))


@app.route("/users/<int:user_id>")
def show_user(user_id):
    found_user = User.query.get(user_id)
    return render_template(
        "users/show_user.html", user=found_user, user_id=user_id)


@app.route("/users/<int:user_id>/edit")
def edit_user(user_id):
    current_user = User.query.get(session.get('user_id'))
    found_user = User.query.get(user_id)
    if found_user != current_user:
        return 'FORBIDDEN YOU CANNOT EDIT'
    return render_template("users/edit.html", user=found_user, user_id=user_id)


@app.route("/users/<int:user_id>", methods=['PATCH'])
def update_user(user_id):
    found_user = User.query.get(user_id)
    found_user.first_name = request.values.get('first_name'),
    found_user.last_name = request.values.get('last_name'),
    found_user.picture_url = request.values.get('profile_picture')
    db.session.commit()
    return render_template(
        "users/show_user.html", user_id=user_id, user=found_user)


@app.route("/users/<int:user_id>/messages")
def show_messages_index(user_id):
    found_user = User.query.get(user_id)
    return render_template("messages/index.html", user=found_user)


# @app.route("/users/messages/new")
# def show_add_message_form():
#     form = addMessageForm()
#     return render_template("messages/new.html", form=form)


@app.route("/users/<int:user_id>/messages", methods=["POST"])
def add_message(user_id):
    new_message = Message(
        author=request.values.get('name'),
        content=request.values.get('content'),
        user_id=user_id)

    db.session.add(new_message)
    db.session.commit()
    return redirect(url_for('show_messages_index', user_id=user_id))


@app.route("/users/<int:user_id>/messages/new", methods=['GET'])
def new_message_form(user_id):
    form = addMessageForm()
    found_user = User.query.get(user_id)
    if form.validate_on_submit():
        content = form.data['content']
        name = form.data['name']
        return f"{content} -{name}"
    else:
        return render_template(
            "messages/new.html", form=form, user=found_user, user_id=user_id)


@app.route(
    "/users/<int:user_id>/messages/<int:message_id>", methods=['DELETE'])
def delete_message(user_id, message_id):
    found_message = Message.query.get(message_id)
    user = found_message.user
    db.session.delete(found_message)
    db.session.commit()
    return redirect(url_for('show_messages_index', user_id=user.id))
