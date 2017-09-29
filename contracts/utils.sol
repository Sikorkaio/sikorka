/**
 * A contract containing utility function
 *
 * @author Lefteris Karapetsas
 * @license BSD3
 */
pragma solidity ^0.4.11;

contract Utils {
    /// @notice Check if a contract exists
    /// @param channel The address to check whether a contract is deployed or not
    /// @return True if a contract exists, false otherwise
    function contractExists(address channel) public constant returns (bool) {
        uint size;

        assembly {
            size := extcodesize(channel)
        }

        return size > 0;
    }
}
