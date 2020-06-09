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
        self.credential = None
        if auth_type == AuthType.MSI:
            self.authType = 'SystemAssignedIdentity'
            self.permissions = permissions
        elif auth_type == AuthType.SP:
            self.auth_type = 'ServicePrincipal'
            self.credential = {
                'id': client_id,
                'secret': client_secret
            }
            self.permissions = permissions
        elif auth_type == AuthType.SECRET:
            self.auth_type = 'Secret'
            self.credential = {
                'id': user,
                'secret': pwd
            }
        else:
            raise Exception('Auth Type is not supported')
