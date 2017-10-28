import os
from sikorka.api.encoding import HexAddressConverter
from sikorka.api.resources import (
    create_blueprint,
    AddressResource,
    DetectorSignResource
)
from werkzeug.exceptions import NotFound
from flask import Flask, send_from_directory
from flask_restful import Api
from flask_cors import CORS
from gevent.wsgi import WSGIServer

from ethereum import slogging
log = slogging.get_logger(__name__)


class APIServer(object):
    """
    Runs the sikorka API server
    """

    # flask TypeConverter
    # links argument-placeholder in route (e.g. '/<hexaddress: channel_address>') to the Converter
    _type_converter_mapping = {
        'hexaddress': HexAddressConverter
    }
    _api_prefix = '/api/1'

    def __init__(self, rest_api, cors_domain_list=None, eth_rpc_endpoint=None, webui=False):
        self.rest_api = rest_api
        self.blueprint = create_blueprint()
        # TODO: Make configurable version
        self.rest_api.version = 1
        if self.rest_api.version == 1:
            self.flask_api_context = Api(
                self.blueprint,
                prefix=self._api_prefix,
            )
        else:
            raise ValueError('Invalid api version: {}'.format(self.rest_api.version))

        rootpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.flask_app = Flask(
            __name__,
            static_url_path='/static',
            static_folder=os.path.join(rootpath, 'ui', 'static')
        )
        if cors_domain_list:
            CORS(self.flask_app, origins=cors_domain_list)
        self._add_default_resources()
        self._register_type_converters()
        self.flask_app.register_blueprint(self.blueprint)
        self.flask_app.config['WEBUI_PATH'] = os.path.join(rootpath, 'ui')

        if webui:
            for route in ['/index.html', '/']:
                self.flask_app.add_url_rule(
                    route,
                    route,
                    view_func=self._serve_webui,
                    methods=['GET'],
                )

    def _add_default_resources(self):
        self.add_resource(AddressResource, '/address')
        self.add_resource(
            DetectorSignResource,
            '/detector_sign/<hexaddress:user_address>'
        )

    def _register_type_converters(self, additional_mapping=None):
        # an additional mapping concats to class-mapping and will overwrite existing keys
        if additional_mapping:
            mapping = dict(self._type_converter_mapping, **additional_mapping)
        else:
            mapping = self._type_converter_mapping

        for key, value in mapping.items():
            self.flask_app.url_map.converters[key] = value

    def add_resource(self, resource_cls, route):
        self.flask_api_context.add_resource(
            resource_cls,
            route,
            resource_class_kwargs={'rest_api_object': self.rest_api}
        )

    def _serve_webui(self, file='index.html'):
        try:
            assert file
            response = send_from_directory(self.flask_app.config['WEBUI_PATH'], file)
        except (NotFound, AssertionError):
            response = send_from_directory(self.flask_app.config['WEBUI_PATH'], 'index.html')
        return response

    def run(self, host='127.0.0.1', port=5011, **kwargs):
        self.flask_app.run(host=host, port=port, **kwargs)

    def start(self, host='127.0.0.1', port=5011):
        self.wsgiserver = WSGIServer((host, port), self.flask_app, log=log, error_log=log)
        self.wsgiserver.start()

    def stop(self, timeout=5):
        if getattr(self, 'wsgiserver', None):
            self.wsgiserver.stop(timeout)
            self.wsgiserver = None
