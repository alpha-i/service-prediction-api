from flask import make_response, render_template, jsonify


class ApiResponse:
    def __init__(self, content_type, next=None, template=None, context=None, status_code=200):
        if content_type in ['text/html', 'application/html']:
            response = make_response()
            if template:
                response = make_response(render_template(template, context), status_code)
            if next:
                response.status_code = 302
                response.headers.add('Location', next)
            if template and next:
                response.headers.add('Refresh', 5)
        else:
            response = make_response(jsonify(context), status_code)
        self.response = response

    def __call__(self, *args, **kwargs):
        return self.response

    def set_cookie(self, key, value, expires):
        self.response.set_cookie(key, value, expires=expires)

