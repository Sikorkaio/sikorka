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

import "./registry.sol";

contract Owned {
    address public owner;

    /// Allows only the owner to call a function
    modifier only_owner {
        require(msg.sender == owner);
        _;
    }

    function Owned() public {
        owner = msg.sender;
    }


    function change_owner(address _newOwner) public only_owner {
        owner = _newOwner;
    }
}

contract SikorkaBasicInterface is Owned {

    string public constant version = "0.1.0";
    string public name;
    int internal latitude;
    int internal longitude;
    // The address corresponding to the detector device for this
    // contract. Used in verifying proof of presence
    address public detector;
    // Number of seconds allowed for proof of presence after the timestamp
    // of the signed message
    uint public seconds_allowed;
    // Mapping of allowed addresses to time when they were next to the detector
    mapping(address => uint) address_to_start_time;
    // Mapping of allowed addresses to duration presence is valid
    mapping(address => uint) address_to_duration;

    modifier only_detector () {
        require(msg.sender == detector);
        _;
    }

    /// Require Proof Of Presence for the function to be executed
    /// Version where the detector should have already sent a message
    /// authorizing the user for a period of time.
    modifier proof_of_presence(bytes message) {
        check_proof_of_presence(message);
        _;
    }

    function check_proof_of_presence(bytes message) view public {
        if (message.length == 0) {
            // detector should have authorized the user
            detector_direct_authorization();
        } else if (message[0] == 1) {
            detector_signed_message(message);
        } else if (message[1] == 2) {
            // only allow this scenario if the contract was deployed without a detector
            require(detector == 0);
            simple_presence_check(message);
        } else {
            require(false); // unrecognized protocol
        }
    }

    function detector_direct_authorization() view public {
        uint start = address_to_start_time[msg.sender];
        require(start != 0);
        require(now - start <= address_to_duration[msg.sender]);
    }

    function simple_presence_check(bytes message) public {
        int g_latitude;
        int g_longitude;
        assembly {
            // skip first byte which is the proof type identifier
            g_latitude := mload(add(message, 33))
            g_longitude := mload(add(message, 65))
        }

        // TODO proper distance check for coordinates, this is rather idiotic
        int latitude_diff;
        int longitude_diff;
        if (g_latitude >= latitude) {
            latitude_diff = g_latitude - latitude;
        } else {
            latitude_diff = latitude - g_latitude;
        }
        assert(latitude_diff >= 0);

        if (g_longitude >= longitude) {
            longitude_diff = g_longitude - longitude;
        } else {
            longitude_diff = longitude - g_longitude;
        }
        assert(longitude_diff >= 0);

        // user must be close to the contract
        require(latitude_diff > 1000 || longitude_diff > 1000);
    }

    function detector_signed_message(bytes message) view public {
        address signee;
        address user;
        uint64 time;
        (signee, user, time) = decode_message(message);

        // Corresponding detector must have signed the message
        // require(signee == detector);
        // The message must have been signed for person interacting with the contract
        require(user == msg.sender);
        // Timestamp must be in the past
        require(time < block.timestamp);
        // Timestamp must be within the seconds_allowed
        require(block.timestamp - time <= seconds_allowed);
    }

    function decode_message(bytes message) view internal returns (
        address signee,
        address user,
        uint64 time
    ) {
        uint signature_start;
        bytes memory signature;
        bytes memory data;
        uint length = message.length;

        signature_start = length - 65;
        signature = slice(message, signature_start, length);
        data = slice(message, 1, signature_start);

        var (r, s, v) = signature_split(signature);
        bytes32 data_hash = keccak256(data);
        signee = ecrecover(data_hash, v, r, s);

        require(signee == detector);

        (user, time) = decode_data(data);
    }

    function decode_data(bytes data) pure internal returns (
        address user,
        uint64 time
    ) {
        assembly {
            user := mload(add(data, 20))
            time := mload(add(data, 28))
        }
    }

    /// Called by the corresponding detector device to authorize a user
    /// who has been detected as present in the vicinity.
    /// @param user     The address of the user for whom the detector wants
    ///                 to provide proof of presence
    /// @param duration The duration in seconds for which the proof of presence
    ///                 will be valid.
    function authorize_user(address user, uint duration) public only_detector {
        address_to_start_time[user] = now;
        address_to_duration[user] = duration;
    }

    ///
    /// @param _name             A name to give to the contract
    /// @param _detector         The address of the detector this contract is tied to
    /// @param _latitude         The latitude part of the geolocation coordinates
    /// @param _longitude        The longitude part of the geolocation coordinates
    /// @param _seconds_allowed  The number of seconds allowed for proof of presence after
    ///                          the proof has been submitted.
    function SikorkaBasicInterface(
        string _name,
        address _detector,
        uint _latitude,
        uint _longitude,
        uint _seconds_allowed,
        address registry_address
    ) public {
        name = _name;
        latitude = _latitude;
        longitude = _longitude;
        seconds_allowed = _seconds_allowed;
        detector = _detector;

        SikorkaRegistry r = SikorkaRegistry(registry_address);
        r.addContract(address(this), _latitude, _longitude);
    }

    function slice(bytes a, uint start, uint end) pure internal returns (bytes n) {
        require(a.length >= end);
        require(start >= 0);

        n = new bytes(end-start);
        for (uint i = start; i < end; i++) {
            n[i-start] = a[i];
        }
    }

    function signature_split(bytes signature)
        pure
        internal
        returns (bytes32 r, bytes32 s, uint8 v)
    {
        // The signature format is a compact form of:
        //   {bytes32 r}{bytes32 s}{uint8 v}
        // Compact means, uint8 is not padded to 32 bytes.
        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            // Here we are loading the last 32 bytes, including 31 bytes
            // of 's'. There is no 'mload8' to do this.
            //
            // 'byte' is not working due to the Solidity parser, so lets
            // use the second best option, 'and'
            v := and(mload(add(signature, 65)), 0xff)
        }

        require(v == 27 || v == 28);
    }

}
