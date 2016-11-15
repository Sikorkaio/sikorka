#!/usr/bin/env python

import os
import math
import re
import sys
import decimal
from __future__ import division


def re_replace_constant(string, typename, varname, value):
    constant_re = re.compile(
        r"({} +constant +{} +=) +(.*);".format(typename, varname)
    )
    match = constant_re.search(string)
    if not match:
        print(
            "ERROR: Could not match RE for '{}' during template generation.".
            format(varname)
        )
        sys.exit(1)

    if match.groups()[1] == str(value):
        # The value already exists in the source
        return string

    new_string = constant_re.sub(r"\1 {};".format(str(value)), string)
    return new_string


def gen_sin_table(amplitude, table_size, number_of_bytes):
    table = '"'
    for i in range(0, table_size):
        radians = (i * (math.pi / 2)) / (table_size - 1)
        sin_value = amplitude * math.sin(radians)
        table_value = round(sin_value)
        hex_value = "{0:0{1}x}".format(int(table_value), 2 * number_of_bytes)
        table += '\\x' + '\\x'.join(
            hex_value[i: i + 2] for i in range(0, len(hex_value), 2)
        )
    return table + '"'


def generate_trigonometry(amplitude, table_size, number_of_bytes):
    print("Generating the sin() lookup table ...")
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'contracts',
        'trigonometry.sol'
    )
    with open(path) as f:
        lines = f.read()

    lines = re_replace_constant(lines, 'uint8', 'entry_bytes', number_of_bytes)
    lines = re_replace_constant(
        lines,
        'uint',
        'SINE_TABLE_SIZE',
        table_size - 1
    )
    lines = re_replace_constant(
        lines,
        'uint',
        'QUADRANT_HIGH_MASK',
        int(round(amplitude / 4))
    )
    lines = re_replace_constant(
        lines,
        'uint',
        'QUADRANT_LOW_MASK',
        int(round(amplitude / 8))
    )
    lines = re_replace_constant(
        lines,
        'bytes',
        'sin_table',
        gen_sin_table(amplitude, table_size, number_of_bytes)
    )

    with open(path, 'w') as f:
        f.write(lines)

if __name__ == '__main__':
    amplitude = 32767
    table_size = 17
    number_of_bytes = 2
    generate_trigonometry(amplitude, table_size, number_of_bytes)
