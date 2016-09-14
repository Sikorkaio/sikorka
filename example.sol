/**
 * An example contract using the Sikorka API
 *
 * A shop owner wants to give some discount credit tokens to any users
 * who go on location and interact with the contracts he/she has deployed.
 *
 * @author Lefteris Karapetsas
 * @license BSD3
 */

pragma solidity ^0.4.1;

import "./sikorka_basic_interface.sol";


contract DiscountTokens is SikorkaBasicInterface {

    mapping (address => uint256) public balances;
    address[] participants;
    uint tokens_to_reward;
    uint public token_round_end;

    /**
     * Constructor
     *
     * @param _tokens_to_reward    The number of tokens to reward to each
     *                             user who succesfully interacts with
     *                             the contract
     * @param _round_duration      The number of seconds this token round
     *                             will last
     */
    function DiscountTokens(
        string _name,
        uint _latitude,
        uint _longtitude,
        string _question,
        bytes32 _answer_hash,
        uint _tokens_to_reward,
        uint _round_duration
    ) SikorkaBasicInterface(
        _name,
        _latitude,
        _longtitude,
        _question,
        _answer_hash) {

        tokens_to_reward = _tokens_to_reward;
        token_round_end = now + _round_duration;
    }

    /**
     * Claim discount tokens for the shop!
     *
     * @param _answer        The answer to the challenge question.
     */
    function claimToken(string _answer) need_pop(_answer) {

        // User already got their discount tokens for this round
        if (balances[msg.sender] != 0) {
            return;
        }
        balances[msg.sender] += tokens_to_reward;
    }

    /**
     * Clear out the tokens to allow for a new round of discounts
     *
     * @param _new_duration        The new duration in seconds
     */
    function clearTokens(uint _new_duration) only_owner {
        for (uint i = 0; i < participants.length; i ++) {
            balances[participants[i]] = 0;
        }
        delete participants;
    }
}
