/**
 * An example sikorka contract
 *
 * @author Lefteris Karapetsas
 * @license BSD3
 */
pragma solidity ^0.4.11;

import "./sikorka_basic_interface.sol";
import "./token.sol";

contract SikorkaDiscountExample is SikorkaBasicInterface, StandardToken {

    function SikorkaDiscountExample(
        string _name,
        address _detector,
        int _latitude,
        int _longitude,
        uint _seconds_allowed,
        address _registry_address,
        uint _totalSupply
    )
        SikorkaBasicInterface(
            _name,
            _detector,
            _latitude,
            _longitude,
            _seconds_allowed,
            _registry_address
        ) public {

        totalSupply = _totalSupply;
        balances[this] = _totalSupply;
    }

    function claimTokens(bytes data) public proof_of_presence(data) {
        transfer(msg.sender, 100);
    }


}
