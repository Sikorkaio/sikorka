# A lot of the code here is taken from pyetherem/pyethapp and raiden

# -*- coding: utf-8 -*-
import getpass
import json
import os
import sys
import random
import pbkdf2
from py_ecc.secp256k1 import privtopub, ecdsa_raw_sign, ecdsa_raw_recover

from utils import encode_hex, decode_hex

try:
    scrypt = __import__('scrypt')
except ImportError:
    sys.stderr.write("""
Failed to import scrypt. This is not a fatal error but does
mean that you cannot create or decrypt privkey jsons that use
scrypt

""")
    scrypt = None
try:
    import bitcoin
except ImportError:
    sys.stderr.write("""
Failed to import bitcoin. This is not a fatal error but does
mean that you will not be able to determine the address from
your wallet file.
""")
import binascii
import struct
from math import ceil
from Crypto.Hash import keccak
sha3_256 = lambda x: keccak.new(digest_bits=256, data=x)
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Util import Counter

# TODO: make it compatible!


SCRYPT_CONSTANTS = {
    "n": 262144,
    "r": 1,
    "p": 8,
    "dklen": 32
}

PBKDF2_CONSTANTS = {
    "prf": "hmac-sha256",
    "dklen": 32,
    "c": 262144
}


def aes_ctr_encrypt(text, key, params):
    iv = big_endian_to_int(decode_hex(params["iv"]))
    ctr = Counter.new(128, initial_value=iv, allow_wraparound=True)
    mode = AES.MODE_CTR
    encryptor = AES.new(key, mode, counter=ctr)
    return encryptor.encrypt(text)


def aes_ctr_decrypt(text, key, params):
    iv = big_endian_to_int(decode_hex(params["iv"]))
    ctr = Counter.new(128, initial_value=iv, allow_wraparound=True)
    mode = AES.MODE_CTR
    encryptor = AES.new(key, mode, counter=ctr)
    return encryptor.decrypt(text)


def aes_mkparams():
    return {"iv": encode_hex(os.urandom(16))}


ciphers = {
    "aes-128-ctr": {
        "encrypt": aes_ctr_encrypt,
        "decrypt": aes_ctr_decrypt,
        "mkparams": aes_mkparams
    }
}


def mk_scrypt_params():
    params = SCRYPT_CONSTANTS.copy()
    params['salt'] = encode_hex(os.urandom(16))
    return params


def scrypt_hash(val, params):
    return scrypt.hash(str(val), decode_hex(params["salt"]), params["n"],
                       params["r"], params["p"], params["dklen"])


def mk_pbkdf2_params():
    params = PBKDF2_CONSTANTS.copy()
    params['salt'] = encode_hex(os.urandom(16))
    return params


def pbkdf2_hash(val, params):
    assert params["prf"] == "hmac-sha256"
    return pbkdf2.PBKDF2(val, decode_hex(params["salt"]), params["c"],
                         SHA256).read(params["dklen"])


kdfs = {
    "pbkdf2": {
        "calc": pbkdf2_hash,
        "mkparams": mk_pbkdf2_params
    }
}

if scrypt is not None:
    kdfs["scrypt"] = {
        "calc": scrypt_hash,
        "mkparams": mk_scrypt_params
    }


def make_keystore_json(priv, pw, kdf="pbkdf2", cipher="aes-128-ctr"):
    # Get the hash function and default parameters
    if kdf not in kdfs:
        raise Exception("Hash algo %s not supported" % kdf)
    kdfeval = kdfs[kdf]["calc"]
    kdfparams = kdfs[kdf]["mkparams"]()
    # Compute derived key
    derivedkey = kdfeval(pw, kdfparams)
    # Get the cipher and default parameters
    if cipher not in ciphers:
        raise Exception("Encryption algo %s not supported" % cipher)
    encrypt = ciphers[cipher]["encrypt"]
    cipherparams = ciphers[cipher]["mkparams"]()
    # Produce the encryption key and encrypt
    enckey = derivedkey[:16]
    c = encrypt(priv, enckey, cipherparams)
    # Compute the MAC
    mac = sha3(derivedkey[16:32] + c)
    # Make a UUID
    u = encode_hex(os.urandom(16))
    uuid = b'-'.join((u[:8], u[8:12], u[12:16], u[16:20], u[20:]))
    # Return the keystore json
    return {
        "crypto": {
            "cipher": cipher,
            "ciphertext": encode_hex(c),
            "cipherparams": cipherparams,
            "kdf": kdf,
            "kdfparams": kdfparams,
            "mac": encode_hex(mac),
            "version": 1
        },
        "id": uuid,
        "version": 3
    }


def check_keystore_json(jsondata):
    """Check if ``jsondata`` has the structure of a keystore file version 3.

    Note that this test is not complete, e.g. it doesn't check key derivation or cipher parameters.

    :param jsondata: dictionary containing the data from the json file
    :returns: `True` if the data appears to be valid, otherwise `False`
    """
    if 'crypto' not in jsondata and 'Crypto' not in jsondata:
        return False
    if 'version' not in jsondata:
        return False
    if jsondata['version'] != 3:
        return False
    crypto = jsondata.get('crypto', jsondata.get('Crypto'))
    if 'cipher' not in crypto:
        return False
    if 'ciphertext' not in crypto:
        return False
    if 'kdf' not in crypto:
        return False
    if 'mac' not in crypto:
        return False
    return True


def decode_keystore_json(jsondata, pw):
    # Get KDF function and parameters
    if "crypto" in jsondata:
        cryptdata = jsondata["crypto"]
    elif "Crypto" in jsondata:
        cryptdata = jsondata["Crypto"]
    else:
        raise Exception("JSON data must contain \"crypto\" object")
    kdfparams = cryptdata["kdfparams"]
    kdf = cryptdata["kdf"]
    if cryptdata["kdf"] not in kdfs:
        raise Exception("Hash algo %s not supported" % kdf)
    kdfeval = kdfs[kdf]["calc"]
    # Get cipher and parameters
    cipherparams = cryptdata["cipherparams"]
    cipher = cryptdata["cipher"]
    if cryptdata["cipher"] not in ciphers:
        raise Exception("Encryption algo %s not supported" % cipher)
    decrypt = ciphers[cipher]["decrypt"]
    # Compute the derived key
    derivedkey = kdfeval(pw, kdfparams)
    assert len(derivedkey) >= 32, \
        "Derived key must be at least 32 bytes long"
    # print(b'derivedkey: ' + encode_hex(derivedkey))
    enckey = derivedkey[:16]
    # print(b'enckey: ' + encode_hex(enckey))
    ctext = decode_hex(cryptdata["ciphertext"])
    # Decrypt the ciphertext
    o = decrypt(ctext, enckey, cipherparams)
    # Compare the provided MAC with a locally computed MAC
    # print(b'macdata: ' + encode_hex(derivedkey[16:32] + ctext))
    mac1 = sha3(derivedkey[16:32] + ctext)
    mac2 = decode_hex(cryptdata["mac"])
    if mac1 != mac2:
        raise ValueError("MAC mismatch. Password incorrect?")
    return o


def mk_random_privkey():
    k = hex(random.getrandbits(256))[2:-1].zfill(64)
    assert len(k) == 64
    return k.decode('hex')


class Account(object):

    """Represents an account.

    :ivar keystore: the key store as a dictionary (as decoded from json)
    :ivar locked: `True` if the account is locked and neither private nor public keys can be
                  accessed, otherwise `False`
    :ivar path: absolute path to the associated keystore file (`None` for in-memory accounts)
    """

    def __init__(self, keystore, password=None, path=None):
        self.keystore = keystore
        try:
            self._address = self.keystore['address'].decode('hex')
        except KeyError:
            self._address = None
        self.locked = True
        if password is not None:
            self.unlock(password)
        if path is not None:
            self.path = os.path.abspath(path)
        else:
            self.path = None

    @classmethod
    def new(cls, password, key=None, uuid=None, path=None):
        """Create a new account.

        Note that this creates the account in memory and does not store it on disk.

        :param password: the password used to encrypt the private key
        :param key: the private key, or `None` to generate a random one
        :param uuid: an optional id
        """
        if key is None:
            key = mk_random_privkey()
        keystore = make_keystore_json(key, password)
        keystore['id'] = uuid
        return Account(keystore, password, path)

    @classmethod
    def load(cls, path, password=None):
        """Load an account from a keystore file.

        :param path: full path to the keyfile
        :param password: the password to decrypt the key file or `None` to leave it encrypted
        """
        with open(path) as f:
            keystore = json.load(f)
        if not check_keystore_json(keystore):
            raise ValueError('Invalid keystore file')
        return Account(keystore, password, path=path)

    def dump(self, include_address=True, include_id=True):
        """Dump the keystore for later disk storage.

        The result inherits the entries `'crypto'` and `'version`' from `account.keystore`, and
        adds `'address'` and `'id'` in accordance with the parameters `'include_address'` and
        `'include_id`'.

        If address or id are not known, they are not added, even if requested.

        :param include_address: flag denoting if the address should be included or not
        :param include_id: flag denoting if the id should be included or not
        """
        d = {}
        d['crypto'] = self.keystore['crypto']
        d['version'] = self.keystore['version']
        if include_address and self.address is not None:
            d['address'] = self.address.encode('hex')
        if include_id and self.uuid is not None:
            d['id'] = self.uuid
        return json.dumps(d)

    def unlock(self, password):
        """Unlock the account with a password.

        If the account is already unlocked, nothing happens, even if the password is wrong.

        :raises: :exc:`ValueError` (originating in ethereum.keys) if the password is wrong (and the
                 account is locked)
        """
        if self.locked:
            self._privkey = decode_keystore_json(self.keystore, password)
            self.locked = False
            self.address  # get address such that it stays accessible after a subsequent lock

    def lock(self):
        """Relock an unlocked account.

        This method sets `account.privkey` to `None` (unlike `account.address` which is preserved).
        After calling this method, both `account.privkey` and `account.pubkey` are `None.
        `account.address` stays unchanged, even if it has been derived from the private key.
        """
        self._privkey = None
        self.locked = True

    @property
    def privkey(self):
        """The account's private key or `None` if the account is locked"""
        if not self.locked:
            return self._privkey
        else:
            return None

    @property
    def pubkey(self):
        """The account's public key or `None` if the account is locked"""
        if not self.locked:
            return privtopub(self.privkey)
        else:
            return None

    @property
    def address(self):
        """The account's address or `None` if the address is not stored in the key file and cannot
        be reconstructed (because the account is locked)
        """
        if self._address:
            pass
        elif 'address' in self.keystore:
            self._address = self.keystore['address'].decode('hex')
        elif not self.locked:
            self._address = privtoaddr(self.privkey)
        else:
            return None
        return self._address

    @property
    def uuid(self):
        """An optional unique identifier, formatted according to UUID version 4, or `None` if the
        account does not have an id
        """
        try:
            return self.keystore['id']
        except KeyError:
            return None

    @uuid.setter
    def uuid(self, value):
        """Set the UUID. Set it to `None` in order to remove it."""
        if value is not None:
            self.keystore['id'] = value
        elif 'id' in self.keystore:
            self.keystore.pop('id')

    def sign_tx(self, tx):
        """Sign a Transaction with the private key of this account.

        If the account is unlocked, this is equivalent to ``tx.sign(account.privkey)``.

        :param tx: the :class:`ethereum.transactions.Transaction` to sign
        :raises: :exc:`ValueError` if the account is locked
        """
        if self.privkey:
            tx.sign(self.privkey)
        else:
            raise ValueError('Locked account cannot sign tx')

    def __repr__(self):
        if self.address is not None:
            address = self.address.encode('hex')
        else:
            address = '?'
        return '<Account(address={address}, id={id})>'.format(address=address, id=self.uuid)


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
        return acc.privkey


def normalize_key(key):
    if is_numeric(key):
        o = encode_int32(key)
    elif len(key) == 32:
        o = key
    elif len(key) == 64:
        o = decode_hex(key)
    elif len(key) == 66 and key[:2] == '0x':
        o = decode_hex(key[2:])
    else:
        raise Exception("Invalid key format: %r" % key)
    if o == b'\x00' * 32:
        raise Exception("Zero privkey invalid")
    return o


def privtoaddr(k):
    k = normalize_key(k)
    x, y = privtopub(k)
    return sha3(encode_int32(x) + encode_int32(y))[12:]


def sha3(seed):
    return sha3_256(seed).digest()


def zpad(x, l):
    """ Left zero pad value `x` at least to length `l`.

    >>> zpad('', 1)
    '\x00'
    >>> zpad('\xca\xfe', 4)
    '\x00\x00\xca\xfe'
    >>> zpad('\xff', 1)
    '\xff'
    >>> zpad('\xca\xfe', 2)
    '\xca\xfe'
    """
    return b'\x00' * max(0, l - len(x)) + x


if sys.version_info.major == 2:

    def int_to_big_endian(value):
        cs = []
        while value > 0:
            cs.append(chr(value % 256))
            value /= 256
        s = ''.join(reversed(cs))
        return s

    def big_endian_to_int(value):
        if len(value) == 1:
            return ord(value)
        elif len(value) <= 8:
            return struct.unpack('>Q', value.rjust(8, b'\x00'))[0]
        else:
            return int(encode_hex(value), 16)

    is_numeric = lambda x: isinstance(x, (int, long))

    def encode_int32(v):
        return zpad(int_to_big_endian(v), 32)


if sys.version_info.major == 3:

    def int_to_big_endian(value):
        byte_length = ceil(value.bit_length() // 8)
        return (value).to_bytes(byte_length, byteorder='big')

    def big_endian_to_int(value):
        return int.from_bytes(value, byteorder='big')

    is_numeric = lambda x: isinstance(x, int)

    def encode_int32(v):
        return v.to_bytes(32, byteorder='big')
