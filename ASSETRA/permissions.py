from functools import wraps
from flask import session, redirect, url_for, flash, g
from models import Account

PERMISSIONS = {
    "superadmin": {"*"},
    "admin": {"asset:add", "asset:delete", "user:manage"},
    "user": {"asset:add"},
}

def can(role, action):
    perms = PERMISSIONS.get(role, set())
    return "*" in perms or action in perms


def current_account():
    uid = session.get("uid")
    if not uid:
        return None
    acc = Account.query.get(uid)
    return acc if acc and acc.is_active else None


def require(action=None):
    """Login required. If `action` is given, role must also be allowed to do it."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            acc = current_account()
            if not acc:
                return redirect(url_for("login"))
            if action and not can(acc.role, action):
                flash("You don't have permission to do that.", "error")
                return redirect(url_for("dashboard"))
            g.account = acc
            return fn(*args, **kwargs)
        return wrapper
    return decorator
