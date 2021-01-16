from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import  Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'f66ef9262ec1b071a797c530d5a422a5'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['MAIL_SERVER']   = 'smtp.googlemail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True

# these are credentials to gmail account
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
mail = Mail(app)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from flask_blog import routes
