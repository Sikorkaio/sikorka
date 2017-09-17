/**
 * The Sikorka Registry
 *
 * This contract serves as a searchable registry for all sikorka-enabled
 * smart contracts.
 *
 * Searching for a contract close to a pair of coordinates is not implemented here
 * as this better fits to be implemented in the client side due to gas concerns.
 *
 * @author Lefteris Karapetsas
 * @license BSD3
 */
pragma solidity ^0.4.11;

import "./utils.sol";

contract SikorkaRegistry is Utils {

    event ContractAdded(address contract_address, uint latitude, uint longitude);
    event ContractRemoved(address contract_address);

    struct Entry {
        address contract_address;
        uint latitude;
        uint longitude;
    }

    Entry[] public sikorka_contracts;
    mapping(address => uint) address_to_index;

    function getContractAddresses() constant returns (address[]) {
        uint i;
        address[] memory result;
        result = new address[](sikorka_contracts.length);
        for (i = 0; i < sikorka_contracts.length; i++) {
            result[i] = sikorka_contracts[i].contract_address;
        }
        return result;
    }

    /// @notice Register a new sikorka contract with the registry
    /// @param contract_address The address of the deployed sikorka contract
    /// @param latitude         The latitude part of the geolocation coordinates
    /// @param longitude        The longitude part of the geolocation coordinates
    function addContract(address contract_address, uint latitude, uint longitude) {
        require(contractExists(contract_address));

        sikorka_contracts.push(
            Entry({
                contract_address: contract_address,
                latitude: latitude,
                longitude: longitude
            }));
        // Taking index + 1, since mapping points to 0 for non-existent mapping,
        // so to recognize that we need to start indexing in the mapping from 1
        uint current_index = sikorka_contracts.length;
        address_to_index[contract_address] = current_index;

        ContractAdded(contract_address, latitude, longitude);
    }

    /// @notice Remove a sikorka contract from the registry
    function removeContract(address contract_address) {
        uint index = address_to_index[contract_address];
        require(index != 0);

        delete sikorka_contracts[index - 1];
        address_to_index[contract_address] = 0;

        ContractRemoved(contract_address);
    }
}
