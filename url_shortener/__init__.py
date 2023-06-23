from flask import Flask
from .extensions import db, bcrypt, login_manager, migrate
from .routes import cache, limiter
from .routes import short
from .models import User, Link
import os

from dotenv import load_dotenv



load_dotenv()
login_manager.login_view = 'short.login'


base_dir = os.path.dirname(os.path.realpath(__file__))


def create_app(config_file='settings.py'):
    app = Flask(__name__)
    
    app.config.from_pyfile(config_file)

  
    app.config.update(UPLOADED_PATH=os.path.join(base_dir, 'static'))



    db.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)



    app.config['SECRET_KEY'] = os.environ.get("APP_SECRET")


    app.register_blueprint(short)

    app.config['CACHE_DEFAULT_TIMEOUT'] = 300


    
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': User,
            'Link': Link
        
        }

    return app

from . import routes

