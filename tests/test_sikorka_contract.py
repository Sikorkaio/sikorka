import pytest
import gevent
from ethereum.tester import TransactionFailed

from sikorka.utils import address_decoder
from utils import addr_equal


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
