/**
 * The Sikorka Basic Interface contract.
 *
 * All contracts using Sikorka should derive from it and
 * extend it so they can be used by the applications around it.
 *
 * @author Lefteris Karapetsas
 * @license BSD3
 */

pragma solidity ^0.4.1;

contract Owned {
    address owner;

    /// Allows only the owner to call a function
    modifier only_owner { if (msg.sender != owner) {
            throw;
        }
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
    string public question;
    bytes32 internal answer_hash;
    uint internal latitude;
    uint internal longtitude;

    /**
     * Require Proof Of Presence for the function to be executed
     *
     * @param _answer        The answer to give to the challenge question
     */
    modifier need_pop(string _answer) {
        if (sha3(_answer) != answer_hash) {
            throw;
        }
        _;
    }

    function SikorkaBasicInterface(
        string _name,
        uint _latitude,
        uint _longtitude,
        string _question,
        bytes32 _answer_hash
    ) {
        name = _name;
        latitude = _latitude;
        longtitude = _longtitude;
        question = _question;
        answer_hash = _answer_hash;
    }

    /**
     * Change the challenge question/answer combination
     *
     * @param _question        The new question
     * @param _answer_hash     The hash to the answer
     */
    function change_question(string _question, bytes32 _answer_hash) only_owner {
        question = _question;
        answer_hash = _answer_hash;
    }

    /**
     * Confirm whether the answer to the challenge question is correct
     *
     * @param _answer        The answer to the question
     */
    function confirm_answer(string _answer) constant returns (bool) {
        return sha3(_answer) == answer_hash;
    }
}
