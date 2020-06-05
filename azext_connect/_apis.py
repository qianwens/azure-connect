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

    def _put_connection(self, uri, data):
        headers = {
            'Authorization': 'Bearer {0}'.format(self._authtoken['accessToken']),
            'Content-Type': 'application/json'
        }
        # TODO: remove verify=False later. The localhost endpoint cert is not set. So set for workaround.
        res = requests.put(uri, headers=headers, data=json.dumps(data), verify=False)
        return res

    def create(self, subscription, rg, name, source, target, auth_info, additional_info=None):
        # TODO: call self._put_connection and do error handling
        uri = CupertinoApi.CONNECTION_URI.format(self._host, subscription, rg, name)
        self._put_connection(uri, {})
        return
