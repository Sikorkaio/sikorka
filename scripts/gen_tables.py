#!/usr/bin/env python

import os
import math


def gen_sin_table(amplitude, table_size, number_of_bytes):
    print("Generating the sin() lookup table ...")
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'contracts',
        'trigonometry.sol'
    )
    with open(path) as f:
        lines = f.readlines()

    f = open(path, 'w')
    for line in lines:
        if 'bytes constant sin_table' in line:
            line = '    bytes constant sin_table = "'
            for i in range(0, table_size):
                radians = (i * (math.pi / 2)) / (table_size - 1)
                sin_value = amplitude * math.sin(radians)
                table_value = round(sin_value)
                hex_value = "{0:0{1}x}".format(table_value, 2 * number_of_bytes)
                line += '\\x' + '\\x'.join(
                    hex_value[i: i + 2] for i in range(0, len(hex_value), 2)
                )
            line += '";\n'

        f.write(line)


if __name__ == '__main__':
    amplitude = 32767
    table_size = 17
    number_of_bytes = 2
    gen_sin_table(amplitude, table_size, number_of_bytes)
