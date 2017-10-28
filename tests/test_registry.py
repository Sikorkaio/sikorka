import pytest
from ethereum.tester import TransactionFailed
from conftest import sikorka_contract



def test_registry_add_contract(chain):
    """Test adding contracts to the registry and querying them"""
    # Deploy 4 contracts (could be anything) since we can only register contracts
    c1, _ = chain.provider.deploy_contract('SikorkaRegistry')
    c2, _ = chain.provider.deploy_contract('SikorkaRegistry')
    c3, _ = chain.provider.deploy_contract('SikorkaRegistry')
    c4, _ = chain.provider.deploy_contract('SikorkaRegistry')

    entries = [
        (c1.address, 1, 2),
        (c2.address, 2, 4),
        (c3.address, 4, 6),
        (c4.address, 5, 10),
    ]

    cc, _ = chain.provider.get_or_deploy_contract('SikorkaRegistry')

    for entry in entries:
        cc.transact().addContract(str(entry[0]), entry[1], entry[2])

    queried_contracts = [x.lower() for x in cc.call().getContractAddresses()]
    assert all(entry[0] in queried_contracts for entry in entries)


def test_registry_remove_nonexistent_contract(chain):
    """Test that removing a non-contract address fails"""
    c, _ = chain.provider.get_or_deploy_contract('SikorkaRegistry')
    with pytest.raises(TransactionFailed):
        c.transact().removeContract("0xacb35c909b156feeace5c58e9b6b7162a4fa2beb")


def test_registry_get_contract_coordinates(chain, web3, create_contract, detector):
    c1 = sikorka_contract(chain, web3, create_contract, detector, 1, -1, False)
    c2 = sikorka_contract(chain, web3, create_contract, detector, 2, -2, False)
    c3 = sikorka_contract(chain, web3, create_contract, detector, 3, -3, False)

    cc, _ = chain.provider.get_or_deploy_contract('SikorkaRegistry')

    entries = [(c1.address, 1, -1), (c2.address, 2, -2), (c3.address, 3, -3)]

    queried_contracts = [x.lower() for x in cc.call().getContractAddresses()]
    assert all(entry[0] in queried_contracts for entry in entries)

    queried_latlong_pairs = cc.call().getContractCoordinates()

    assert len(queried_latlong_pairs) == len(entries) * 2
    for i in range(0, len(queried_latlong_pairs) // 2):
        assert queried_latlong_pairs[2 * i] == entries[i][1]
        assert queried_latlong_pairs[2 * i + 1] == entries[i][2]
