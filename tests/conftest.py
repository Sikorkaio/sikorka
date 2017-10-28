import pytest
import os

from sikorka.service import Sikorka
from sikorka.accounts import Account


@pytest.fixture()
def name():
    return "test_sikorka_contract"


@pytest.fixture()
def latitude():
    return 1


@pytest.fixture()
def longitude():
    return 2


@pytest.fixture()
def seconds_allowed():
    return 60


@pytest.fixture
def owner_index():
    return 1


@pytest.fixture()
def block_now(web3):
    return web3.eth.getBlock("latest").timestamp


@pytest.fixture
def owner(web3, owner_index):
    return web3.eth.accounts[owner_index]


@pytest.fixture
def detector_index():
    return 2


@pytest.fixture
def detector(web3, detector_index):
    return web3.eth.accounts[detector_index]


@pytest.fixture()
def sikorka_ctx():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    acc = Account(os.path.join(dir_path, 'test_key.json'), '123')
    sikorka = Sikorka(None, acc)
    return sikorka


@pytest.fixture()
def use_signee_detector():
    return False


@pytest.fixture
def create_contract(chain, owner, web3, use_signee_detector, sikorka_ctx):
    def get(contract_type, arguments, transaction=None):
        if not transaction:
            transaction = {}
        if 'from' not in transaction:
            transaction['from'] = owner

        if use_signee_detector:
            arguments[0] = sikorka_ctx.address()

        deploy_txn_hash = contract_type.deploy(transaction=transaction, args=arguments)
        contract_address = chain.wait.for_contract_address(deploy_txn_hash)
        contract = contract_type(address=contract_address)

        return contract
    return get


@pytest.fixture()
def sikorka_interface(
        chain,
        web3,
        create_contract,
        name,
        detector,
        latitude,
        longitude,
        seconds_allowed):
    registry, _ = chain.provider.deploy_contract('SikorkaRegistry')
    factory = chain.provider.get_contract_factory('SikorkaBasicInterface')
    sikorka = create_contract(factory, [
        name, detector, latitude, longitude, seconds_allowed, registry.address
    ])

    return sikorka


@pytest.fixture()
def sikorka_contract(
        chain,
        web3,
        create_contract,
        detector,
        latitude,
        longitude):
    registry, _ = chain.provider.deploy_contract('SikorkaRegistry')
    factory = chain.provider.get_contract_factory('SikorkaExample')
    sikorka = create_contract(factory, [
        detector, latitude, longitude, seconds_allowed(), registry.address
    ])

    return sikorka


@pytest.fixture()
def create_sikorka_contract(chain, web3, create_contract):
    def get(name, detector, latitude, longitude, seconds_allowed):
        registry, _ = chain.provider.deploy_contract('SikorkaRegistry')
        factory = chain.provider.get_contract_factory('SikorkaExample')
        sikorka = create_contract(factory, [
            detector, latitude, longitude, seconds_allowed(), registry.address
        ])

        return sikorka
    return get
