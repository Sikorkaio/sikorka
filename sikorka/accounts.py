# A lot of the code here is taken from pyetherem/pyethapp and raiden

# -*- coding: utf-8 -*-
import getpass
import json
import os
import sys
import binascii
import struct
from ethereum.keys import decode_keystore_json
from coincurve import PrivateKey
from sha3 import keccak_256


def sha3(data):
    """
    Raises:
        RuntimeError: If Keccak lib initialization failed, or if the function
        failed to compute the hash.

        TypeError: This function does not accept unicode objects, they must be
        encoded prior to usage.
    """
    return keccak_256(data).digest()


def address_decoder(addr):
    if addr[:2] == '0x':
        addr = addr[2:]

    addr = binascii.unhexlify(addr)
    assert len(addr) in (20, 0)
    return addr


class Account(object):

    def __init__(self, keyfile, passfile_or_password):
        with open(keyfile) as data_file:
            data = json.load(data_file)

        if os.path.isfile(passfile_or_password):
            with open(passfile_or_password) as f:
                password = f.read().strip('\n')
        else:
            password = passfile_or_password

        privkey_bin = decode_keystore_json(data, password)
        self.private_key = PrivateKey(privkey_bin)

    def address(self):
        return binascii.hexlify(bytearray(
            sha3(self.private_key.public_key.format(
                compressed=False)[1:])[-20:]
        )).decode('utf-8')

    def sign(self, messagedata):
        signature = self.private_key.sign_recoverable(
            messagedata,
            hasher=sha3
        )
        if len(signature) != 65:
            raise ValueError('invalid signature')

        return signature[:-1] + bytearray(chr(signature[-1] + 27), 'utf-8')

    def create_signed_message(self, user_address_hex, timestamp):
        message_data = (
            bytearray(address_decoder(user_address_hex)) +
            bytearray(struct.pack(">Q", timestamp))
        )
        sig = self.sign(message_data)
        message_data = message_data + bytearray(sig)
        return message_data


def find_datadir():
    home = os.path.expanduser('~')
    if home == '~':  # Could not expand user path
        return None
    datadir = None

    if sys.platform == 'darwin':
        datadir = os.path.join(home, 'Library', 'Ethereum')
    # NOTE: Not really sure about cygwin here
    elif sys.platform == 'win32' or sys.platform == 'cygwin':
        datadir = os.path.join(home, 'AppData', 'Roaming', 'Ethereum')
    elif os.name == 'posix':
        datadir = os.path.join(home, '.ethereum')
    else:
        raise RuntimeError('Unsupported Operating System')

    if not os.path.isdir(datadir):
        return None
    return datadir


def find_keystoredir():
    datadir = find_datadir()
    if datadir is None:
        # can't find a data directory in the system
        return None
    keystore_path = os.path.join(datadir, 'keystore')
    if not os.path.exists(keystore_path):
        # can't find a keystore under the found data directory
        return None
    return keystore_path


class AccountManager(object):

    def __init__(self, keystore_path=None):
        self.keystore_path = keystore_path
        self.accounts = {}
        if self.keystore_path is None:
            self.keystore_path = find_keystoredir()
        if self.keystore_path is not None:

            for f in os.listdir(self.keystore_path):
                fullpath = os.path.join(self.keystore_path, f)
                if os.path.isfile(fullpath):
                    try:
                        with open(fullpath) as data_file:
                            data = json.load(data_file)
                            self.accounts[str(data['address']).lower()] = str(fullpath)
                    except (ValueError, KeyError, IOError) as ex:
                        # Invalid file - skip
                        if f.startswith("UTC--"):
                            # Should be a valid account file - warn user
                            msg = "Invalid account file"
                            if isinstance(ex, IOError):
                                msg = "Can not read account file"
                                raise ValueError(
                                    "{} {} {}".format(msg, fullpath, ex)
                                )

    def address_in_keystore(self, address):
        if address is None:
            return False

        if address.startswith('0x'):
            address = address[2:]

        return address.lower() in self.accounts

    def get_privkey(self, address, password=None):
        """Find the keystore file for an account, unlock it and get the private key

        :param str address: The Ethereum address for which to find the keyfile in the system
        :param str password: Mostly for testing purposes. A password can be provided
                             as the function argument here. If it's not then the
                             user is interactively queried for one.
        :return str: The private key associated with the address
        """

        if address.startswith('0x'):
            address = address[2:]

        address = address.lower()

        if not self.address_in_keystore(address):
            raise ValueError("Keystore file not found for %s" % address)

        with open(self.accounts[address]) as data_file:
            data = json.load(data_file)

        # Since file was found prompt for a password if not already given
        if password is None:
            password = getpass.getpass("Enter the password to unlock %s: " % address)
        acc = Account(data, password, self.accounts[address])
        return acc
