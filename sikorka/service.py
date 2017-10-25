from web3 import Web3, HTTPProvider, IPCProvider


class Sikorka(object):

    def __init__(self, eth_rpc_endpoint, unlocked_acc):
        try:
            self.web3 = Web3(HTTPProvider(eth_rpc_endpoint))
        except:
            self.web3 = Web3(IPCProvider())

        self.account = unlocked_acc

    def get_our_address(self):
        return self.account.address()
