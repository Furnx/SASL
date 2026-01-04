from flask import Flask
from middleware.header_type import WSGIHeader


class WSGILogging:
    def __init__(self, app: Flask):
        self.app = app

    def __call__(self, environ, start_response):
        #env = WSGIHeader(environ)
        response = self.app(environ, start_response)

        return response
