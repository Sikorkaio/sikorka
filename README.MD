# Sikorka App and smart contracts

This repository contains a desktop app and the smart contracts for the [Sikorka](http://sikorka.io/) project.

## Sikorka app


### Installation

Create a virtualenvironment and do `pip install -e .`

Then you can call the sikorka executable via `sikorka`. For a list of all commands
write `sikorka --help`.

### Rest API

Sikorka runs a rest api server underneath so that users can communicate with it. The Rest API server is on by default.

Assuming a server running on localhost on port 5011 we have the following endpoints:

#### Get address associated with the client

Use a `GET http://localhost:5011/api/1/address` to get the address associated with the client.

#### Request signed detector message

Use `GET http://localhost:5011/api/1/detector_sign/0x8bed7fd11ef2efa1899f751a8d422c1fd028610c`

where you should replace `0x8bed7fd11ef2efa1899f751a8d422c1fd028610c` with the address of the user you want to get a detector signed message for.

### Running A Bluetooth Server

Sikorka can also run a bluetooth server with its own API.

Add the argument `--bluetooth-server`.

We need a Bluetooth enabled linux system with python 3.

Make sure bluetooth is activated and running -- guide may vary depending on your system -- for Arch check [here](https://wiki.archlinux.org/index.php/Bluetooth).

```
systemctl start bluetooth.service
```

If things don't work check this SO answer: https://stackoverflow.com/questions/33110992/python-code-for-bluetooth-throws-error-after-i-had-to-reset-the-adapter

Make sure your device is up:

```
sudo hciconfig hci0 piscan
```

If the above gives you any errors, then make the interface go up by

```
sudo hciconfig hci0 up
```

Then provide a unique name for the device.

```
sudo hciconfig hci0 name 'Mock Detector'
```

Also run sikorka with sudo if it is required to access bluetooth.

### Bluetooth API

The bluetooth server API is very simple and text based.

#### Getting address associated with the client via bluetooth

Connect and send `ETH_ADDRESS` followed by a newline.

#### Request detector sign via bluetooth

Connect and send `SIGNED_MESSAGE::0x8bed7fd11ef2efa1899f751a8d422c1fd028610c` where you should replace `0x8bed7fd11ef2efa1899f751a8d422c1fd028610c` with the user address you want the sign for. Always end with newline.

## Testing

In order to run the tests we use [populus](https://github.com/pipermerriam/populus), a python framework for testing smart contracts.

- [Create](http://docs.python-guide.org/en/latest/dev/virtualenvs/) a python virtual environment and activate it.

- Run `pip install -r requirements.txt`

- And now from the root directory run the tests by `pytest tests/ --populus-project .`

## Smart Contracts

The repository contains the following contracts:

### SikorkaBasicInterface

The SikorkaBasicInterface is the interface that all Sikorka compliant contracts should implement. It contains functions that allow the contract to interace with the real world via the use of hardware detectors.

When a sikorka contract is deployed it must be linked with a detector provided at construction time.

The detector is a piece of hardware deployed at the location that can verify the presence of the user at the location for a specific amount of time. There are two ways that the detector interfaces with the contract.

#### Direct Detector Interface

The direct method via which the detector can interface with the contract is by sending a transaction to the contract authorizing a user for a specific period of time.

This is done by calling `authorize_user()` and providing the address of the user and the period of time he is authorized to access the contract.

Then finally the user is able to call the functions of the contract that need authorization as long as it's within the time frame provided by the detector.

#### Indirect Detector Interface

The indirect method via which the detector can interface with the contract is by signing a message containing the `address` of the user, the `timestamp` at which the user was authorized and the `duration` for which he was authorized.

The user then submits this message as proof to the contract with each interaction and the contract recovers the signee's address, compares it to the registered detector and if all is well authorizes the user.

Then as with the direct method the user can interact with the contract for the duration of the authorization.

### SikorkaRegistry

The SikorkaRegistry is a registry contract containing the addresses of all Sikorka enabled contracts. When a new sikorka contract is deployed it should be added in the registry along with its latitude and longitude.

Sikorka applications can get the list of contracts from there, insert them into appropriate data structures and search them.

### Trigonometry

Trigonometry is a basic library for offering the functionality of basic trigonometry functions with both input and output being integer approximated and with the use of a lookup table of the first quadrant of `sin(x)` and of first order linear interpolation.

The algorithm can be seen [here](http://web.archive.org/web/20120301144605/http://www.dattalo.com/technical/software/pic/picsine.html) along with sourcecode for the PIC microcontroller.

The degrees found in a circle are approximated by an integer with `N` bits. Thus for
example if `N` is 14 a circle can have 16384 angle units. A lookup table of `Y` values
of the `sin()` function is created but those values are transformed from the range of [-1.0, 1.0] to [-(N+1 bits), (N+1 bits)] number. So if `N` was 14 then the range here would be [-32767, 32767].

Assuming N=14 we will have a bit layout in the given number like this:

QQTTTT IIIIIIII

- `QQ`       -> Quadrant. 00 = quadrant 1, 01 = quadrant 2, etc.
- `TTTT`     -> Index into the `sin(x)` lookup table
- `IIIIIIII` -> Interpolation between successsive entries in the table

For more details on the algorithm visit either the [C implementation page](http://www.dribin.org/dave/trigint/) or the [PIC implementation](http://web.archive.org/web/20120301144605/http://www.dattalo.com/technical/software/pic/picsine.html).

#### Input/Output Transformation

Depending on the chosen N for the angles in a circle you want to transform your input degrees with following:

```
input_angle_int = (degrees * ANGLES_PER_CYCLE) / 360.0
```

Also in order to transform your sin/cos output to the usual [-1.0, 1.0] range you can
use the following, assuming `AMPLITUDE` is the amplitude range by which the lookup table was created.

```
result = return_value * (1.0 / AMPLITUDE)
```

Examples of all the above and functions to accomplish them can be seen in `test_trigonometry.py`

#### Generating the contract

Inside the repository there is already an implementation where N=14, and the angles
in a circle are 16384.

The script `generate_trigonometry.py` allows you to set those parameters and will edit the solidity library for you in order to adjust for the new parameters. Due to gas
constraints on the lookup table the maximum number of bits at the moment is 32.

The maximum error rate is as follows depending on the number of bits.

| Bits     |    Error Rate   |
|----------|:---------------:|
| 16       |  0.001251258889 |
| 32       |  0.000004693866 |

### SikorkaBasicInterface

The Basic Interface for Sikorka Smart contracts. TODO: More details.
