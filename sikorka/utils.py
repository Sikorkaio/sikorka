# Some of these functions are taken from pyethapp/pyethereum


def decode_hex(s):
    if isinstance(s, bytearray):
        s = str(s)
    if not isinstance(s, (str, unicode)):
        raise TypeError('Value must be an instance of str or unicode')
    return s.decode('hex')


def encode_hex(s):
    if isinstance(s, bytearray):
        s = str(s)
    if not isinstance(s, (str, unicode)):
        raise TypeError('Value must be an instance of str or unicode')
    return s.encode('hex')


def data_decoder(data):
    """Decode `data` representing unformatted data."""
    if not data.startswith('0x'):
        data = '0x' + data

    if len(data) % 2 != 0:
        # workaround for missing leading zeros from netstats
        assert len(data) < 64 + 2
        data = '0x' + '0' * (64 - (len(data) - 2)) + data[2:]

    try:
        return decode_hex(data[2:])
    except TypeError:
        raise ValueError('Invalid data hex encoding', data[2:])


def address_decoder(data):
    """Decode an address from hex with 0x prefix to 20 bytes."""
    addr = data_decoder(data)
    if len(addr) not in (20, 0):
        raise ValueError('Addresses must be 20 or 0 bytes long')
    return addr


def address_encoder(address):
    assert len(address) in (20, 0)
    return '0x' + encode_hex(address)
