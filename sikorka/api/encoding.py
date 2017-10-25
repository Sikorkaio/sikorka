from werkzeug.routing import (
    BaseConverter,
    ValidationError,
)
from sikorka.utils import (
    address_encoder
)


class HexAddressConverter(BaseConverter):
    def to_python(self, value):
        if value[:2] != '0x':
            raise ValidationError()

        try:
            value = value[2:].decode('hex')
        except TypeError:
            raise ValidationError()

        if len(value) != 20:
            raise ValidationError()

        return value

    def to_url(self, value):
        return address_encoder(value)
