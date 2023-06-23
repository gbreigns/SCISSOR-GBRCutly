from flask import Blueprint, render_template, url_for, request, redirect, flash, current_app
from flask_login import login_required, current_user, login_user, logout_user
from datetime import datetime

from .models import Link, User
from .extensions import db, bcrypt
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import validators
from .forms import QRCodeData, SignupForm, LoginForm
import secrets
import qrcode
import os



limiter = Limiter(get_remote_address)
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})


short = Blueprint('short', __name__)

@short.route('/<short_url>')
@cache.cached(timeout=45)
def redirect_to_url(short_url):
    link = Link.query.filter_by(custom_url=short_url).first()
    if not link:
        # If it doesn't, check if it matches a short URL
        link = Link.query.filter_by(short_url=short_url).first_or_404()

    link.visits = link.visits + 1   
    db.session.commit()

    return redirect(link.original_url)


@short.route('/')
def index():
    return render_template('index.html')


@short.route('/add_link', methods=['POST'])
@login_required
@limiter.limit("10/minutes")
def add_link():
    original_url = request.form['long-url']
    custom_url = request.form['custom-url']

    # Add a default scheme if the URL doesn't have one {turns www.google.com to https://www.google.com}
    if not original_url.startswith(('http://', 'https://')):
        original_url = 'https://' + original_url

    # validate the long url
    if not validators.url(original_url):
        return render_template('index.html', invalid=True)

    # check if the custom url is already in use in the database
    if custom_url:
        existing_link = Link.query.filter_by(custom_url=custom_url).first()
        # if it is found in the database, return the custom url
        if existing_link:
            return render_template('link_added.html', custom_url_exists=True, new_link=existing_link.custom_url, original_url=existing_link.original_url)
        # if it isn't found in the database, add it to the Link object
        else:
            link = Link(original_url=original_url, custom_url=custom_url)
            link.save()
            return render_template('link_added.html', new_link=link.custom_url, original_url=link.original_url)
        
    # check if the original_url is already in the database and does not have a custom url
    short_link = Link.query.filter_by(original_url=original_url, custom_url=None).first()

    # if it is, return the existing short url
    if short_link:
        return render_template('link_added.html', new_link=short_link.short_url, original_url=short_link.original_url)
    
    # if it isn't, create a new Link object, save it, and return the new short url
    else:
        link = Link(original_url=original_url)
        link.save()
        return render_template('link_added.html', new_link=link.short_url, original_url=link.original_url)

    

    return ''


@short.route('/stats')
@login_required
@cache.cached(timeout=60)
def stats():
    links = Link.query.all()

    return render_template('stats.html', links=links)


@short.app_errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404


@short.route("/signup", methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_pword = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, email=form.email.data, password_hash=hashed_pword)
        user.save()
        flash('Account has been created successfully!', 'success')
        return redirect(url_for('short.login'))
    return render_template('signup.html', title='SignUp', form=form)


@short.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            return render_template('index.html')
        else:
            flash('Login Unsuccessful, please check that email and password are correct.', 'error')
    return render_template('login.html', title='Login', form=form)



@short.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('short.index'))

@short.route("/generate_qrcode", methods=["GET", "POST"])
@login_required
def generate_qrcode():
    form = QRCodeData()
    if request.method == "POST":
        if form.validate_on_submit():
            data = form.data.data
            image_name = f"{secrets.token_hex(10)}.png"
            # qrcode_location = f"{app.config['UPLOADED_PATH']}/{image_name}"

            try:
                my_qrcode = qrcode.make(str(data))
                my_qrcode.save('static/image_name')
            except Exception as e:
                print(e)

        return render_template("generated_qrcode.html", title="Generated", image=image_name)

    else:
        return render_template("generate_qrcode.html", title="Generate", form=form)