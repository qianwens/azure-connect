import json
import os
import requests


class CupertinoApi(object):

    CONNECTION_URI = '{0}/subscriptions/{1}/resourceGroups/{2}/providers/Microsoft.Cupertino/connections/{3}'

    def __init__(self, authtoken, graphtoken, sqltoken, mysqltoken):
        if 'CONN_HOST' in os.environ:
            self._host = os.environ['CONN_HOST']
        else:
            self._host = 'https://localhost:44345'
        self._authtoken = authtoken
        self._graphtoken = graphtoken
        self._sqltoken = sqltoken
        self._mysqltoken = mysqltoken

    def _convert_auth_info(self, auth_info):
        authInfo = None
        if auth_info:
            authInfo = {
                'authType': auth_info.auth_type,
                'permissions': auth_info.permissions,
                'credential': auth_info.credential
            }
        return authInfo

    def _populate_tokens(self, additional_info=None):
        if not additional_info:
            additional_info = {}
        return additional_info

    def _put_connection(self, uri, data):
        headers = {
            'Authorization': 'Bearer {0}'.format(self._authtoken['accessToken']),
            'GraphToken': 'Bearer {0}'.format(self._graphtoken['accessToken']),
            'SqlToken': 'Bearer {0}'.format(self._sqltoken['accessToken']),
            'MySqlToken': 'Bearer {0}'.format(self._mysqltoken['accessToken']),
            'Content-Type': 'application/json'
        }
        # TODO: remove verify=False later. The localhost endpoint cert is not set. So set for workaround.
        data_string = json.dumps(data)
        res = requests.put(uri, headers=headers, data=data_string, verify=False)
        return res

    def create(self, subscription, rg, name, source, target, auth_info, additional_info=None):
        # TODO: call self._put_connection and do error handling
        uri = CupertinoApi.CONNECTION_URI.format(self._host, subscription, rg, name)
        properties = {
            'sourceId': source,
            'targetId': target,
            'authInfo': self._convert_auth_info(auth_info),
            'additionalInfo': self._populate_tokens(additional_info)
        }
        data = {
            'name': name,
            'properties': properties
        }
        res = self._put_connection(uri, data)
        return res
