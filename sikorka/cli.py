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
from sikorka.btserver import run_bt_server
from sikorka.qrcodes import generate_qr_codes


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
    click.option(
        '--rpc/--no-rpc',
        default=True,
        help='Turn the Rest API rpc on/off'
    ),
    click.option(
        '--bluetooth-server/--no-bluetooth-server',
        default=False,
        help='Turn the Bluetooth server API on/off'
    ),
    click.option(
        '--qrcodes/--no-qrcodes',
        default=False,
        help='Run a simple webserver generating signed timed QR codes'
    ),
    click.option(
        '--bluetooth-device-name',
        default='Mock Detector',
        help='Device name for bluetooth server'
    )
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
def run(ctx, rpc, bluetooth_server, qrcodes, **kwargs):
    if ctx.invoked_subcommand is None:
        print('Sikorka desktop client, version {}!'.format(SIKORKA_VERSION))

        end_event = gevent.event.Event()
        sikorka_app = ctx.invoke(app, **kwargs)
        sikorka_api = RestAPI(sikorka_app)
        if rpc:
            sikorka_rest_server = APIServer(
                rest_api=sikorka_api,
                cors_domain_list=None,
                eth_rpc_endpoint=kwargs['eth_rpc_endpoint'],
                webui=qrcodes,
            )
            sikorka_rest_server.start('localhost', kwargs['api_port'])

        if bluetooth_server:
            bt_server = gevent.spawn(
                run_bt_server,
                end_event,
                kwargs['bluetooth_device_name'],
                sikorka_app.account
            )

        if qrcodes:
            qrcodes_greenlet = gevent.spawn(
                generate_qr_codes,
                end_event,
                sikorka_app.account
            )

        # wait for interrupt
        gevent.signal(signal.SIGQUIT, end_event.set)
        gevent.signal(signal.SIGTERM, end_event.set)
        gevent.signal(signal.SIGINT, end_event.set)
        end_event.wait()

        if bluetooth_server:
            bt_server.join()

        if qrcodes:
            qrcodes_greenlet.join()

        if rpc:
            sikorka_rest_server.stop()
