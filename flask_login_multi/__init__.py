"""
created  by  hzwlxy  at 2018/7/5 13:53
__author__: 西瓜哥
__QQ__ : 120235331
__Note__：
"""
from werkzeug.local import LocalProxy
from functools import wraps
from flask import (session, current_app, request, has_request_context,_request_ctx_stack)

from flask_login.signals import user_logged_in, user_login_confirmed, user_logged_out
from flask_login.config import COOKIE_NAME, EXEMPT_METHODS

current_user = LocalProxy(lambda: _get_user())



def _get_endpoint():
    endpoint = request.endpoint
    try:
        return endpoint.split('.')[0]
    except Exception as e:
        return 'user'


def login_user(user, remember=False, duration=None, force=False, fresh=True):
    if not force and not user.is_active:
        return False

    user_id = getattr(user, current_app.login_manager.id_attribute)()
    session[_get_endpoint() + '_user_id'] = user_id
    session[_get_endpoint() + '_fresh'] = fresh
    # 存放浏览器和ip加密信息
    session[_get_endpoint() + '_id'] = current_app.login_manager._session_identifier_generator()
    if remember:
        session[_get_endpoint() + '_remember'] = 'set'
        if duration is not None:
            try:
                session[_get_endpoint() + '_remember_seconds'] = (duration.microseconds +
                                                                  (duration.seconds +
                                                                   duration.days * 24 * 3600) *
                                                                  10 ** 6) / 10.0 ** 6
            except AttributeError:
                raise Exception('duration must be a datetime.timedelta, '
                                'instead got: {0}'.format(duration))

    setattr(_request_ctx_stack.top, _get_endpoint(), user)
    user_logged_in.send(current_app._get_current_object(), user=_get_user())

    return True


def _get_user():
    if has_request_context() and not hasattr(_request_ctx_stack.top, _get_endpoint()):
        current_app.login_manager._load_user()
    return getattr(_request_ctx_stack.top, _get_endpoint(), None)


def logout_user():
    user = _get_user()
    if (_get_endpoint() + '_id') in session:
        session.pop(_get_endpoint() + '_id')

    if (_get_endpoint() + '_user_id') in session:
        session.pop(_get_endpoint() + '_user_id')

    if (_get_endpoint() + '_fresh') in session:
        session.pop(_get_endpoint() + '_fresh')

    cookie_name =_get_endpoint() + '_' +current_app.config.get('REMEMBER_COOKIE_NAME', COOKIE_NAME)
    if cookie_name in request.cookies:
        session[_get_endpoint() + '_remember'] = 'clear'
        if (_get_endpoint() + '_remember_seconds') in session:
            session.pop(_get_endpoint() + '_remember_seconds')
    user_logged_out.send(current_app._get_current_object(), user=user)

    current_app.login_manager.reload_user()

    return True


def confirm_login():
    session[_get_endpoint() + '_fresh'] = True
    session[_get_endpoint() + '_id'] = current_app.login_manager._session_identifier_generator()
    user_login_confirmed.send(current_app._get_current_object())

def login_fresh():
    return session.get(_get_endpoint() + '_fresh', False)

def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in EXEMPT_METHODS:
            return func(*args, **kwargs)
        elif current_app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        return func(*args, **kwargs)

    return decorated_view

def _user_context_processor():
    return dict(current_user=_get_user())