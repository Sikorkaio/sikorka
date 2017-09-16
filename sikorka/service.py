from web3 import Web3, HTTPProvider, IPCProvider


class Sikorka(object):

    def __init__(self, eth_rpc_endpoint, privatekey_bin):
        try:
            self.web3 = Web3(HTTPProvider(eth_rpc_endpoint))
        except:
            self.web3 = Web3(IPCProvider())

        self.privatekey_bin = privatekey_bin
