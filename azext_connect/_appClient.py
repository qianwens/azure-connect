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


class AppClient:

    def __init__(self, app):
        self.app = app
        self._keyvault_cache = {}

    def create_app(self):
        # generate app config
        with open("./app.json", "w") as file:
            json.dump(self.app, file)

    def deploy_app(self, environment):
        # create resource group
        rg = self.app.env[environment].resource_group
        location = self.app.env[environment].location
        self._create_resource_group(rg, location)
        # create keyvault
        self._create_keyvault(environment)
        # create db
        for db in self.app.databases:
            self._create_database(db, environment)
        # create services
        for service in self.app.services:
            self._create_service(service, environment)

    def get_app_log(self):
        pass

    def get_app(self):
        pass

    def open_app(self):
        pass

    def local_run(self):
        pass

    def _create_resource_group(self, name, location):
        parameters = [
            'group', 'create',
            '--name', name,
            '--location', location,
            '--tags', 'app='+self.app.name
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource group %s' % name)

    def _create_keyvault(self, environment):
        self._keyvault_cache[environment] = {}
        parameters = [
            'keyvault', 'create',
            '--name', self.app.name + environment,
            '--location', self.app.env[environment].location,
            '--resource-group', self.app.env[environment].resource_group,
            '--tags', 'app='+self.app.name
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource group %s' % name)

    def _create_deploy_account(self, environment):
        password = str(uuid.uuid4())
        user_name = "deployuser" + self.app.resource_name_suffix + environment
        self._store_secret(environment, )
        parameters = [
            'webapp', 'deployment', 'user', 'set',
            '--user-name', user_name,
            '--password', password
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create deployment account %s' % user_name)

    def _create_service(self, service, environment):
        service_creators = {
            "webapp": self._create_webapp
        }
        creator = service_creators[service.type]
        creator(service, environment)

    def _create_webapp(self, service, environment, databases):
        _create_deploy_account(environment)

        parameters = [
            'appservice', 'plan', 'create',
            '--name', self.app.name + environment,
            '--location', self.app.env[environment].location,
            '--resource-group', self.app.env[environment].resource_group,
            '--number-of-workers', '1',  # todo: specify the worker number
            '--is-linux',
            '--sku', 'F1'
            '--tags', 'app=' + self.app.name
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % self.app.name + environment)

        parameters = [
            'webapp', 'create',
            '--name', service.name + self.app.resource_name_suffix,
            '--location', self.app.env[environment].location,
            '--resource-group', self.app.env[environment].resource_group,
            '--plan', self.app.name + environment,
            '--runtime', service.properties.runtime,
            '--tags', 'app='+self.app.name
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % service.name + self.app.resource_name_suffix)

        parameters = [
            'webapp', 'deployment', 'source', 'config-local-git'
            '--name', service.name + self.app.resource_name_suffix,
            '--resource-group', self.app.env[environment].resource_group
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % service.name)

        settings = service.env
        for database in databases:
            settings += " DBHOST="
            settings += self._get_database_hostname(database)
            settings += " DBUSER=azureadmin"
            settings += " DBPASS="
            settings += self._keyvault_cache[environment][database.serverName + ".admin_password"]
            settings += " DBNAME="
            settings += database.databaseName

        parameters = [
            'webapp', 'config', 'appsettings', 'set'
            '--name', service.name + self.app.resource_name_suffix,
            '--resource-group', self.app.env[environment].resource_group,
            '--settings', settings
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % name)

        

    def _create_database(self, database, environment):
        database_creator = {
            "postgresql": self._create_postgresql
        }
        creator = database_creator[database.type]
        creator(database, environment)

    def _store_secret(self, environment, name, value):
        self._keyvault_cache[environment][name] = value

        parameters = [
            'keyvault', 'secret', 'set',
            '--name', name,
            '--vault-name', self.app.name + environment,
            '--value', value,
            '--resource-group', self.app.env[environment].resource_group
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create secret %s' % name)

    def _create_postgresql(self, database, environment):
        administrator_login_password = str(uuid.uuid4())

        # store password
        self._store_secret(environment, database.serverName + ".admin_password", administrator_login_password)

        # create server
        parameters = [
            'postgres', 'server', 'create',
            '--name', database.serverName + environment,
            '--location', self.app.env[environment].location,
            '--resource-group', self.app.env[environment].resource_group,
            '--sku-name', 'GP_Gen5_2',
            '--admin-user', 'azureadmin',
            '--admin-password', administrator_login_password,
            '--tags', 'app=' + self.app.name
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % name)

        # create db
        parameters = [
            'postgres', 'db', 'create',
            '--name', database.databaseName,
            '--resource-group', self.app.env[environment].resource_group,
            '--server-name', database.serverName + environment
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % name)

        # configure azure firewall
        parameters = [
            'postgres', 'server', 'firewall-rule', 'create',
            '--name', 'azure-access',
            '--resource-group', self.app.env[environment].resource_group,
            '--server-name', database.serverName + environment,
            '--start-ip-address', '0.0.0.0',
            '--end-ip-address', '0.0.0.0'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % name)

    def _get_database_hostname(self, database):
        hostname_suffix = {
            "postgresql": '.postgres.database.azure.com'
        }
        return database.serverName + hostname_suffix[database.type]