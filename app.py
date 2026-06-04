from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from models.student import db, Admin
from routes.auth import auth_bp
from routes.students import students_bp
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in first.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)

    with app.app_context():
        db.create_all()
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin created: admin / admin123")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)