import pytest
import os
import gevent
from ethereum.tester import TransactionFailed
from sikorka.accounts import Account
from sikorka.service import Sikorka
from sikorka.utils import address_decoder
from utils import addr_equal


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


def test_sikorka_construction(
        sikorka_interface,
        detector,
        owner,
        name,
        latitude,
        longitude,
        seconds_allowed):

    assert addr_equal(owner, sikorka_interface.call().owner())
    assert addr_equal(detector, sikorka_interface.call().detector())
    assert name == sikorka_interface.call().name()
    assert seconds_allowed == sikorka_interface.call().seconds_allowed()


def test_sikorka_change_owner(sikorka_interface, owner, accounts):
    assert addr_equal(owner, sikorka_interface.call().owner())
    new_owner = accounts[3]

    # only owner should be able to change the owner
    with pytest.raises(TransactionFailed):
        sikorka_interface.transact({'from': new_owner}).change_owner(new_owner)

    assert sikorka_interface.transact({'from': owner}).change_owner(new_owner)
    assert addr_equal(new_owner, sikorka_interface.call().owner())


def test_sikorka_detector_authorizes_users(
        sikorka_contract,
        detector, owner,
        accounts,
        chain,
        web3):
    user = accounts[0]
    other_user = accounts[3]
    duration = 120

    assert user != detector
    assert user != owner
    assert other_user != detector
    assert other_user != owner

    # Detector authorizes a user
    sikorka_contract.transact({'from': detector}).authorize_user(user, duration)

    # Temporary fix since Populus did not update the location of request manager
    # yet: https://gitter.im/pipermerriam/populus?at=59cf9d7d177fb9fe7e204d6b
    web3._requestManager = web3.manager
    chain.wait.for_block(chain.web3.eth.blockNumber + 5)

    # After a bit, but within the authorize duration user interacts with the contract
    assert sikorka_contract.call().value() == 0
    assert sikorka_contract.transact({'from': user}).increase_value('')
    assert sikorka_contract.call().value() == 1

    # When more than the duration has passed the user can no longer interact
    # with the contract
    chain.wait.for_block(chain.web3.eth.blockNumber + 100)
    with pytest.raises(TransactionFailed):
        sikorka_contract.transact({'from': user}).increase_value('')
    assert sikorka_contract.call().value() == 1

    # Detector re-authorizes the same user
    sikorka_contract.transact({'from': detector}).authorize_user(user, duration)

    # The user is able to re-interact with the contract
    chain.wait.for_block(chain.web3.eth.blockNumber + 5)
    assert sikorka_contract.transact({'from': user}).increase_value('')
    assert sikorka_contract.call().value() == 2

    # And after some time he is no longer able to interact with it
    chain.wait.for_block(chain.web3.eth.blockNumber + 100)
    with pytest.raises(TransactionFailed):
        sikorka_contract.transact({'from': user}).increase_value('')
    assert sikorka_contract.call().value() == 2

    # Finally detector authorizes another user too
    sikorka_contract.transact({'from': detector}).authorize_user(other_user, duration)

    chain.wait.for_block(chain.web3.eth.blockNumber + 5)
    assert sikorka_contract.transact({'from': other_user}).increase_value('')
    assert sikorka_contract.call().value() == 3

    chain.wait.for_block(chain.web3.eth.blockNumber + 100)
    with pytest.raises(TransactionFailed):
        sikorka_contract.transact({'from': other_user}).increase_value('')
    assert sikorka_contract.call().value() == 3


@pytest.mark.parametrize('use_signee_detector', [True])
@pytest.mark.parametrize('seconds_allowed', [5])
def test_sikorka_detector_signs_message(
        sikorka_contract,
        sikorka_ctx,
        owner,
        accounts,
        chain,
        seconds_allowed,
        web3,
        block_now):
    user = accounts[0]
    other_user = accounts[3]
    detector = sikorka_ctx.address()

    assert user != detector
    assert user != owner
    assert other_user != detector
    assert other_user != owner

    # Detector signs a message for the user
    signed_msg = sikorka_ctx.sign_message_as_detector(address_decoder(user), time=block_now)

    # Temporary fix since Populus did not update the location of request manager
    # yet: https://gitter.im/pipermerriam/populus?at=59cf9d7d177fb9fe7e204d6b
    web3._requestManager = web3.manager
    chain.wait.for_block(chain.web3.eth.blockNumber + 5)

    # After a bit, but within the authorize duration user interacts with the contract
    assert sikorka_contract.call().value() == 0
    assert sikorka_contract.transact({'from': user}).increase_value(signed_msg)
    assert sikorka_contract.call().value() == 1

    # When more than the duration has passed the user can no longer interact
    # with the contract
    gevent.sleep(5)
    chain.wait.for_block(chain.web3.eth.blockNumber + 15)
    with pytest.raises(TransactionFailed):
        sikorka_contract.transact({'from': user}).increase_value(signed_msg)
    assert sikorka_contract.call().value() == 1
