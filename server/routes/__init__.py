from .admin_routes import admin_bp
from .auth_routes import auth_bp
from .student_routes import student_bp
from .teacher_routes import teacher_bp

def register_routes(app):
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)