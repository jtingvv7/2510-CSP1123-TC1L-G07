from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def restrict_banned(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_banned:
            flash("Your account has been banned. You can only view pages.", "error")
            return redirect(url_for("index"))  # redirect to home or read-only page
        return f(*args, **kwargs)
    return decorated_function