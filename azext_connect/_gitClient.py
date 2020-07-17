# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from knack.prompting import prompt, prompt_y_n, prompt_choice_list, prompt_pass, NoTTYException
from azure.cli.command_modules.profile.custom import get_access_token
from azure.cli.core import get_default_cli
from azure.cli.core.commands.client_factory import get_subscription_id
import json
import random
import time
import subprocess
from getpass import getpass
import os
import platform
import datetime
import sys
import zipfile
import stat
from six.moves.urllib.parse import urlparse
from six.moves.urllib.request import urlopen  # pylint: disable=import-error

logger = get_logger(__name__)

DEFAULT_CLI = get_default_cli()


def download_source(url, location):
    _urlretrieve(url, location)


def pull_repo():

    pass


def push_repo():
    pass


def _urlretrieve(url, location):
    import io
    req = urlopen(url)
    compressed_file = io.BytesIO(req.read())
    if url.endswith('zip'):
        with zipfile.ZipFile(compressed_file) as zip_ref:
            zip_ref.extractall(location)
    else:
        raise CLIError('Invalid downloading url {}'.format(url))

