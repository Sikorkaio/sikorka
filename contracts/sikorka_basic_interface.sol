/**
 * The Sikorka Basic Interface contract.
 *
 * All contracts using Sikorka should derive from it and
 * extend it so they can be used by the applications around it.
 *
 * @author Lefteris Karapetsas
 * @license BSD3
 */

pragma solidity ^0.4.11;

contract Owned {
    address owner;

    /// Allows only the owner to call a function
    modifier only_owner {
        require(msg.sender == owner);
        _;
    }

    function Owned() {
        owner = msg.sender;
    }


    function change_owner(address _newOwner) only_owner {
        owner = _newOwner;
    }
}

contract SikorkaBasicInterface is Owned {

    string public name;
    uint internal latitude;
    uint internal longitude;
    // The address corresponding to the detector device for this
    // contract. Used in verifying proof of presence
    address public detector;
    // Number of seconds allowed for proof of presence after the timestamp
    // of the signed message
    uint seconds_allowed;

    /**
     * Require Proof Of Presence for the function to be executed
     * @param message      The signed message containing the timestamp,
     *                     distance from the detector and address of user
     */
    modifier need_pop(bytes message) {
        address signee;
        uint timestamp;
        address user;
        uint distance;

        (signee, timestamp, user, distance) = decode_message(message);

        // Corresponding detector must have signed the message
        require(signee == detector);
        // The message must have been signed for person interacting with the contract
        require(user == msg.sender);
        // Timestamp must be in the past
        require(timestamp < block.timestamp);
        // Timestamp must be within the seconds_allowed
        require(block.timestamp - timestamp < seconds_allowed);

        _;
    }

    function decode_message(bytes message) internal returns (
        address signee,
        uint timestamp,
        address user,
        uint distance
    ) {
        // TODO
    }

    /**
     * @param name             A name to give to the contract
     * @param detector         The address of the detector this contract is tied to
     * @param latitude         The latitude part of the geolocation coordinates
     * @param longitude        The longitude part of the geolocation coordinates
     * @param seconds_allowed  The number of seconds allowed for proof of presence after
     *                         the proof has been submitted.
     */
    function SikorkaBasicInterface(
        string name,
        address detector,
        uint latitude,
        uint longitude,
        uint seconds_allowed
    ) {
        name = name;
        latitude = latitude;
        longitude = longitude;
        seconds_allowed = seconds_allowed;
        detector = detector;
    }

}
