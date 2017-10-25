from sikorka.api.encoding import HexAddressConverter
from sikorka.api.resources import create_blueprint, AddressResource
from flask import Flask, make_response, url_for, send_from_directory, request
from flask.json import jsonify
from flask_restful import Api, abort
from flask_cors import CORS
from gevent.wsgi import WSGIServer

from ethereum import slogging
log = slogging.get_logger(__name__)


class APIServer(object):
    """
    Runs the API-server that routes the endpoint to the resources.
    The API is wrapped in multiple layers, and the Server should be invoked this way::


        # instance of the raiden-api
        raiden_api = RaidenAPI(...)

        # wrap the raiden-api with rest-logic and encoding
        rest_api = RestAPI(raiden_api)

        # create the server and link the api-endpoints with flask / flask-restful middleware
        api_server = APIServer(rest_api)

        # run the server
        api_server.run('127.0.0.1', 5001, debug=True)

    """

    # flask TypeConverter
    # links argument-placeholder in route (e.g. '/<hexaddress: channel_address>') to the Converter
    _type_converter_mapping = {
        'hexaddress': HexAddressConverter
    }
    _api_prefix = '/api/1'

    def __init__(self, rest_api, cors_domain_list=None, eth_rpc_endpoint=None):
        self.rest_api = rest_api
        self.blueprint = create_blueprint()
        # TODO: Make configurable version
        self.rest_api_version = 1
        if self.rest_api_version == 1:
            self.flask_api_context = Api(
                self.blueprint,
                prefix=self._api_prefix,
            )
        else:
            raise ValueError('Invalid api version: {}'.format(self.rest_api_version))

        self.flask_app = Flask(__name__)
        if cors_domain_list:
            CORS(self.flask_app, origins=cors_domain_list)
        self._add_default_resources()
        self._register_type_converters()
        self.flask_app.register_blueprint(self.blueprint)

    def _add_default_resources(self):

        self.add_resource(AddressResource, '/address')
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

    def run(self, host='127.0.0.1', port=5001, **kwargs):
        self.flask_app.run(host=host, port=port, **kwargs)

    def start(self, host='127.0.0.1', port=5001):
        self.wsgiserver = WSGIServer((host, port), self.flask_app, log=log, error_log=log)
        self.wsgiserver.start()

    def stop(self, timeout=5):
        if getattr(self, 'wsgiserver', None):
            self.wsgiserver.stop(timeout)
            self.wsgiserver = None
