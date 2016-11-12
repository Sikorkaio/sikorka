/**
 * Basic trigonometry functions
 *
 * Solidity contract offering the functionality of basic trigonometry functions
 * with both input and output being integer approximated.
 *
 * This is useful since:
 * - At the moment no floating/fixed point math can happen in solidity
 * - Should be (?) cheaper than the actual operations using floating point
 *   if and when they are implemented.
 *
 * The implementation is based off Dave Dribin's trigint C library
 * http://www.dribin.org/dave/trigint/
 *
 * @author Lefteris Karapetsas
 * @license BSD3
 */

pragma solidity ^0.4.4;

contract Trigonometry {

    // Table index into the trignometric table
    uint8 constant INDEX_WIDTH = 4;
    // Interpolation between successive entries in the tables
    uint8 constant INTERP_WIDTH = 8;
    uint8 constant INDEX_OFFSET = 12 - INDEX_WIDTH; // 8
    uint8 constant INTERP_OFFSET = INDEX_OFFSET - INTERP_WIDTH; // 0
    uint constant QUADRANT_HIGH_MASK = 8192;
    uint constant QUADRANT_LOW_MASK = 4096;
    uint8 constant SINE_TABLE_SIZE = 16;

    // TODO: constant is not yet implemented for this type
    // Nice to have in solidity: if identifier is a constant uint
    // allow it as index of array. e.g: SINE_TABLE_SIZE + 1
    uint16[17] sin16_table = [
        0,  3211,  6392,  9511, 12539, 15446, 18204, 20787, 23169,
        25329, 27244, 28897, 30272, 31356, 32137, 32609, 32767
    ];

    function Trigonometry() {
    }


    function bits(uint16 _value, uint8 _width, uint8 _bit) internal returns (int32) {
        /* return (_value >> _bit) & ((1 << _width) - 1); */
        return (_value / (2 ** _bit)) & (((2 **  _width)) - 1);
    }


    /**
     * Return the sine of an integer approximated angle
     *
     * @param _angle A 14-bit angle, 0 - 0x3FFFF. This divides the circle
     *              into 16,384 angle units, instead of the standard 360 degrees.
     *              Thus:
     *              - 1 angle unit =~ 360/16384 =~ 0.0219727 degrees
     *              - 1 angle unit =~ 2*M_PI/16384 =~ 0.0003835 radians
     */
    function sin(uint16 _angle) returns (int) {
        int32 interp = bits(_angle, INTERP_WIDTH, INTERP_OFFSET);
        uint8 index = uint8(bits(_angle, INDEX_WIDTH, INDEX_OFFSET));

        bool is_odd_quadrant = (_angle & QUADRANT_LOW_MASK) == 0;
        bool is_negative_quadrant = (_angle & QUADRANT_HIGH_MASK) != 0;

        if (!is_odd_quadrant) {
            index = SINE_TABLE_SIZE - 1 - index;
        }

        int32 x1 = sin16_table[index];
        int32 x2 = sin16_table[index + 1];
        /* int32 approximation = ((x2-x1) * interp) >> SINE_INTERP_WIDTH; */
        int32 approximation = ((x2 - x1) * interp) / (2 ** INTERP_WIDTH);

        int32 sine;
        if (is_odd_quadrant) {
            sine = x1 + approximation;
        } else {
            sine = x2 - approximation;
        }

        if (is_negative_quadrant) {
            sine *= -1;
        }

        return sine;
    }

}
