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


def mk_build_dir(name, app_name):
    import pkgutil
    data = pkgutil.get_data(__name__, "docker/" + name + "/dockerfile")
    docker_path = "./" + app_name + "/docker"
    from os import path
    if path.isfile("./app.json"):
        docker_path = "./docker"
    if not os.path.isdir(docker_path):
        os.mkdir(docker_path)
    with open(docker_path + "/dockerfile", 'w') as outfile:
        outfile.write(data.decode())
    return docker_path


def _run_command(cwd, args):
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

