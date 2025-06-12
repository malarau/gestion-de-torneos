"""
Authentication loaders for Flask-Login
"""

from flaskapp import login_manager
from flaskapp.database.models import User


@login_manager.user_loader
def user_loader(id):
    """Load user by ID for Flask-Login."""
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    """Load user from request for Flask-Login."""
    username = request.form.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        return user if user else None
    return None