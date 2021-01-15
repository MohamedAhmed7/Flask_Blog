import secrets, os
from PIL  import Image
from flask_blog.models import User, Post
from flask import render_template, url_for, flash, redirect, request
from flask_blog.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flask_blog import app, db
from flask_blog import bcrypt
from flask_login import login_user, current_user, logout_user, login_required

posts = [
    {
        'author': 'michael',
        'date_posted': '8-aug-2020',
        'content':'this is my first post'
    },
    {
        'author': 'ali',
        'date_posted': '8-aug-2020',
        'content':'this is my first post'
    }
]
@app.route("/")
@app.route("/Home")
def home():
    return render_template('Home.html', posts = posts)
@app.route("/about")
def about():
    return render_template('about.html', title = 'about')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # check if user already have account
        user = User.query.filter_by(email = form.email.data).first()
        if user:
            #print(user)
            flash(f'Seems this email is already registered try to log in', 'danger')
            return redirect(url_for('login'))
        else:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(username = form.username.data, email = form.email.data, password = hashed_password)
            db.session.add(user)
            db.session.commit()
            flash(f'Your Account has been created! now you can log in ', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', title = 'Register', form= form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(url_for(f'{next_page[1:]}')) if next_page else redirect(url_for('home'))
        else:
            flash('Login Failed, Please check your mail or password', 'danger')
    return render_template('login.html', title = 'Login', form= form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/account")
@login_required
def account():
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title = 'account', image_file=image_file)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = current_user.username + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics/', picture_fn)
    #resizing the image
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/update_account", methods=['GET', "POST"])
@login_required
def update_account():
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    form = UpdateAccountForm()
    if form.validate_on_submit():
        # check if user already have account
        if form.picture.data:
            pic_path = os.path.join(app.root_path, 'static/profile_pics/', current_user.image_file)
            try:
                os.remove(pic_path)
            except:
                pass
            picture_fn = save_picture(form.picture.data)
            current_user.image_file = picture_fn
        current_user.username = form.username.data
        current_user.email    = form.email.data
        db.session.commit()
        flash(f'Your Account has been updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('update_account.html', title='update_account',
                           image_file=image_file, form = form)
