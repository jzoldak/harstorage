class AuthMiddleware(object):
    """
    Basic authentication middleware for the entire application,
    following the baseline recommended practice at
    http://wsgi.readthedocs.org/en/latest/specifications/simple_authentication.html
    """
    def __init__(self, app, config, realm='site'):
        self.app = app
        self.config = config
        self.realm = realm

    def __call__(self, environ, start_response):
        def repl_start_response(status, headers, exc_info=None):
            if status.startswith('401'):
                remove_header(headers, 'WWW-Authenticate')
                headers.append(('WWW-Authenticate',
                    'Basic realm="{}"'.format(self.realm)
                    )
                )
            return start_response(status, headers)

        auth = environ.get('HTTP_AUTHORIZATION')

        if auth:
            scheme, data = auth.split(None, 1)
            assert scheme.lower() == 'basic'
            username, password = data.decode('base64').split(':', 1)

            if not self.check_password(username, password):
                return self.authenticate(environ, start_response)
            environ['REMOTE_USER'] = username
            del environ['HTTP_AUTHORIZATION']

            return self.app(environ, repl_start_response)

        return self.authenticate(environ, repl_start_response)

    def authenticate(self, environ, start_response):
        body = 'Please authenticate'
        headers = [
            ('content-type', 'text/plain'),
            ('content-length', str(len(body))),
            ('WWW-Authenticate', 'Basic realm="{}"'.format(self.realm))]
        start_response('401 Unauthorized', headers)
        return [body]

    def check_password(self, username, password):
        return username == self.config["app_conf"]["auth_user"] and password == self.config["app_conf"]["auth_pswd"]

def remove_header(headers, name):
    for header in headers:
        if header[0].lower() == name.lower():
            headers.remove(header)
            break
