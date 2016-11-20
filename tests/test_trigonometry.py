from __future__ import division
import decimal
import math
import pytest
import os

import sys
sys.path.insert(
    0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'scripts'
    )
)
from generate_trigonometry import generate_trigonometry


# The c library's test use 42 as accepted error. My own tests show that
# 41 is the biggest error I have gotten for the sin(64.75)
ACCURACY = 0.00125125888852


def drange(x, y, jump):
    while x < y:
        yield float(x)
        x += decimal.Decimal(jump)


def degrees_to_radians(degrees):
    return degrees * math.pi / 180.0


class TrigonometryHandler(object):

    def __init__(self, number_of_bits):
        self.angles_per_cycle = 1 << (number_of_bits - 2)
        # The amplitude of the range of the values returned
        # by the trigonometry functions
        self.amplitude = (1 << (number_of_bits - 1)) - 1
        self.contract = None

    def degrees_to_int_angle(self, degrees):
        return int(((degrees * self.angles_per_cycle) / 360.0))

    def radians_to_int_angle(self, radians):
        return ((radians * self.angles_per_cycle) / (2 * math.pi))

    def result_to_float(self, res):
        return res * float(1.0 / self.amplitude)

    def float_to_result(self, f):
        return int(f * self.amplitude)

    def degrees_to_params(self, degrees):
        """
        Returns the needed parameters for the trigonometry tests out of the
        given angle in degrees
        :param double degrees: The angle in degrees as a double
        :return (double, int): Returns a tuple containing the angle in radians
                           and the approximated int angle
        """
        return (
            degrees_to_radians(degrees),
            self.degrees_to_int_angle(degrees)
        )

    def assert_sin(self, angle_degrees):
        angle_radians, angle_int = self.degrees_to_params(angle_degrees)
        res = self.contract.call().sin(angle_int)
        expected_res = self.float_to_result(math.sin(angle_radians))
        # Since it's an approximation we get close to the expected value, but
        # we can also be off by some allowed error
        error = abs(res - expected_res) / self.amplitude
        assert error <= ACCURACY, "Testing sin({}) got {} but expected {}".format(
            angle_degrees, res, expected_res
        )
        return error

    def assert_cos(self, angle_degrees):
        angle_radians, angle_int = self.degrees_to_params(angle_degrees)
        res = self.contract.call().cos(angle_int)
        expected_res = self.float_to_result(math.cos(angle_radians))
        # Since it's an approximation we get close to the expected value, but
        # we can also be off by some allowed error
        error = abs(res - expected_res) / self.amplitude

        assert error <= ACCURACY, "Testing cos({}) got {} but expected {}".format(
            angle_degrees, res, expected_res
        )
        return error


@pytest.fixture
def number_of_bits():
    return 16


@pytest.fixture
def table_size():
    return 17


@pytest.fixture
def trigonometry_handler(chain, number_of_bits, table_size):
    handler = TrigonometryHandler(number_of_bits)
    generate_trigonometry(number_of_bits, table_size, for_tests=True)
    handler.contract = chain.get_contract('TrigonometryGenerated')
    return handler


def test_sin(trigonometry_handler):
    error = 0
    for i in drange(0, 360, 0.25):
        error = max(error, trigonometry_handler.assert_sin(i))

    print("Maximum sin() error was: {}".format(error))


def test_cos(trigonometry_handler):
    error = 0
    for i in drange(0, 360, 0.25):
        error = max(error, trigonometry_handler.assert_cos(i))

    print("Maximum cos() error was: {}".format(error))
