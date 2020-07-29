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
import prettytable as pt
import os
from getpass import getpass
from ._app import App
from halo import Halo

logger = get_logger(__name__)

DEFAULT_CLI = get_default_cli()


class AppClient:

    def __init__(self, app):
        self.app = app
        self._keyvault_cache = {}

    def create_app(self):
        spinner = Halo(text="[app] Storing app: \033[43m{0}\033[00m ...".format(self.app.name),
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
        # generate app config
        with open("./" + self.app.name + "/app.json", 'w') as outfile:
            json.dump(self.app.__dict__, outfile)
        spinner.succeed("[app] Stored app: \033[43m{0}\033[00m".format(self.app.name))

    def deploy_app(self, environment):
        # create resource group
        print("\033[92m{}\033[00m".format("* Begin deploy app infrastructure in environment: {0}".format(environment)))
        rg = self.app.environments[environment].get('resourceGroup')
        location = self.app.environments[environment].get('location')
        self._create_resource_group(rg, location)
        # create keyvault
        self._create_keyvault(environment)
        # create db
        for db in self.app.addons:
            self._create_database(db, environment)
            self._set_database_firewall(db, environment)
        # create services
        self.update_launch_file(environment)
        for service in self.app.services:
            self._create_service(service, environment)

        self.migrate_db(environment)
        
    def update_launch_file(self, environment):
        for service in self.app.services:
            if 'source' not in service or not service['source']:
                continue
            launch_path = os.path.join("./" + self.app.name, service['source'], '.vscode', 'launch.json')
            if os.path.exists(launch_path):
                with open(launch_path, 'r') as fp:
                    content = fp.read()
                    for database in self.app.addons:
                        content = content.replace('{DBHOST}', self._get_database_hostname(database, environment))\
                            .replace('{DBUSER}', 'azureadmin@' + environment + self.app.id_suffix)\
                            .replace('{DBNAME}', database.get('databaseName'))
                        secrets = self._get_keyvault_secrets(environment)
                        for key, value in secrets.items():
                            if key == database.get('serverName') + "-adminpassword":
                                content.replace('{DBPASS}', self._get_secret(environment, database.get(
                                    'serverName') + "-adminpassword"))
                                content = content.replace('{DBPASS}', value)
                                break
                        break
                with open(launch_path, 'w') as fp:
                    fp.write(content)

    def get_app_log(self, environment):
        logs = []
        # get db log
        for db in self.app.addons:
            log = self._get_database_log(db, environment)
            if log is not None:
                logs.extend(log)
        # get app log
        for service in self.app.services:
            log = self._get_service_log(service, environment)
            if log is not None:
                logs.extend(log)

        sorted_logs = sorted(logs, key=lambda log: log[0])
        
        for log in sorted_logs:
            print(log[0] + ' ' + log[1].replace('\n', ''))

    def get_app(self, environment):
        # print('\033[1m' + 'About' + '\033[0m')
        for service in self.app.services:
            self._get_service_info(service, environment)
        
        print('\n' + '\033[1m' + 'Connected Services' + '\033[0m')
        table = pt.PrettyTable(['Service Type', 'Name', 'Endpoint'])
        table.add_row(self._get_keyvault_info(environment))
        for db in self.app.addons:
            table.add_row(self._get_database_info(db, environment))
        print(table)

        print('\n' + '\033[1m' + 'Secrets in keyvault' + '\033[0m')
        table = pt.PrettyTable(['Secret Name', 'Secret Value'])
        vaults = self._get_keyvault_secrets(environment)
        for key, value in vaults.items():
            # usage = self._parse_secret_name(key)
            table.add_row([key, value])
        print(table)

        print('\n' + '\033[1m' + 'Next Commands' + '\033[0m')
        table = pt.PrettyTable(['Service Type', 'Command Description', 'Command'])
        printTable = []
        for db in self.app.addons:
            printTable += self._get_database_commands(db, environment)
        for service in self.app.services:
            printTable += self._get_service_commands(service, environment)
        for command in printTable:
            table.add_row(command)
        print(table)

    def open_app(self, environment):
        import webbrowser
        # get url of webapp
        # assume we only have one webapp service here
        service_name = self.app.services[0].get('name') + self.app.id_suffix + environment
        url = "https://{0}.azurewebsites.net".format(service_name)
        print("\033[92m{}\033[00m".format("* Open browser at {0}".format(url)))
        webbrowser.open(url)

    def local_run(self, environment):
        for database in self.app.addons:
            self._set_database_firewall(database, environment)
            self._set_database_env(database, environment)
            self._run_database_server(database)

    def run_command(self, environment, commands=None):
        from ._run import run_ssh
        resource_group = self.app.environments[environment].get('resourceGroup')
        # assume we only have one webapp service here
        service_name = self.app.services[0].get('name') + self.app.id_suffix + environment
        run_ssh(resource_group, service_name, commands=commands)

    def migrate_db(self, environment):
        for database in self.app.addons:
            migrate_command = database.get('migrate', None)
            if migrate_command:
                print("\033[92m{}\033[00m".format(
                    "* Begin migrate database: {0}".format(database.get('databaseName'))))
                commands = ["cd site/wwwroot", "source /antenv/bin/activate",
                            "pip install -r requirements.txt", migrate_command]
                #print("command to run: ", commands)
                self.run_command(environment, commands)

    def _create_resource_group(self, name, location):
        spinner = Halo(text="[app] Creating resource group: \033[43m{0}\033[00m ...".format(name),
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
        parameters = [
            'group', 'create',
            '--name', name,
            '--location', location,
            '--tags', 'app='+self.app.name,
            '-o', 'none'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource group %s' % name)
        spinner.succeed("[app] Created resource group: \033[43m{0}\033[00m".format(name))

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
        key_vault_name = environment + self.app.id_suffix
        spinner = Halo(text="[app] Creating key vault: \033[43m{0}\033[00m ...".format(key_vault_name),
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
        parameters = [
            'keyvault', 'create',
            '--name', key_vault_name,
            '--location', self.app.environments[environment].get('location'),
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--tags', 'app='+self.app.name,
            '-o', 'none'
        ]

        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create keyvault %s' % key_vault_name)
        spinner.succeed("[app] Created key vault: \033[43m{0}\033[00m".format(key_vault_name))

    def _create_deploy_account(self, environment):
        import uuid
        password = str(uuid.uuid4())
        user_name = "deployuser" + self.app.id_suffix + environment
        spinner = Halo(text='[webapp] Creating web app deploy user: \033[43m{0}\033[00m ...'.format(user_name),
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
        self._store_secret(environment, "deployuser" + environment, password)
        parameters = [
            'webapp', 'deployment', 'user', 'set',
            '--user-name', user_name,
            '--password', password,
            '-o', 'none'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create deployment account %s' % user_name)
        spinner.succeed('[webapp] Created web app deploy user: \033[43m{0}\033[00m'.format(user_name))

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
        spinner = Halo(text='[webapp] Creating web app service plan: \033[43m{0}\033[00m ...'.format(service_plan_name),
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
        parameters = [
            'appservice', 'plan', 'create',
            '--name', service_plan_name,
            '--location', self.app.environments[environment].get('location'),
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--number-of-workers', '1',  # todo: specify the worker number
            '--is-linux',
            '--sku', 'S1', # F1 free servicefarm max 10
            '--tags', 'app=' + self.app.name,
            '-o', 'none',
            '--query', '[name, resourceGroup, location, maximumElasticWorkerCount, id]'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % self.app.name + environment)
        spinner.succeed('[webapp] Created web app service plan: \033[43m{0}\033[00m '.format(service_plan_name))
        spinner = Halo(text="[webapp] Creating webapp service: \033[43m{0}\033[00m...".format(service_name),
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
        parameters = [
            'webapp', 'create',
            '--name', service_name,
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--plan', service_plan_name,
            '--runtime', service.get('properties').get('runtime'),
            '--tags', 'app='+self.app.name,
            '-o', 'none',
            '--query', '[defaultHostName, resourceGroup, location, state, id]'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % service_name)
        spinner.succeed("[webapp] Created webapp service: \033[43m{0}\033[00m".format(service_name))
        spinner = Halo(text="[webapp] Configuring local git deploy...",
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
        parameters = [
            'webapp', 'deployment', 'source', 'config-local-git',
            '--name', service_name,
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '-o', 'none'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % service_name)
        spinner.succeed("[webapp] Configured local git deploy")

        spinner = Halo(text="[webapp] Configuring webapp settings...",
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
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
            '-o', 'none',
            '--settings',
        ] + settings
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % name)
        spinner.succeed("[webapp] Configured webapp settings")
        # push source code
        print("\033[92m{}\033[00m".format("* Begin deploy source code in environment: {0}".format(environment)))
        from ._gitUtil import push_repo
        deploy_user, password = self._get_deploy_account(environment)
        repo_url = f"https://{deploy_user}:{password}@{service_name}.scm.azurewebsites.net/{service_name}.git"
        push_repo(repo_url, "master", self.app.name, service.get('source'))
        print("\033[92m{}\033[00m".format("* Run `git push {0} master -f` to deploy source code.".format(repo_url)))


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
            '--value', value,
            '-o', 'none'
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
        spinner = Halo(text='[postgresql] Storing postgresql server admin user secret...',
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
        self._store_secret(environment, database.get('serverName') + "-adminpassword", administrator_login_password)
        spinner.succeed('[postgresql] Stored postgresql server admin user secret')
        server_name = environment + self.app.id_suffix
        spinner = Halo(text='[postgresql] Creating postgresql server: \033[43m{0}\033[00m ...'.format(server_name),
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
        # create server
        parameters = [
            'postgres', 'server', 'create',
            '--name', server_name,
            '--location', self.app.environments[environment].get('location'),
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--sku-name', 'GP_Gen5_2',
            '--admin-user', 'azureadmin',
            '--admin-password', administrator_login_password,
            '--tags', 'app=' + self.app.name,
            '-o', 'none',
            '--query', '[fullyQualifiedDomainName, location, resourceGroup, userVisibleState, id]'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % server_name)
        spinner.succeed('[postgresql] Created postgresql server: \033[43m{0}\033[00m'.format(server_name))
        spinner = Halo(text='[postgresql] Creating postgresql DB: \033[43m{0}\033[00m ...'.format(database.get('databaseName')),
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
        # create db
        parameters = [
            'postgres', 'db', 'create',
            '--name', database.get('databaseName'),
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--server-name', server_name,
            '-o', 'none'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % server_name)
        spinner.succeed('[postgresql] Created postgresql DB: \033[43m{0}\033[00m'.format(database.get('databaseName')))
        spinner = Halo(text='[postgresql] Opening postgres server firewall for azure service access...',
                       spinner='dots', text_color='yellow', color='blue')
        spinner.start()
        # configure azure firewall
        parameters = [
            'postgres', 'server', 'firewall-rule', 'create',
            '--name', 'azure-access',
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--server-name', server_name,
            '--start-ip-address', '0.0.0.0',
            '--end-ip-address', '0.0.0.0',
            '-o', 'none'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % server_name)
        spinner.succeed('[postgresql] Opened postgres server firewall for azure service access')

    def _get_database_hostname(self, database, environment):
        hostname_suffix = {
            "postgresql": '.postgres.database.azure.com'
        }
        return environment + self.app.id_suffix + hostname_suffix[database.get('type')]

    def _get_database_log(self, database, environment):
        database_logger = {
            "postgresql": self._get_postgresql_log
        }
        logger = database_logger[database.get('type')]
        return logger(database, environment)

    def _list_postgresql_log(self, serverName, environment):
        parameters = [
            'postgres', 'server-logs', 'list',
            '--server-name', serverName,
            '--resource-group', self.app.environments[environment].get('resourceGroup'),
            '--output', 'none'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to list logs of postgresql %s' % serverName)

        file_names = []
        log_file = json.loads(json.dumps(DEFAULT_CLI.result.result))
        for item in log_file[1:]:
            file_names.append(item['name'])
        if file_names.count == 0:
            return
        file_names.reverse()
        return file_names

    def _get_postgresql_log(self, database, environment):
        logs = []
        lines = 10
        serverName = environment + self.app.id_suffix
        # list log files
        file_names = self._list_postgresql_log(serverName, environment)

        # download and print log files
        i = 0
        while lines > 0:
            if i >= len(file_names):
                return

            parameters = [
                'postgres', 'server-logs', 'download',
                '--server-name', serverName,
                '--resource-group', self.app.environments[environment].get('resourceGroup'),
                '-n', file_names[i]
            ]

            if DEFAULT_CLI.invoke(parameters):
                raise CLIError('Fail to load log %s' % file_names[i])
            
            current_file = open(file_names[i], 'r')
            file_line = -1
            for file_line, line in enumerate(current_file):
                pass
            file_line += 1
            current_file.seek(0, 0)
            if lines > file_line:
                while True:
                    current_line = current_file.readline()
                    if current_line:
                        parsed_log = self._parse_postgre_log(current_line, serverName)
                        if parsed_log is not None:
                            logs.append(parsed_log)
                    else:
                        break
                current_file.close()
                os.remove(file_names[i])
                lines = lines - file_line
                i += 1
                continue
            else:
                j = 0
                while j < file_line - lines:
                    current_file.readline()
                    j += 1
                while True:
                    current_line = current_file.readline()
                    if current_line:
                        parsed_log = self._parse_postgre_log(current_line, serverName)
                        if parsed_log is not None:
                            logs.append(parsed_log)
                    else:
                        break
                current_file.close()
                os.remove(file_names[i])
                break
        return logs

    def _parse_postgre_log(self, log, server_name):
        contents = log.split('-', 4)
        if (len(contents) < 3):
            return
        times = contents[2].split(' ', 2)
        if (len(contents) < 5):
            return [contents[0] + '-' + contents[1] + '-' + times[0] + ' ' + times[1], server_name + '[postresql]: ']
        else:
            if contents[4].startswith('ERROR'):
                contents[4] = '\033[31;1m' + contents[4] + '\033[0m'
            elif contents[4].startswith('WARNING'):
                contents[4] = '\033[35;1m' + contents[4] + '\033[0m'
            elif contents[4].startswith('STATEMENT'):
                contents[4] = '\033[32;1m' + contents[4] + '\033[0m'
            return [contents[0] + '-' + contents[1] + '-' + times[0] + ' ' + times[1], server_name + '[postresql]: ' + contents[4]]

    def _get_service_log(self, service, environment):
        service_loggers = {
            "webapp": self._get_webapp_log
        }
        logger = service_loggers[service.get('type')]
        return logger(service, environment)

    def _get_webapp_log(self, service, environment):
        logs = []
        lines = 10
        service_name = service.get('name') + self.app.id_suffix + environment
        parameters = [
            'webapp', 'log', 'download',
            '-n', service_name,
            '-g', self.app.environments[environment].get('resourceGroup'),
            '--output', 'none'
        ]

        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to get log of webapp %s' % service_name)
        
        import zipfile
        with zipfile.ZipFile('webapp_logs.zip') as zf:
            zf.extractall()
            os.chdir("LogFiles/")
            os.chdir("kudu/")
            os.chdir("deployment/")
            for file in os.listdir():
                current_file = open(file, 'r')
                file_line = -1
                for file_line, line in enumerate(current_file):
                    pass
                file_line += 1
                current_file.seek(0, 0)
                if file_line < lines:
                    while True:
                        current_line = current_file.readline()
                        if current_line:
                            parsed_log = self._parse_webapp_log(current_line, service_name)
                            if parsed_log is not None:
                                logs.append(self._parse_webapp_log(current_line, service_name))
                        else:
                            break
                else:
                    j = 0
                    while j < file_line - lines:
                        current_file.readline()
                        j += 1
                    while True:
                        current_line = current_file.readline()
                        if current_line:
                            parsed_log = self._parse_webapp_log(current_line, service_name)
                            if parsed_log is not None:
                                logs.append(self._parse_webapp_log(current_line, service_name))
                        else:
                            break

                current_file.close()
        
        os.chdir("../../../")
        os.remove('webapp_logs.zip')
        import shutil
        shutil.rmtree('deployments')
        shutil.rmtree('LogFiles')
        return logs

    def _parse_webapp_log(self, log, service_name):
        contents = log.split('  ', 1)
        times = contents[0].split('T', 1)
        if (len(times) == 1):
            return None
        if (len(contents) == 1):
            return [times[0] + ' ' + times[1], service_name + '[webapp]: ']
        else:
            return [times[0] + ' ' + times[1], service_name + '[webapp]: ' + contents[1]]

    def _get_keyvault_info(self, environment):
        res = []
        server = environment + self.app.id_suffix
        res.append('KeyVault')
        res.append(server)
        info = json.loads(self._get_keyvault(environment))
        res.append(info['properties']['vaultUri'])
        # res.append(info['id'])
        return res

    def _get_database_info(self, database, environment):
        database_info = {
            "postgresql": self._get_postgresql_info
        }
        info = database_info[database.get('type')]
        return info(database, environment)

    def _get_postgresql(self, database, environment):
        serverName = environment + self.app.id_suffix
        parameters = [
            'postgres', 'server', 'show',
            '--name', serverName,
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

    def _get_postgresql_info(self, database, environment):
        res = []
        # server = environment + self.app.id_suffix
        res.append('PostgresDB')
        res.append(database['databaseName'])
        res.append(self._get_database_hostname(database, environment))
        info = json.loads(self._get_postgresql(database, environment))
        # res.append(info['id'])
        return res

    def _get_keyvault_secrets(self, environment):
        res = {}
        vault = environment + self.app.id_suffix
        parameters = [
            'keyvault', 'secret', 'list',
            '--vault-name', vault,
            '--output', "none"
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to get vault secret %s' % vault)

        secret_names = []
        secret_names_json = json.loads(json.dumps(DEFAULT_CLI.result.result))
        for item in secret_names_json:
            secret_names.append(item['name'])

        for item in secret_names:
            parameters = [
                'keyvault', 'secret', 'show',
                '--vault-name', vault,
                '-n', item,
                '--output', "none"
            ]
            if DEFAULT_CLI.invoke(parameters):
                raise CLIError('Fail to get vault secret %s' % vault)
            secret_json = json.loads(json.dumps(DEFAULT_CLI.result.result))
            res[item] = secret_json['value']

        return res
    
    def _get_service_info(self, service, environment):
        service_info = {
            "webapp": self._get_webapp_info
        }
        info = service_info[service.get('type')]
        return info(service, environment)

    def _get_webapp_info(self, service, environment):
        service_name = service.get('name') + self.app.id_suffix + environment

        print("Name\t\t {0}".format(service_name))
        print("HostName\t https://{0}.azurewebsites.net".format(service_name))
        print("GitURL\t\t https://{0}.scm.azurewebsites.net/{0}.git".format(service_name))
        print("Environment\t {0}".format(environment))

    def _get_service_commands(self, service, environment):
        service_commands = {
            "webapp": self._get_webapp_commands
        }
        commands = service_commands[service.get('type')]
        return commands(service, environment)

    def _get_webapp_commands(self, service, environment):
        res = []
        service_type = 'Webapp'
        service_name = service.get('name') + self.app.id_suffix + environment
        rg = self.app.environments[environment].get('resourceGroup')

        # az webapp show
        res.append([service_type, 'Get the details of a web app.', 'az webapp show -n {0} -g {1}'.format(service_name, rg)])

        # az webapp config show
        res.append([service_type, 'Get the details of a web app\'s configuration.', 'az webapp config show -n {0} -g {1}'.format(service_name, rg)])

        return res

    def _get_database_commands(self, database, environment):
        database_commands = {
            "postgresql": self._get_postgresql_commands
        }
        commands = database_commands[database.get('type')]
        return commands(database, environment)

    def _get_postgresql_commands(self, database, environment):
        res = []
        serverName = environment + self.app.id_suffix
        rg = self.app.environments[environment].get('resourceGroup')
        service_type = 'PostgresDB'

        # az postgres server show
        res.append([service_type, 'Get the details of a server.', 'az postgres server show -n {0} -g {1}'.format(serverName, rg)])

        # az postgres server configuration show
        res.append([service_type, 'Get the configuration for a server.', 'az postgres server configuration show -n {0} -g {1}'.format(serverName, rg)])

        return res

    def _parse_secret_name(self, secret_name):
        if secret_name.endswith('-adminpassword'):
            server_name = secret_name.replace('-adminpassword', '')
            return "Admin password of {0}.".format(server_name)

        elif secret_name.startswith('deployuser'):
            return "Webapp deployment user."

    def _set_database_env(self, database, environment):
        database_env = {
            "postgresql": self._set_postgresql_env
        }
        env = database_env[database.get('type')]
        env(database, environment)

    def _set_postgresql_env(self, database, environment):
        os.environ["DJANGO_ENV"] = "production"
        os.environ["DBHOST"] = self._get_database_hostname(database, environment)
        os.environ["DBUSER"] = "azureadmin@{0}{1}".format(environment, self.app.id_suffix)
        os.environ['DBNAME'] = database.get('databaseName')
        secrets = self._get_keyvault_secrets(environment)
        for key, value in secrets.items():
            if key == database.get('serverName') + "-adminpassword":
                os.environ['DBPASS'] = value
                break
        
        print("Env:")
        print("DBHOST = {0}".format(os.environ.get("DBHOST")))
        print("DBUSER = {0}".format(os.environ.get("DBUSER")))
        print("DBNAME = {0}".format(os.environ.get("DBNAME")))
        print("DBPASS = **********")
        print("DJANGO_ENV = {0}".format(os.environ.get("DJANGO_ENV")))

    def _run_database_server(self, database):
        database_servers = {
            "postgresql": self._run_postgresql_server
        }
        server = database_servers[database.get('type')]
        server()

    def _run_postgresql_server(self):
        os.chdir("azure-sample-master/")
        from ._local import runServer
        runServer()

    def _set_database_firewall(self, database, environment):
        import requests
        ip = requests.get('http://ip.42.pl/raw').text
        print("Current IP: {0}".format(ip))

        database_firewalls = {
            "postgresql": self._set_postgresql_firewall
        }
        firewall = database_firewalls[database.get('type')]
        firewall(database, environment, ip)

    def _set_postgresql_firewall(self, database, environment, ip):
        serverName = environment + self.app.id_suffix
        parameters = [
            'postgres', 'server', 'firewall-rule', 'create',
            '-g', self.app.environments[environment].get('resourceGroup'),
            '-s', serverName,
            '-n', 'LocalIp',
            '--start-ip-address', ip,
            '--end-ip-address', ip,
            '--output', 'none'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to set firewall rul for PostgresSQL %s' % serverName)
