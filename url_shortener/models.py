from .extensions import db, login_manager, bcrypt
from datetime import datetime
import string
from random import choices
from flask_login import UserMixin

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(512))
    short_url = db.Column(db.String(5), unique=True)
    custom_url = db.Column(db.String(50), unique=True)
    visits = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime(), default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.custom_url:
            self.short_url = self.generate_short_link()

    def save(self):
        db.session.add(self)
        db.session.commit()

    # Generate the short link
    def generate_short_link(self):
        chars = string.ascii_letters + string.digits
        short_url = ''.join(choices(chars, k=5))

        link = self.query.filter_by(short_url=short_url).first()

        if link:
            return self.generate_short_link()
        
        return short_url

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    date_created = db.Column(db.DateTime(), default=datetime.now)
    links = db.relationship('Link', backref='user', lazy=True)



    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()



    # def __init__(self, username, email):
    #     self.name = name
    #     self.email = email

    # def set_password(self, password):
    #     self.password = hash_password(password)
    

    # def save(self):
    #     db.session.add(self)
    #     db.session.commit()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # def hash_password(self, password):
    #     return bcrypt.generate_password_hash(password).decode('utf-8')