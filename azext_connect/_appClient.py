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
from ._app import app

logger = get_logger(__name__)

DEFAULT_CLI = get_default_cli()


def create_app(app):
    # generate app config
    with open("./app.json", "w") as file:
        json.dump(app, file)


def deploy_app(app):
    # create keyvault
    # create services
    # store password
    # create db
    # configure webapp
    pass


def get_app_log():
    pass


def get_app():
    pass


def open_app():
    pass


def local_run():
    pass


