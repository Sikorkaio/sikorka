import pytest
from ethereum.tester import TransactionFailed


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

    queried_contracts = cc.call().getContractAddresses()
    import pdb
    pdb.set_trace()
    assert all(entry[0] in queried_contracts for entry in entries)


def test_registry_add_non_contract_address(chain):
    """Test that adding a non-contract address fails"""
    c, _ = chain.provider.get_or_deploy_contract('SikorkaRegistry')
    with pytest.raises(TransactionFailed):
        c.transact().addContract("0xacb35c909b156feeace5c58e9b6b7162a4fa2beb", 10, 100)
