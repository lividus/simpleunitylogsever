from http.server import BaseHTTPRequestHandler
from urllib import parse

def set_class_attr(cls, attrname, value):
    if not hasattr(cls, attrname):
        setattr(cls, attrname, value)


def request(cls):
    setattr(cls, '_get_rule_cache', {})
    setattr(cls, '_post_rule_cache', {})
    setattr(cls, '_post_rule_cache', {})
    for name, method in cls.__dict__.items():
        if hasattr(method, "_rule_cache"):
            atr = getattr(method, "_rule_cache")
            rules = atr[name]
            for rule in rules:
                path = rule[1]['path']
                if rule[0] is 'get':
                    cls._get_rule_cache[path] = method
                elif rule[0] is 'post':
                    cls._post_rule_cache[path] = method
                elif rule[0] is 'put':
                    cls._put_rule_cache[path] = method

    return cls


def route(rule, **options):
    """A decorator that is used to define custom routes for methods in
    FlaskView subclasses. The format is exactly the same as Flask's
    `@app.route` decorator.
    """

    def decorator(f):
        # Put the rule cache on the method itself instead of globally
        if not hasattr(f, '_rule_cache') or f._rule_cache is None:
            f._rule_cache = {f.__name__: [(rule, options)]}
        elif not f.__name__ in f._rule_cache:
            f._rule_cache[f.__name__] = [(rule, options)]
        else:
            f._rule_cache[f.__name__].append((rule, options))

        return f

    return decorator


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _set_json_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json;charset=UTF-8')
        self.end_headers()

    def _set_400_response(self):
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("400 error. Wrong path: '{}'".format(self.path).encode('utf-8'))

    def get_clear_path(self):
        result = self.path
        self.request_parameters = {}
        if result == '/':
            return result
        qpos = result.find('?')
        if qpos >= 0:
            params = result[qpos+1:]
            result = result[:qpos]
            self.request_parameters = parse.parse_qs(params)
        if result[-1] == "/":
            result = result[:-1]
        return result

    def do_GET(self):
        process_func = self._get_rule_cache.get(self.get_clear_path(), None)
        if process_func is not None:
            process_func(self)
        else:
            self._set_400_response()

    def do_POST(self):
        process_func = self._post_rule_cache.get(self.get_clear_path(), None)
        if process_func is not None:
            process_func(self)
        else:
            self._set_400_response()