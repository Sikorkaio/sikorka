import time
import select
from bluetooth import (
    BluetoothSocket,
    BluetoothError,
    RFCOMM,
    PORT_ANY,
    SERIAL_PORT_CLASS,
    SERIAL_PORT_PROFILE,
    advertise_service,
)


def run_bt_server(end_event, device_name, account):
    """Adapted from: https://github.com/EnableTech/raspberry-bluetooth-demo"""
    server_sock = BluetoothSocket(RFCOMM)

    server_sock.bind(("", PORT_ANY))
    server_sock.listen(1)

    port = server_sock.getsockname()[1]
    print ("listening on port %d" % port)

    uuid = "1e0ca4ea-299d-4335-93eb-27fcfe7fa848"
    try:
        advertise_service(
            server_sock,
            device_name,
            service_id=uuid,
            service_classes=[uuid, SERIAL_PORT_CLASS],
            profiles=[SERIAL_PORT_PROFILE],
            # protocols=[OBEX_UUID],
        )
    except BluetoothError as e:
        print(
            'ERROR: Bluetooth Error:{}.\n Quiting bluetooth server. Is your '
            'bluetooth setup correctly? Do you have sudo privileges?'.format(e)
        )
        return

    print("Waiting for connection on RFCOMM channel %d" % port)

    client_sock, client_info = server_sock.accept()
    print("Accepted connection from ", client_info)
    client_sock.setblocking(0)

    bufferdata = bytearray()
    try:
        while not end_event.is_set():
            ready = select.select([client_sock], [], [], 5)
            if not ready[0]:
                break
            data = client_sock.recv(1024)
            if len(data) == 0:
                break
            print("received [%s]" % data)
            bufferdata = bufferdata + data
            print(bufferdata)
            try:
                end = bufferdata.index(b'\n')
                our_data = bufferdata[0:end].strip(b'\r')
                if len(bufferdata) > end:
                    bufferdata = bufferdata[end + 1:]
                else:
                    bufferdata = bytearray()
                bluetooth_process(our_data, client_sock, account)
            except ValueError:
                pass

    except IOError:
        pass
    print("bluetooth server disconnected")

    client_sock.close()
    server_sock.close()
    print("all done")


def bluetooth_process(data, client_sock, account):
    if data == b'ETH_ADDRESS':
        client_sock.send(
            "ETH_ADDRESS::0x{}\r\nEND\r\n".format(account.address())
        )
    elif data.startswith(b'SIGNED_MESSAGE::'):
        start = len('SIGNED_MESSAGE::')
        user_address = data[start:start + 42]
        message = account.create_signed_message(
            user_address,
            int(time.time())
        )
        client_sock.send(message)
    elif data.startswith('AUTHORIZE_USER::'):
        start = len('AUTHORIZE_USER::')
        user_address = data[start:start + 42]
        # TODO Add a blockchain transaction here to authorize the user
