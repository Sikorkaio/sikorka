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

    function SikorkaExample(address _detector, uint _latitude, uint _longitude)
        SikorkaBasicInterface(
            "Example",
            _detector,
            _latitude,
            _longitude,
            60
        ) {}

    function increase_value() need_pop {
        value += 1;
    }
}
