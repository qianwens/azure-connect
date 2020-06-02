from enum import Enum


class AuthType(Enum):
    MSI = 'MSI'
    SP = 'SP'
    SECRET = 'Secret'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_  # pylint: disable=no-member


class AuthInfo():
    def __init__(
        self, auth_type, permission=None, client_id=None,
        client_secret=None, user=None, pwd=None
    ):
        if auth_type == AuthType.MSI:
            self.auth_type = auth_type
            self.permission = permission
        elif auth_type == AuthType.SP:
            self.auth_type = auth_type
            self.client_id = client_id
            self.client_secret = client_secret
            self.permission = permission
        elif auth_type == AuthType.SECRET:
            self.auth_type = auth_type
            self.user = user
            self.pwd = pwd
        else:
            raise Exception('Auth Type is not supported')
