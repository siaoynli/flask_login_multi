"""
created  by  hzwlxy  at 2018/7/5 10:59
__author__: 西瓜哥
__QQ__ : 120235331
__Note__： 
"""
from datetime import datetime, timedelta
from flask import (session, _request_ctx_stack, request, current_app)
from flask_login import LoginManager as  _loginManager

from flask_login.signals import user_accessed, session_protected, user_loaded_from_cookie
from flask_login.config import COOKIE_NAME, AUTH_HEADER_NAME, COOKIE_DURATION, COOKIE_SECURE, COOKIE_HTTPONLY
from flask_login.utils import decode_cookie, encode_cookie

from flask_login_multi import _get_user

SESSION_KEYS = set(['user_id', 'remember', 'id', 'fresh', 'next'])


class LoginManager(_loginManager):

    @property
    def _get_endpoint(self):
        endpoint = request.endpoint
        try:
            return endpoint.split('.')[0]
        except Exception as e:
            return 'user'

    def reload_user(self, user=None):
        ctx = _request_ctx_stack.top
        if user is None:
            user_id = session.get(self._get_endpoint + '_user_id')
            if user_id is None:
                setattr(ctx, self._get_endpoint, self.anonymous_user())
            else:
                if self.user_callback is None:
                    raise Exception(
                        "No user_loader has been installed for this "
                        "LoginManager. Refer to"
                        "https://flask-login.readthedocs.io/"
                        "en/latest/#how-it-works for more info.")
                # 根据endpoint来判断当前登录是用户还是管理员
                user = self.user_callback(user_id, self._get_endpoint)
                if user is None:
                    setattr(ctx, self._get_endpoint, self.anonymous_user())
                else:
                    setattr(ctx, self._get_endpoint, user)
        else:
            setattr(ctx, self._get_endpoint, user)

    def _load_user(self):
        user_accessed.send(current_app._get_current_object())
        config = current_app.config

        if config.get('SESSION_PROTECTION', self.session_protection):
            deleted = self._session_protection()
            if deleted:
                return self.reload_user()

        is_missing_user_id = (self._get_endpoint + '_user_id') not in session
        if is_missing_user_id:
            cookie_name = self._get_endpoint + '_' + config.get('REMEMBER_COOKIE_NAME', COOKIE_NAME)
            header_name = config.get('AUTH_HEADER_NAME', AUTH_HEADER_NAME)
            has_cookie = (cookie_name in request.cookies and
                          session.get('remember') != 'clear')

            if has_cookie:
                return self._load_from_cookie(request.cookies[cookie_name])
            elif self.request_callback:
                return self._load_from_request(request)
            elif header_name in request.headers:
                return self._load_from_header(request.headers[header_name])

        return self.reload_user()

    def _get_session_protection(self):
        app = current_app._get_current_object()
        return app.config.get('SESSION_PROTECTION', self.session_protection)

    def _session_protection(self):
        sess = session._get_current_object()
        ident = self._session_identifier_generator()
        app = current_app._get_current_object()
        mode = app.config.get('SESSION_PROTECTION', self.session_protection)

        # 用了endpoint区别之后，不能直接 用sess来判断session有没有值
        # 用sess.get(self._get_endpoint + '_user_id',None) 来判断当前用户session标志存不存在
        if sess.get(self._get_endpoint + '_user_id', None) and ident != sess.get(self._get_endpoint + '_id', None):
            if mode == 'basic' or sess.permanent:
                sess[self._get_endpoint + '_fresh'] = False
                session_protected.send(app)
                return False
            elif mode == 'strong':

                for k in SESSION_KEYS:
                    sess.pop(self._get_endpoint + '_' + k, None)
                sess[self._get_endpoint + '_remember'] = 'clear'
                session_protected.send(app)
                return True
        return False

    def _load_from_cookie(self, cookie):
        data = decode_cookie(cookie).split('||')
        user_id = data[0]
        mode = current_app._get_current_object().config.get('SESSION_PROTECTION', self.session_protection)
        if user_id is not None:
            session[self._get_endpoint + '_user_id'] = user_id
            session[self._get_endpoint + '_fresh'] = False
            if mode == 'strong':
                session[self._get_endpoint + '_id'] = data[1]

        self.reload_user()
        user = getattr(_request_ctx_stack.top, self._get_endpoint, None)

        if user is not None:
            app = current_app._get_current_object()
            user_loaded_from_cookie.send(app, user=_get_user())

    def _update_remember_cookie(self, response):

        if (self._get_endpoint + '_remember') not in session and current_app.config.get('REMEMBER_COOKIE_REFRESH_EACH_REQUEST'):
            session[self._get_endpoint + '_remember'] = 'set'

        if (self._get_endpoint + '_remember') in session:
            operation = session.pop((self._get_endpoint + '_remember'), None)

            if operation == 'set' and (self._get_endpoint + '_user_id') in session:
                self._set_cookie(response)
            elif operation == 'clear':
                self._clear_cookie(response)

        return response

    def _set_cookie(self, response):

        config = current_app.config
        cookie_name = self._get_endpoint + '_' + config.get('REMEMBER_COOKIE_NAME', COOKIE_NAME)
        domain = config.get('REMEMBER_COOKIE_DOMAIN')
        path = config.get('REMEMBER_COOKIE_PATH', '/')
        secure = config.get('REMEMBER_COOKIE_SECURE', COOKIE_SECURE)
        httponly = config.get('REMEMBER_COOKIE_HTTPONLY', COOKIE_HTTPONLY)

        if (self._get_endpoint + '_remember_seconds') in session:
            duration = timedelta(seconds=session[self._get_endpoint + '_remember_seconds'])
        else:
            duration = config.get('REMEMBER_COOKIE_DURATION', COOKIE_DURATION)

        # 用户id 和 浏览器加密信息 存入cookie
        temp = (str(session[self._get_endpoint + '_user_id']), str(session[self._get_endpoint + '_id']))
        data = encode_cookie('||'.join(temp))

        if isinstance(duration, int):
            duration = timedelta(seconds=duration)

        try:
            expires = datetime.utcnow() + duration
        except TypeError:
            raise Exception('REMEMBER_COOKIE_DURATION must be a ' +
                            'datetime.timedelta, instead got: {0}'.format(
                                duration))

        response.set_cookie(cookie_name,
                            value=data,
                            expires=expires,
                            domain=domain,
                            path=path,
                            secure=secure,
                            httponly=httponly)

    def _clear_cookie(self, response):
        config = current_app.config
        cookie_name = self._get_endpoint + '_' + config.get('REMEMBER_COOKIE_NAME', COOKIE_NAME)
        domain = config.get('REMEMBER_COOKIE_DOMAIN')
        path = config.get('REMEMBER_COOKIE_PATH', '/')
        response.delete_cookie(cookie_name, domain=domain, path=path)
