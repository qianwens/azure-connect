from enum import Enum


class AuthType(Enum):
    MSI = 'MSI'
    SP = 'SP'
    SECRET = 'Secret'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_
