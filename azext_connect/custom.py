# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import random
import time
import sys
import re
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.command_modules.profile.custom import get_access_token
from azure.cli.core import get_default_cli
from azure.cli.core.commands.client_factory import get_subscription_id
from knack.prompting import prompt, prompt_pass, prompt_choice_list
from ._apis import CupertinoApi
from ._model import AuthType, AuthInfo

logger = get_logger(__name__)
COSMOSDB_KIND = ['GlobalDocumentDB', 'MongoDB', 'Parse']
COSMOS_CAPABILITES = ['EnableCassandra', 'EnableTable', 'EnableGremlin']
COSMOS_DATABASE_TYPE = ['cassandraKeyspaces', 'tables', 'gremlinDatabases', 'sqlDatabases', 'mongodbDatabases']


def _is_resourcid(resource):
    return resource.startswith('/subscriptions/')


def _get_rg_from_scope(scope):
    if scope.startswith('/subscriptions'):
        match = re.search(r"\/resourceGroups\/[^\/]+", scope)
        if (match):
            return match.group().split("/")[2]
    raise Exception('Can not get resource group from {0}'.format(scope))


def _get_cosmos_database_type(resource_group, cosmos_account):
    cli = get_default_cli()
    parameters = [
        'cosmosdb', 'show',
        '--name', cosmos_account,
        '--resource-group', resource_group,
        '--output', 'none'
    ]
    if cli.invoke(parameters):
        raise CLIError('Fail to show CosmosDb account %s info.' % cosmos_account)
    kind = cli.result.result['kind']
    capabilites = cli.result.result['capabilities']
    if kind == COSMOSDB_KIND[0]:
        for item in capabilites:
            if item['name'] == COSMOS_CAPABILITES[0]:
                return COSMOS_DATABASE_TYPE[0]
            if item['name'] == COSMOS_CAPABILITES[1]:
                return COSMOS_DATABASE_TYPE[1]
            if item['name'] == COSMOS_CAPABILITES[2]:
                return COSMOS_DATABASE_TYPE[2]
        return COSMOS_DATABASE_TYPE[3]
    if kind == COSMOSDB_KIND[1]:
        return COSMOS_DATABASE_TYPE[4]
    raise Exception('CosmosDB database type not supported')


def _update_postgres_server(target, password):
    cli = get_default_cli()
    parameters = [
        'postgres', 'server', 'update',
        '--ids', target,
        '--admin-password', password
    ]
    rc = cli.invoke(parameters)
    return rc


def _get_target_id(scope, sql=None, mysql=None, postgres=None, cosmos=None, database=None, signalR=None, keyvault=None):
    if sql and database:
        sql = sql if _is_resourcid(sql) else '{0}/providers/Microsoft.Sql/servers/{1}'.format(scope, sql)
        return '{0}/databases/{1}/'.format(sql, database)
    if mysql and database:
        mysql = mysql if _is_resourcid(mysql) else '{0}/providers/Microsoft.DBforMySQL/servers/{1}'.format(scope, mysql)
        return '{0}/databases/{1}'.format(mysql, database)
    if postgres and database:
        postgres = postgres if _is_resourcid(postgres) else '{0}/providers/Microsoft.DBforPostgreSQL/servers/{1}'.format(scope, postgres)
        return '{0}/databases/{1}'.format(postgres, database)
    if cosmos and database:
        if _is_resourcid(cosmos):
            cosmos_id = cosmos
        else:
            cosmos_id = '{0}/providers/Microsoft.DocumentDb/databaseAccounts/{1}'.format(scope, cosmos)
        database_type = _get_cosmos_database_type(_get_rg_from_scope(scope), cosmos)
        return '{0}/{1}/{2}'.format(cosmos_id, database_type, database)
    if signalR:
        return signalR if _is_resourcid(signalR) else '{0}/providers/Microsoft.SignalRService/signalR/{1}'.format(scope, signalR)
    if keyvault:
        return keyvault if _is_resourcid(keyvault) else '{0}/providers/Microsoft.KeyVault/vaults/{1}'.format(scope, keyvault)
    else:
        raise Exception('Target resource is not valid')


def _create_api(cmd):
    authtoken = get_access_token(cmd)
    graphtoken = get_access_token(cmd, resource='https://graph.windows.net/')
    sqltoken = get_access_token(cmd, resource='https://database.windows.net')
    mysqltoken = get_access_token(cmd, resource_type='oss-rdbms')
    return CupertinoApi(authtoken, graphtoken, sqltoken, mysqltoken)


def _bind(
    cmd, subscription, resource_group, name, source, target, authtype, permission=None, client_id=None,
    client_secret=None, username=None, password=None, additional_info={}
):
    if not AuthType.has_value(authtype):
        raise Exception('Auth type not supported')
    auth_info = AuthInfo(
        AuthType(authtype), permission, client_id, client_secret, username, password
    )
    api = _create_api(cmd)
    result = api.create(subscription, resource_group, name, source, target, auth_info, additional_info)
    if result.ok is not True:
        err_msg = 'Fail to bind {0} with {1}. Code:{2}. Detail:{3}'.format(source, target, result.status_code, result.text)
        raise Exception(err_msg)
    res_obj = json.loads(result.text)
    return res_obj


def bind_webapp(
    cmd, resource_group, name, appname, authtype='MSI', permission=None,
    sql=None, mysql=None, postgres=None, cosmos=None, database=None, client_id=None,
    client_secret=None, username=None, password=None,
    keyvault=None
):
    try:
        subscription = get_subscription_id(cmd.cli_ctx)
        scope = '/subscriptions/{0}/resourceGroups/{1}'.format(subscription, resource_group)
        source = '{0}/providers/Microsoft.Web/sites/{1}'.format(scope, appname)
        target = _get_target_id(scope, sql=sql, cosmos=cosmos, mysql=mysql, postgres=postgres, database=database, keyvault=keyvault)
        result = _bind(
            cmd, subscription, resource_group, name, source,
            target, authtype, permission, client_id, client_secret, username, password
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(e)
        logger.error(e)
        sys.exit(1)


def bind_webapp_postgres(
    cmd, resource_group, appname, server, database,
    name=None, client_id=None, client_secret=None,
    username=None, password=None, authtype='Secret', permission=None
):
    try:
        if authtype == 'Secret':
            if not username:
                username = prompt('Username: ')
            if not password:
                password = prompt_pass(msg='Password: ')
        if not name:
            name = '{0}_{1}_{2}_{3}_{4}'.format(appname, server, database, int(time.time()), random.randint(10000, 99999)) 
        subscription = get_subscription_id(cmd.cli_ctx)
        scope = '/subscriptions/{0}/resourceGroups/{1}'.format(subscription, resource_group)
        source = '{0}/providers/Microsoft.Web/sites/{1}'.format(scope, appname)
        target = _get_target_id(scope, postgres=server, database=database)
        succeeded = False
        for i in range(3):
            try:
                result = _bind(
                    cmd, subscription, resource_group, name, source,
                    target, authtype, permission, client_id, client_secret, username, password
                )
            except Exception as e:
                s = str(e)
                if s.find('\"UnauthorizedResourceAccess\"') and authtype == 'Secret':
                    print('Admin username or password error, retry left: {0}'.format(3-i))
                    choice_list = [
                        're-input the password for the admin user \"{0}\"'.format(username),
                        'Change the password for the admin user \"{0}\"'.format(username)
                    ]
                    choice = prompt_choice_list('Select re-input the admin password or change the admin password',
                                                choice_list)
                    if choice == 0:
                        password = prompt_pass(msg='Password: ')
                    elif choice == 1:
                        password = prompt_pass(msg='New password: ')
                        _update_postgres_server(target, password)
                    continue
            else:
                succeeded = True
                print(json.dumps(result, indent=2))
                break
        if not succeeded:
            result = _bind(
                cmd, subscription, resource_group, name, source,
                target, authtype, permission, client_id, client_secret, username, password
            )
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(e)
        logger.error(e)
        sys.exit(1)


def bind_springcloud(
    cmd, resource_group, name, springcloud, appname, mysql=None, cosmos=None, database=None, username=None, password=None
):
    try:
        subscription = get_subscription_id(cmd.cli_ctx)
        scope = '/subscriptions/{0}/resourceGroups/{1}'.format(subscription, resource_group)
        source = '{0}/providers/Microsoft.AppPlatform/Spring/{1}/Apps/{2}'.format(scope, springcloud, appname)
        target = _get_target_id(scope, mysql=mysql, cosmos=cosmos, database=database)
        result = _bind(
            cmd, subscription, resource_group, name, source,
            target, authtype='Secret', username=username, password=password
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(e)
        logger.error(e)
        sys.exit(1)


def bind_function(
    cmd, resource_group, name, appname, function_name=None,
    signalR=None, binding=None, username=None, password=None
):
    try:
        subscription = get_subscription_id(cmd.cli_ctx)
        scope = '/subscriptions/{0}/resourceGroups/{1}'.format(subscription, resource_group)
        source = '{0}/providers/Microsoft.Web/sites/{1}/functions/{2}'.format(scope, appname, function_name)
        target = _get_target_id(scope, signalR=signalR)
        additional_info = {'BindingType': binding}
        result = _bind(
            cmd, subscription, resource_group, name, source,
            target, 'Secret', None, None, None, username, password, additional_info)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(e)
        logger.error(e)
        sys.exit(1)


def validate_general(cmd, resource_group, name):
    try:
        subscription = get_subscription_id(cmd.cli_ctx)
        api = _create_api(cmd)
        result = api.validate(subscription, resource_group, name)
        if result.ok is not True:
            err_msg = 'Fail to validate the connection {0}. Code:{1}. Detail:{2}'.format(name, result.status_code, result.text)
            raise Exception(err_msg)
        res_obj = json.loads(result.text)
        print(json.dumps(res_obj, indent=2))
    except Exception as e:
        print(e)
        logger.error(e)
        sys.exit(1)


def get_general(cmd, resource_group, name):
    try:
        subscription = get_subscription_id(cmd.cli_ctx)
        api = _create_api(cmd)
        result = api.get(subscription, resource_group, name)
        if result.ok is not True:
            err_msg = 'Fail to get the connection {0}. Code:{1}. Detail:{2}'.format(name, result.status_code, result.text)
            raise Exception(err_msg)
        res_obj = json.loads(result.text)
        print(json.dumps(res_obj, indent=2))
    except Exception as e:
        print(e)
        logger.error(e)
        sys.exit(1)