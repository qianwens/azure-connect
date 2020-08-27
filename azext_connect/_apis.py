import json
import os
import requests
import urllib3


class CupertinoApi(object):

    CONNECTION_URI = '{0}/subscriptions/{1}/resourceGroups/{2}/providers/Microsoft.Cupertino/connections/{3}'
    VALIDATION_URI = '{0}/subscriptions/{1}/resourceGroups/{2}/providers/Microsoft.Cupertino/connections/{3}/validateConnectivity'
    GET_URI = '{0}/subscriptions/{1}/resourceGroups/{2}/providers/Microsoft.Cupertino/connections/{3}'

    def __init__(self, authtoken, graphtoken, sqltoken, mysqltoken):
        if 'LOCAL_CONN_HOST' in os.environ:
            self._host = os.environ['LOCAL_CONN_HOST']
        else:
            self._host = 'https://cupertinostaging.azurewebsites.net'
        self._authtoken = authtoken
        self._graphtoken = graphtoken
        self._sqltoken = sqltoken
        self._mysqltoken = mysqltoken
        # disable ssl warnings
        urllib3.disable_warnings()

    def _convert_auth_info(self, auth_info):
        from ._model import AuthType
        authInfo = None
        if auth_info:
            authInfo = {
                'authType': auth_info.auth_type,
                'permissions': auth_info.permissions,
                "id": auth_info.id if auth_info.auth_type == 'Secret' else None,
                "secret": auth_info.secret if auth_info.auth_type == 'Secret' else None
            }
        return authInfo

    def _make_headers(self):
        headers = {
            'Authorization': 'Bearer {0}'.format(self._authtoken['accessToken']),
            'GraphToken': 'Bearer {0}'.format(self._graphtoken['accessToken']),
            'SqlToken': 'Bearer {0}'.format(self._sqltoken['accessToken']),
            'MySqlToken': 'Bearer {0}'.format(self._mysqltoken['accessToken']),
            'Content-Type': 'application/json'
        }
        return headers

    def _put_connection(self, uri, data):
        headers = self._make_headers()
        # TODO: remove verify=False later. The localhost endpoint cert is not set. So set for workaround.
        data_string = json.dumps(data)
        res = requests.put(uri, headers=headers, data=data_string, verify=False)
        return res

    def _post_connection(self, uri, data):
        headers = self._make_headers()
        # TODO: remove verify=False later. The localhost endpoint cert is not set. So set for workaround.
        data_string = json.dumps(data)
        res = requests.post(uri, headers=headers, data=data_string, verify=False)
        return res

    def _get_connection(self, uri, data):
        headers = self._make_headers()
        # TODO: remove verify=False later. The localhost endpoint cert is not set. So set for workaround.
        data_string = json.dumps(data)
        res = requests.get(uri, headers=headers, data=data_string, verify=False)
        return res

    def create(self, subscription, rg, name, source, target, auth_info, additional_info=None):
        # TODO: call self._put_connection and do error handling
        uri = CupertinoApi.CONNECTION_URI.format(self._host, subscription, rg, name)
        properties = {
            'sourceId': source,
            'targetId': target,
            'authInfo': self._convert_auth_info(auth_info),
            'additionalInfo': additional_info
        }
        data = {
            'name': name,
            'properties': properties
        }
        res = self._put_connection(uri, data)
        return res

    def validate(self, subscription, rg, name):
        uri = CupertinoApi.VALIDATION_URI.format(self._host, subscription, rg, name)
        properties = {
        }
        data = {
            'name': name,
            'properties': properties
        }
        res = self._post_connection(uri, data)
        return res

    def get(self, subscription, rg, name):
        uri = CupertinoApi.GET_URI.format(self._host, subscription, rg, name)
        properties = {
        }
        data = {
            'name': name,
            'properties': properties
        }
        res = self._get_connection(uri, data)
        return res
