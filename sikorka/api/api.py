import json
import http.client
from binascii import hexlify
from flask import make_response


def api_response(result, status_code=http.client.OK):
    response = make_response((
        json.dumps(result),
        status_code,
        {'mimetype': 'application/json', 'Content-Type': 'application/json'}
    ))
    return response


class RestAPI(object):

    def __init__(self, sikorka):
        self.api_version = 1
        self.sikorka = sikorka

    def get_our_address(self):
        return api_response(
            result=dict(address=self.sikorka.address())
        )

    def detector_sign(self, user_address_bin):
        signed_bytes = self.sikorka.sign_message_as_detector(user_address_bin)
        return api_response(
            result=dict(message=hexlify(signed_bytes).decode('utf-8'))
        )
