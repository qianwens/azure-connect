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
        self, auth_type, permissions=[], client_id=None,
        client_secret=None, user=None, pwd=None
    ):
        self.permissions = None
        if auth_type == AuthType.MSI:
            self.auth_type = 'SystemAssignedIdentity'
            self.permissions = permissions
        elif auth_type == AuthType.SP:
            self.auth_type = 'ServicePrincipal'
            self.id = client_id
            self.secret = client_secret
            self.permissions = permissions
        elif auth_type == AuthType.SECRET:
            self.auth_type = 'Secret'
            self.id = user
            self.secret = pwd
        else:
            raise Exception('Auth Type is not supported')
