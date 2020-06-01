import os
import requests


class CupertinoApi(object):
    def __init__(self):
        if os.environ['CONN_HOST'] is not None:
            self._host = os.environ['CONN_HOST']
        else:
            self._host = ''
        self._authtoken = ''

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

    def create(self, source, target, auth_info, additional_info=None):
        # TODO: if necessary call _prepare_db_authtoken
        # TODO: call self._put_connection and do error handling
        return
