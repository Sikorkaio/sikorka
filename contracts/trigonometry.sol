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
    uint constant INDEX_WIDTH = 4;
    // Interpolation between successive entries in the tables
    uint constant INTERP_WIDTH = 8;
    uint constant INDEX_OFFSET = 12 - INDEX_WIDTH; // 8
    uint constant INTERP_OFFSET = INDEX_OFFSET - INTERP_WIDTH; // 0
    uint constant QUADRANT_HIGH_MASK = 8192;
    uint constant QUADRANT_LOW_MASK = 4096;
    uint constant SINE_TABLE_SIZE = 16;

    // TODO: constant is not yet implemented for this type
    // Nice to have in solidity: if identifier is a constant uint
    // allow it as index of array. e.g: SINE_TABLE_SIZE + 1
    uint16[17] sin16_table = [
        0,  3211,  6392,  9511, 12539, 15446, 18204, 20787, 23169,
        25329, 27244, 28897, 30272, 31356, 32137, 32609, 32767
    ];

    function Trigonometry() {
    }


    function bits(uint _value, uint _width, uint _bit) internal returns (uint) {
        /* return (_value >> _bit) & ((1 << _width) - 1); */
        return (_value / (2 ** _bit)) & (((2 **  _width)) - 1);
    }

    /**
     * Return the sine of an integer approximated angle as a signed 16-bit
     * integer. It is scaled to an amplitude of 32,767, thus values
     * will range from -32,767 to +32,767.
     *
     * @param _angle A 14-bit angle, 0 - 0x3FFFF. This divides the circle
     *              into 16,384 angle units, instead of the standard 360 degrees.
     *              Thus:
     *              - 1 angle unit =~ 360/16384 =~ 0.0219727 degrees
     *              - 1 angle unit =~ 2*M_PI/16384 =~ 0.0003835 radians
     * @return The sine result as a number in the range -32767 to 32767. The
     *         error margin can be up to 41 decimal digits.
     */
    function sin(uint16 _angle) returns (int) {
        uint interp = bits(_angle, INTERP_WIDTH, INTERP_OFFSET);
        uint index = bits(_angle, INDEX_WIDTH, INDEX_OFFSET);

        bool is_odd_quadrant = (_angle & QUADRANT_LOW_MASK) == 0;
        bool is_negative_quadrant = (_angle & QUADRANT_HIGH_MASK) != 0;

        if (!is_odd_quadrant) {
            index = SINE_TABLE_SIZE - 1 - index;
        }

        uint x1 = sin16_table[index];
        uint x2 = sin16_table[index + 1];
        uint approximation = ((x2 - x1) * interp) / (2 ** INTERP_WIDTH);

        int sine;
        if (is_odd_quadrant) {
            sine = int(x1) + int(approximation);
        } else {
            sine = int(x2) - int(approximation);
        }

        if (is_negative_quadrant) {
            sine *= -1;
        }

        return sine;
    }

}
