/**
 * An example sikorka contract
 *
 * @author Lefteris Karapetsas
 * @license BSD3
 */
pragma solidity ^0.4.11;

import "./sikorka_basic_interface.sol";

contract SikorkaExample is SikorkaBasicInterface {

    uint public value;

    function SikorkaExample(
        address _detector,
        int _latitude,
        int _longitude,
        uint _seconds_allowed,
        address _registry_address
    )
        SikorkaBasicInterface(
            "Example",
            _detector,
            _latitude,
            _longitude,
            _seconds_allowed,
            _registry_address
        ) public {}

    function increase_value(bytes data) public proof_of_presence(data) {
        value += 1;
    }


}
