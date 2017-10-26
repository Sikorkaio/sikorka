import gevent
import gevent.monkey
gevent.monkey.patch_all()
import sys
import click
import signal

from sikorka.utils import address_decoder, address_encoder
from sikorka.accounts import AccountManager, Account
from sikorka.service import Sikorka
from sikorka.api.rest import APIServer
from sikorka.api.api import RestAPI


SIKORKA_VERSION = '0.0.1'


class AddressType(click.ParamType):
    name = 'address'

    def convert(self, value, param, ctx):
        try:
            return address_decoder(value)
        except:
            self.fail('Please specify a valid hex-encoded address.')


ADDRESS_TYPE = AddressType()

OPTIONS = [
    click.option(
        '--address',
        help=(
            'The ethereum address you would like sikorka to use and for which '
            'a keystore file exists in your local system.'),
        default=None,
        type=ADDRESS_TYPE,
    ),
    click.option(
        '--keystore-path',
        help=(
            'If you have a non-standard path for the ethereum keystore '
            'directory provide it using this argument.'),
        default=None,
        type=click.Path(exists=True),
    ),
    click.option(
        '--eth-rpc-endpoint',
        help='"host:port" address of ethereum JSON-RPC server.\n Also'
        ' accepts a protocol prefix (http:// or https://) with optional port',
        default='127.0.0.1:8545',  # geth default jsonrpc port
        type=str,
    ),
    click.option(
        '--keyfile',
        help='path to a particular keyfile to use',
        type=click.Path(exists=True),
    ),
    click.option(
        '--passfile',
        help='path to a particular file containing a password to use for the key',
        type=click.Path(exists=True),
    ),
    click.option(
        '--api-port',
        help='Sikorka api port',
        default=5011,
        type=int,
    ),
]


def options(func):
    """Having the common app options as a decorator facilitates reuse.
    """
    for option in OPTIONS:
        func = option(func)
    return func


def prompt_account(address_hex, keystore_path, password_file):
    accmgr = AccountManager(keystore_path)
    if not accmgr.accounts:
        raise RuntimeError('No Ethereum accounts found in the user\'s system')

    if not accmgr.address_in_keystore(address_hex):
        addresses = list(accmgr.accounts.keys())
        formatted_addresses = [
            '[{:3d}] - 0x{}'.format(idx, addr)
            for idx, addr in enumerate(addresses)
        ]

        should_prompt = True

        print('The following accounts were found in your machine:')
        print('')
        print('\n'.join(formatted_addresses))
        print('')

        while should_prompt:
            idx = click.prompt(
                'Select one of them by index to continue', type=int
            )

            if idx >= 0 and idx < len(addresses):
                should_prompt = False
            else:
                print("\nError: Provided index '{}' is out of bounds\n".format(
                    idx)
                )

        address_hex = addresses[idx]

    password = None
    if password_file:
        password = password_file.read().splitlines()[0]
    if password:
        try:
            unlocked_account = accmgr.get_privkey(address_hex, password)
        except ValueError:
            # ValueError exception raised if the password is incorrect
            print('Incorrect password for {} in file. Aborting ...'.format(
                address_hex)
            )
            sys.exit(1)
    else:
        unlock_tries = 3
        while True:
            try:
                unlocked_account = accmgr.get_privkey(address_hex)
                break
            except ValueError:
                # ValueError exception raised if the password is incorrect
                if unlock_tries == 0:
                    print(
                        'Exhausted passphrase unlock attempts for {}. Aborting'
                        ' ...'.format(address_hex)
                    )
                    sys.exit(1)

                print(
                    'Incorrect passphrase to unlock the private key. {} tries '
                    'remaining. Please try again or kill the process to quit. '
                    'Usually Ctrl-c.'.format(unlock_tries)
                )
                unlock_tries -= 1

    return unlocked_account


@options
@click.command()
def app(address, eth_rpc_endpoint, keystore_path, keyfile, passfile, **kwargs):
    address_hex = address_encoder(address) if address else None
    if keyfile is not None and passfile is not None:
        unlocked_account = Account(keyfile, passfile)
    else:
        unlocked_account = prompt_account(address_hex, keystore_path, passfile)
    sikorka = Sikorka(eth_rpc_endpoint, unlocked_account)
    return sikorka


@click.group(invoke_without_command=True)
@options
@click.pass_context
def run(ctx, **kwargs):
    if ctx.invoked_subcommand is None:
        print('Sikorka desktop client, version {}!'.format(SIKORKA_VERSION))

        # import pdb
        # pdb.set_trace()
        sikorka_app = ctx.invoke(app, **kwargs)
        sikorka_api = RestAPI(sikorka_app)
        sikorka_rest_server = APIServer(sikorka_api, None, kwargs['eth_rpc_endpoint'])
        sikorka_rest_server.start('localhost', kwargs['api_port'])
        # wait for interrupt
        event = gevent.event.Event()
        gevent.signal(signal.SIGQUIT, event.set)
        gevent.signal(signal.SIGTERM, event.set)
        gevent.signal(signal.SIGINT, event.set)
        event.wait()

        # Here put the eventual app shutdown process
        sikorka_rest_server.stop()
