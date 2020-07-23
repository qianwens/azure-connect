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
from ._app import App

logger = get_logger(__name__)

DEFAULT_CLI = get_default_cli()


class AppClient:

    def __init__(self, app):
        self.app = app
        self._keyvault_cache = {}

    def create_app(self):

        # generate app config
        with open(".\\" + self.app.name + "\\app.json", 'w') as outfile:
            json.dump(self.app.__dict__, outfile)

    def deploy_app(self, environment):
        # create resource group
        rg = self.app.environments[environment].get('resourceGroup')
        location = self.app.environments[environment].get('location')
        self._create_resource_group(rg, location)
        # create keyvault
        self._create_keyvault(environment)
        # create db
        for db in self.app.addons:
            self._create_database(db, environment)
        # create services
        for service in self.app.services:
            self._create_service(service, environment)

    def get_app_log(self):
        pass

    def get_app(self):
        pass

    def open_app(self, environment):
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

    def _get_keyvault(self, environment):
        parameters = [
            'keyvault', 'show',
            '--name', environment + self.app.id_suffix,
            '--resource-group', self.app.environments[environment].get('resourceGroup')
        ]
        from six import StringIO
        stdout_buf = StringIO()
        try:
            if not DEFAULT_CLI.invoke(parameters, out_file=stdout_buf):
                return stdout_buf.getvalue()
        except SystemExit as ex:
            pass
        return None

    def _create_keyvault(self, environment):
        self._keyvault_cache[environment] = {}

        parameters = [
            'keyvault', 'create',
            '--name', environment + self.app.id_suffix,
            '--location', self.app.environments[environment].get('location'),
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--tags', 'app='+self.app.name
        ]

        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create keyvault %s' % self.app.id_suffix + environment)

    def _create_deploy_account(self, environment):
        import uuid
        password = str(uuid.uuid4())
        user_name = "deployuser" + self.app.id_suffix + environment
        self._store_secret(environment, "deployuser" + environment, password)
        parameters = [
            'webapp', 'deployment', 'user', 'set',
            '--user-name', user_name,
            '--password', password
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create deployment account %s' % user_name)

    def _get_deploy_account(self, environment):
        return "deployuser" + self.app.id_suffix + environment,\
               self._get_secret(environment, "deployuser" + environment)

    def _create_service(self, service, environment):
        service_creators = {
            "webapp": self._create_webapp
        }
        creator = service_creators[service.get('type')]
        creator(service, environment)

    def _create_webapp(self, service, environment):
        self._create_deploy_account(environment)
        service_name = service.get('name') + self.app.id_suffix + environment
        service_plan_name = environment + self.app.id_suffix
        print('create app service')
        parameters = [
            'appservice', 'plan', 'create',
            '--name', service_plan_name,
            '--location', self.app.environments[environment].get('location'),
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--number-of-workers', '1',  # todo: specify the worker number
            '--is-linux',
            '--sku', 'S1', # F1 free servicefarm max 10
            '--tags', 'app=' + self.app.name
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % self.app.name + environment)

        parameters = [
            'webapp', 'create',
            '--name', service_name,
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--plan', service_plan_name,
            '--runtime', service.get('properties').get('runtime'),
            '--tags', 'app='+self.app.name
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % service_name)

        parameters = [
            'webapp', 'deployment', 'source', 'config-local-git',
            '--name', service_name,
            '--resource-group', self.app.environments[environment].get('resourceGroup')
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % service_name)

        settings = [service.get('env')]
        for database in self.app.addons:
            settings.append("DBHOST=" + self._get_database_hostname(database, environment))
            settings.append("DBUSER=azureadmin@" + environment + self.app.id_suffix)
            settings.append("DBPASS=" + self._get_secret(environment, database.get('serverName') + "-adminpassword"))
            settings.append("DBNAME=" + database.get('databaseName'))

        parameters = [
            'webapp', 'config', 'appsettings', 'set',
            '--name', service_name,
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--settings'
        ] + settings
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % name)

        # push source code
        from ._gitUtil import push_repo
        deploy_user, password = self._get_deploy_account(environment)
        repo_url = f"https://{deploy_user}:{password}@{service_name}.scm.azurewebsites.net/{service_name}.git"
        push_repo(repo_url, "master", self.app.name, service.get('source'))

    def _create_database(self, database, environment):
        database_creator = {
            "postgresql": self._create_postgresql
        }
        creator = database_creator[database.get('type')]
        creator(database, environment)

    def _store_secret(self, environment, name, value):
        self._keyvault_cache[environment][name] = value

        parameters = [
            'keyvault', 'secret', 'set',
            '--name', name,
            '--vault-name', environment + self.app.id_suffix,
            '--value', value
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create secret %s' % name)

    def _get_secret(self, environment, name):
        # todo: return from keyvault
        return self._keyvault_cache[environment][name]

    def _create_postgresql(self, database, environment):
        import uuid
        administrator_login_password = str(uuid.uuid4())
        # todo: check server exist
        # store password
        self._store_secret(environment, database.get('serverName') + "-adminpassword", administrator_login_password)
        serverName = environment + self.app.id_suffix

        # create server
        parameters = [
            'postgres', 'server', 'create',
            '--name', serverName,
            '--location', self.app.environments[environment].get('location'),
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--sku-name', 'GP_Gen5_2',
            '--admin-user', 'azureadmin',
            '--admin-password', administrator_login_password,
            '--tags', 'app=' + self.app.name
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % serverName)

        # create db
        parameters = [
            'postgres', 'db', 'create',
            '--name', database.get('databaseName'),
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--server-name', serverName
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % serverName)

        # configure azure firewall
        parameters = [
            'postgres', 'server', 'firewall-rule', 'create',
            '--name', 'azure-access',
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--server-name', serverName,
            '--start-ip-address', '0.0.0.0',
            '--end-ip-address', '0.0.0.0'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % serverName)

    def _get_database_hostname(self, database, environment):
        hostname_suffix = {
            "postgresql": '.postgres.database.azure.com'
        }
        return environment + self.app.id_suffix + hostname_suffix[database.get('type')]
