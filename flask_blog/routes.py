import secrets, os
from PIL  import Image
from flask_blog.models import User, Post, Replies
from flask import render_template, url_for, flash, redirect, request, abort
from flask_blog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, Reply
from flask_blog import app, db
from flask_blog import bcrypt
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
@app.route("/Home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page, per_page=5)
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
    user = current_user
    posts = Post.query.filter_by(author=user) \
        .order_by(Post.date_posted.desc()) \
        .paginate(per_page=5)
    return render_template('account.html', title = 'account', image_file=image_file, posts = posts)


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

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()

    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author = current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your Post have been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form = form, legend='New Post')

@app.route("/post/<int:post_id>", methods=['GET','POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    replies = post.replies
    num_of_rep = len(replies)

    form = Reply()
    if form.validate_on_submit():
        flash('Log in First to reply to this post', 'danger')
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        reply = Replies(post_id = post_id, user_id = current_user.id, content = form.content.data)
        db.session.add(reply)
        db.session.commit()
        flash('Your replied to this post!', 'success')
        return redirect(url_for('post', post_id=post.id))
    return render_template('post.html', title=post.title,
                               post=post, replies=replies, n=num_of_rep, form=form)
@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your Post have been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='update Post', form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete" , methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your Post have been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username = username).first_or_404()
    posts = Post.query.filter_by(author = user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page, per_page=5)
    return render_template('user_posts.html', posts = posts, user=user)