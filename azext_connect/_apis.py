import os
import requests
from azure.cli.core import get_default_cli


class CupertinoApi(object):
    def __init__(self, authtoken, graphtoken, sqltoken, mysqltoken):
        if 'CONN_HOST' in os.environ:
            self._host = os.environ['CONN_HOST']
        else:
            self._host = ''
        self._authtoken = authtoken
        self._graphtoken = graphtoken
        self._sqltoken = sqltoken
        self._mysqltoken = mysqltoken

    def _get_authtoken(self):
        return

    def _get_graphtoken(self):
        return

    def _prepare_db_authtoken(self):
        self._db_authtoken = ''
        return

    def _put_connection(self, data):
        uri = self._host  # get the connection endpoint
        headers = {
            'Authorization': self._authtoken,
            'Content-Type': 'application/json'
        }
        res = requests.put(uri, headers=headers, data=data)
        return res

    def create(self, name, source, target, auth_info, additional_info=None):
        # TODO: call self._put_connection and do error handling
        return
