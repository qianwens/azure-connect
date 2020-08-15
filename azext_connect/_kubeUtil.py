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


def create_docker_registry_secret(secret_name, server, username, pwd):
    args = ['kubectl', 'delete', 'secret', secret_name]
    _run_command_silent('.', args)
    args = ['kubectl', 'create', 'secret', 'docker-registry', secret_name, '--docker-server', server,
            '--docker-username', username, '--docker-password', pwd]
    _run_command_silent('.', args)


def create_secret(secret_name, secrets):
    args = ['kubectl', 'delete', 'secret', secret_name]
    _run_command_silent('.', args)
    secret_format = '--from-literal={}={}'
    args = ['kubectl', 'create', 'secret', 'generic', secret_name]
    for secret in secrets:
        key, value = secret
        args.append(secret_format.format(key, value))
    _run_command_silent('.', args)


def helm_install(release_name, repo, chart, settings):
    args = ['helm', 'repo', 'add', 'bitnami', repo]
    _run_command_silent('.', args)
    args = ['helm', 'install', release_name, chart]
    for setting in settings:
        key, value = setting
        args.append('--set')
        args.append(key + '=' + value)
    _run_command('.', args)


def _run_command(cwd, args):
    env_kwargs = {}

    result = subprocess.call(args, env=dict(os.environ, **env_kwargs), cwd=cwd)
    if result > 0:
        raise CLIError('Failed to perform {} operation.'.format(args[1]))


def _run_command_silent(cwd, args):
    env_kwargs = {}
    fnull = open(os.devnull, 'w')
    result = subprocess.call(args, env=dict(os.environ, **env_kwargs), cwd=cwd, stdout=fnull, stderr=subprocess.STDOUT)
    if result > 0:
        raise CLIError('Failed to perform {} operation.'.format(args[1]))

