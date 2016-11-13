import decimal
import math

TRIGINT_ANGLES_PER_CYCLE = 16384
# The amplitude of the range of the values returned by the trigonometry funcs
AMPLITUDE = 32767
# The c library's test use 42 as accepted error. My own tests show that
# 41 is the biggest error I have gotten for the sin(64.75)
ACCURACY = 41


def drange(x, y, jump):
    while x < y:
        yield float(x)
        x += decimal.Decimal(jump)


def degrees_to_int_angle(degrees):
    return int(((degrees * TRIGINT_ANGLES_PER_CYCLE) / 360.0))


def radians_to_int_angle(radians):
    return ((radians * TRIGINT_ANGLES_PER_CYCLE) / (2 * math.pi))


def degrees_to_radians(degrees):
    return degrees * math.pi / 180.0


def result_to_float(res):
    return res * float(1.0 / AMPLITUDE)


def float_to_result(f):
    return int(f * AMPLITUDE)


def degrees_to_params(degrees):
    """
    Returns the needed parameters for the trigonometry tests out of the
    given angle in degrees
    :param double degrees: The angle in degrees as a double
    :return (double, int): Returns a tuple containing the angle in radians
                           and the approximated int angle
    """
    return (degrees_to_radians(degrees), degrees_to_int_angle(degrees))


def assert_sin(trigcontract, angle_degrees):
    angle_radians, angle_int = degrees_to_params(angle_degrees)
    res = trigcontract.call().sin(angle_int)
    expected_res = float_to_result(math.sin(angle_radians))
    # Since it's an approximation we get close to the expected value, but we
    # can also be off by some allowed error
    assert abs(res - expected_res) <= ACCURACY, "Testing sin({}) got {} but expected {}".format(
        angle_degrees, res, expected_res
    )


def test_sin(chain):
    tig = chain.get_contract('Trigonometry')

    for i in drange(0, 360, 0.25):
        assert_sin(tig, i)
