import time
from web3 import Web3, HTTPProvider, IPCProvider
from utils import address_encoder


class Sikorka(object):

    def __init__(self, eth_rpc_endpoint, unlocked_acc):
        try:
            self.web3 = Web3(HTTPProvider(eth_rpc_endpoint))
        except:
            self.web3 = Web3(IPCProvider())

        self.account = unlocked_acc

    def address(self):
        return self.account.address()

    def sign_message_as_detector(self, user_address_bin):
        user_address = address_encoder(user_address_bin)
        return self.account.create_signed_message(user_address, int(time.time()))
