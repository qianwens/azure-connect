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
from halo import Halo

logger = get_logger(__name__)

DEFAULT_CLI = get_default_cli()


def download_source(url, location):
    spinner = Halo(text="[app] Downloading source code from: {0} ...".format(url),
                   spinner='dots', text_color='yellow', color='blue')
    spinner.start()
    _urlretrieve(url, location)
    spinner.succeed("[app] Downloaded source code from: {0}".format(url))


def push_repo(url, repo, app_name, source_folder):
    cwd = "./" + app_name + "/" + source_folder
    from os import path
    if path.isfile("./app.json"):
        cwd = "./" + source_folder
    _init_repo(cwd)
    args = ["push", "--set-upstream", url, repo, "-f"]
    _run_command(cwd, args)


def _init_repo(location):
    args = ["init"]
    _run_command(location, args)
    args = ["add", "*"]
    _run_command(location, args)
    args = ["commit", "-m", "first commit"]
    _run_command(location, args)


def _run_command(cwd, args):
    args = ["git"] + args
    str_print = ' '.join(args)
    str_print = (str_print[:75] + '..') if len(str_print) > 75 else str_print
    spinner = Halo(text=str_print,
                   spinner='dots', text_color='yellow', color='blue')
    spinner.start()
    env_kwargs = {}
    fnull = open(os.devnull, 'w')
    result = subprocess.call(args, env=dict(os.environ, **env_kwargs), cwd=cwd, stdout=fnull, stderr=subprocess.STDOUT)
    if result > 0:
        raise CLIError('Failed to perform {} operation.'.format(args[1]))
    spinner.succeed()

def _urlretrieve(url, location):
    import io
    req = urlopen(url)
    compressed_file = io.BytesIO(req.read())
    if url.endswith('zip'):
        with zipfile.ZipFile(compressed_file) as zip_ref:
            zip_ref.extractall(location)
    else:
        raise CLIError('Invalid downloading url {}'.format(url))
