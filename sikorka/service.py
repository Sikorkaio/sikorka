import time
from web3 import Web3, HTTPProvider, IPCProvider
from sikorka.utils import address_encoder


class Sikorka(object):

    def __init__(self, eth_rpc_endpoint, unlocked_acc):
        if eth_rpc_endpoint:
            try:
                self.web3 = Web3(HTTPProvider(eth_rpc_endpoint))
            except:
                self.web3 = Web3(IPCProvider())

        self.account = unlocked_acc

    def address(self):
        return self.account.address()

    def sign_message_as_detector(self, user_address_bin, time=int(time.time())):
        """Returns the required signed message as bytes"""
        user_address = address_encoder(user_address_bin)
        signed_bytes = self.account.create_signed_message(
            user_address,
            time
        )
        signed_bytes = bytearray.fromhex('01') + signed_bytes
        return signed_bytes
