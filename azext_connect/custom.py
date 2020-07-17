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
from ._apis import CupertinoApi
from ._cosmosdb import cosmosdb_handler
from ._model import (AuthType, AuthInfo)
from ._mysql import mysql_handler
from ._spring_cloud import spring_cloud_handler
import subprocess
from getpass import getpass

logger = get_logger(__name__)

SERVICE_MAP = {
    'signalr': ('signalr', 'Azure SignalR Service', 1),
    'sql': ('sql', 'Azure SQL Database', 2),
    'webapp': ('webapp', 'Azure Web App Service', 3),
    'acr': ('acr', 'Azure Container Registry', 4),
    'aks': ('aks', 'Azure Kubernetes Service', 5),
    'cosmosdb': ('cosmosdb', 'Azure CosmosDB Service', 6),
    'mysql': ('mysql', 'Azure Database for MySQL', 7),
    'spring-cloud': ('spring-cloud', 'Azure Spring Cloud', 8)
}
DEFAULT_CLI = get_default_cli()


def connect(resource_group, aks = None, acr = None, webapp = None, sql = None,
            mysql = None, asc = None, ascapp = None):
    if not resource_group:
        raise CLIError('--resource-group not specified')
    service_list = []
    services_name = []
    para_list = ''
    connection_type = ''
    url = ''
    if acr:
        service_list.append(SERVICE_MAP['acr'])
        para_list = para_list + 'acr:' + acr + ' '
        services_name.append(acr)
    if aks:
        service_list.append(SERVICE_MAP['aks'])
        para_list = para_list + 'aks:' + aks + ' '
        connection_type = connection_type + 'Service Principal'
        url = url + 'https://aka.ms/AA861xl'
        services_name.append(aks)
    if sql:
        service_list.append(SERVICE_MAP['sql'])
        para_list = para_list + 'sql:' + sql +' msi:1 '
        para_list = interaction('database', para_list)
        para_list = interaction('aad-user', para_list)
        connection_type = connection_type + 'Managaed Identity (MSI)'
        url = url + 'https://aka.ms/AA866zi'
        services_name.append(sql)
    if webapp:
        service_list.append(SERVICE_MAP['webapp'])
        para_list = para_list + 'webapp:' + webapp + ' '
        services_name.append(webapp)
    if mysql:
        service_list.append(SERVICE_MAP['mysql'])
        para_list = para_list + 'mysql_server_name:' + mysql + ' '
        para_list = interaction('admin_user', para_list)
        para_list = interaction('admin_password', para_list, True)
        para_list = interaction('database_name', para_list)
        connection_type = connection_type + 'Service Binding'
        url = url + 'https://aka.ms/AA877da'
        services_name.append(mysql)
    if asc:
        service_list.append(SERVICE_MAP['spring-cloud'])
        para_list = para_list + 'asc_name:' + asc + ' '
        if not ascapp:
            raise CLIError('Need to input ASC App name using --ascapp.')
        para_list = para_list + 'app_name:' + ascapp + ' '
        services_name.append(asc)
    service_list.sort(key=lambda x: x[2])
    check_resource(service_list, resource_group)
    para_dict = parseParameter(para_list)
    deploy(service_list, resource_group, para_dict)
    # print('Service %s connected via %s.' %(' and '.join([s[1] + ':' + para_dict[s[0]] for s in service_list]), connection_type))
    print('Serivce %s:%s and %s:%s connected via %s' %(service_list[0][1], services_name[0], service_list[1][1], services_name[1], connection_type))
    print('To test connection, either run \'az connect test\' or follow %s.' % url)

def interaction(display_name, para_list, passwd = None):
    if passwd:
        para = getpass('%s: ' % display_name)
    else:
        para = input("%s: " % display_name)
    para_list = para_list + display_name + ':' + para + ' '
    return para_list

def connect_test(resource_group, aks = None, acr = None, webapp = None, sql = None,
                 mysql = None, asc = None, ascapp = None):
    if not resource_group:
        raise CLIError('--resource-group not specified')
    services_name = []
    para_list = ''
    service_list = []
    if acr:
        service_list.append(SERVICE_MAP['acr'])
        para_list = para_list + 'acr:' + acr + ' '
        services_name.append(acr)
    if aks:
        service_list.append(SERVICE_MAP['aks'])
        para_list = para_list + 'aks:' + aks + ' '
        services_name.append(aks)
    if webapp:
        service_list.append(SERVICE_MAP['webapp'])
        para_list = para_list + 'webapp:' + webapp + ' '
        services_name.append(webapp)
    if sql:
        service_list.append(SERVICE_MAP['sql'])
        para_list = para_list + 'sql:' + sql + ' '
        services_name.append(sql)
    if mysql:
        service_list.append(SERVICE_MAP['mysql'])
        para_list = para_list + 'mysql_server_name:' + mysql + ' '
        services_name.append(mysql)
    if asc:
        service_list.append(SERVICE_MAP['spring-cloud'])
        if not ascapp:
            raise CLIError('Need to input ASC App name using --ascapp.')
        para_list = para_list + 'asc_name:' + asc + ' '
        para_list = para_list + 'app_name:' + ascapp + ' '
        services_name.append(ascapp)
    service_list.sort(key=lambda x: x[2])
    para_dict = parseParameter(para_list)
    print('Resource Group %s services: %s' % (resource_group, ' and '.join([s[0] for s in service_list])))
    print('%s -> %s connected!!' % (services_name[0], services_name[1]))

def parseParameter(para_list):
    dict = {}
    for s in para_list.split():
        tmp = s.split(':',1)
        dict[tmp[0]] = tmp[1]
    return dict

def validate(service):
    result = []
    for s in service.split():
        if not s in SERVICE_MAP:
            raise CLIError('service %s is not recognized' % s)
        result.append(SERVICE_MAP[s])
    return sorted(result, key=lambda x: x[2])


def check_resource(service_list, resource_group):
    # print('Resource Group %s already exists.' % resource_group)
    print('Connecting %s in resource group %s.' % (', '.join([s[1] for s in service_list]), resource_group))
    # for s in service_list:
    #     print('Resource %s already exists.' % s[1])


def deploy(service_list, resource_group, para_dict):
    start = time.monotonic()
    deployment_id = random.randint(0, 1000000)
    settings = {}
    for service in service_list:
        create_resource(service, resource_group, deployment_id, settings, para_dict)
    print('Complete in %d seconds' % (time.monotonic() - start))

def get_resource_name(resource, deployment_id):
    return '%s%d' % (resource.lower(), deployment_id)


def create_resource(service, resource_group, deployment_id, settings, para_dict):
    if service[0] == 'signalr':
        # create SignalR resource
        resource_name = get_resource_name('mySignalR', deployment_id)
        print('Create %s resource: %s' % (service[1], resource_name))
        parameters = [
            'signalr', 'create',
            '--name', resource_name,
            '--resource-group', resource_group,
            '--sku', 'Standard_S1',
            '--unit-count', '1',
            '--service-mode', 'Default',
            '--output', 'none'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % resource_name)
        # get SignalR connection string
        parameters = [
            'signalr', 'key', 'list',
            '--name', resource_name,
            '--resource-group', resource_group,
            '--query', 'primaryConnectionString',
            '-o', 'tsv',
            '--output', 'none'
        ]
        DEFAULT_CLI.invoke(parameters)
        connection_string = DEFAULT_CLI.result.result
        settings['Azure:SignalR:ConnectionString'] = connection_string
        print('Connection string of %s: %s' % (resource_name, connection_string))
    
    elif service[0] == 'sql':
        # # create sql server
        # parameters = [
        #     'sql', 'server', 'create',
        #     '--name', server,
        #     '--resource-group', resource_group,
        #     '--location', 'east us',
        #     '--admin-user', username,
        #     '--admin-password', password
        # ]
        # if DEFAULT_CLI.invoke(parameters):
        #     raise CLIError('Fail to create resource %s' % server)
        # # config server firewall rule
        # parameters = [
        #     'sql', 'server', 'firewall-rule', 'create',
        #     '--server', server,
        #     '--resource-group', resource_group,
        #     '--name', 'AllowAllIps',
        #     '--start-ip-address', '0.0.0.0',
        #     '--end-ip-address', '0.0.0.0'
        # ]
        # DEFAULT_CLI.invoke(parameters)
        # # create sql db
        # parameters = [
        #     'sql', 'sql', 'db', 'create',
        #     '--server', server,
        #     '--resource-group', resource_group,
        #     '--name', sql,
        #     '--service-objective', '50'
        # ]
        # if DEFAULT_CLI.invoke(parameters):
        #     raise CLIError('Fail to create resource %s' % sql)
        # save connection string
        if 'msi' not in para_dict:
            connection_string = "Server=tcp:" + para_dict['sql'] + ".database.windows.net,1433;Database=" + para_dict['database'] + ";User ID=" + para_dict['username'] + ";Password=" + para_dict['password'] + ";Encrypt=true;Connection Timeout=30;"
            settings['MyDbConnection'] = connection_string
            print('Connection string of %s: %s' % (para_dict['database'], connection_string))
        else:
            parameters = [
                'webapp', 'identity', 'assign',
                '--resource-group', resource_group,
                '--name', para_dict['webapp'],
                '--output', 'none'
            ]
            DEFAULT_CLI.invoke(parameters)
            statement = "CREATE USER [" + para_dict['webapp'] + "] FROM EXTERNAL PROVIDER; ALTER ROLE db_datareader ADD MEMBER [" + para_dict['webapp'] + "]; ALTER ROLE db_datawriter ADD MEMBER [" + para_dict['webapp'] + "]; ALTER ROLE db_ddladmin ADD MEMBER [" + para_dict['webapp'] + "];"
            server = para_dict['sql'] + ".database.windows.net"
            subprocess.call(["sqlcmd", "-S", server, "-d", para_dict['database'], "-U", para_dict['aad-user'], "-G", "-l", "30", '-Q', statement])
    
    elif service[0] == 'webapp':
        # create App Service plan
        # plan_name = get_resource_name('myAppService', deployment_id)
        # print('Create App Service Plan: %s' % plan_name)
        # parameters = [
        #     'appservice', 'plan', 'create',
        #     '--name', plan_name,
        #     '--resource-group', resource_group,
        #     '--sku', 'FREE'
        # ]
        # if DEFAULT_CLI.invoke(parameters):
        #     raise CLIError('Fail to create resource %s' % plan_name)
        # # create Web App resource
        # resource_name = get_resource_name('myWebApp', deployment_id)
        # print('Create %s resource: %s' % (service[1], resource_name))
        # parameters = [
        #     'webapp', 'create',
        #     '--name', resource_name,
        #     '--resource-group', resource_group,
        #     '--plan', plan_name
        # ]
        # if DEFAULT_CLI.invoke(parameters):
        #     raise CLIError('Fail to create resource %s' % resource_name)
        # # config app settings
        # print('Config app settings')
        # parameters = [
        #     'webapp', 'config', 'appsettings', 'set',
        #     '--name', resource_name,
        #     '--resource-group', resource_group,
        #     '--settings'
        # ]
        # settings['PROJECT'] = 'samples/ChatRoom/ChatRoom.csproj'
        # for k, v in settings.items():
        #     parameters.append('%s=%s' % (k, v))
        # DEFAULT_CLI.invoke(parameters)
        # # deploy sample code
        # url = 'https://github.com/aspnet/AzureSignalR-samples'
        # print('Deploy sample code from %s/samples/ChatRoom' % url)
        # parameters = [
        #     'webapp', 'deployment', 'source', 'config',
        #     '--name', resource_name,
        #     '--resource-group', resource_group,
        #     '--repo-url', url,
        #     '--branch', 'master',
        #     '--manual-integration'
        # ]
        # DEFAULT_CLI.invoke(parameters)
        # print('App url: http://%s.azurewebsites.net/' % resource_name)
        if 'msi' not in para_dict:
            print("Using connection-string to connect Webapp and SQL.")
            parameters = [
                'webapp', 'config', 'connection-string', 'set',
                '--name', para_dict['webapp'],
                '--resource-group', resource_group,
                '--connection-string-type', 'SQLServer',
                '--settings',
                '--output', 'none'
            ]
            for k, v in settings.items():
                parameters.append('%s=%s' % (k, v))
            DEFAULT_CLI.invoke(parameters)
            parameters = [
                'webapp', 'config', 'appsettings', 'set',
                '--name', para_dict['webapp'],
                '--resource-group', resource_group,
                '--settings', 'ASPNETCORE_ENVIRONMENT=Production',
                '--output', 'none'
            ]
            DEFAULT_CLI.invoke(parameters)
        # else:
        #     print("Deploy to Webapp.")
        #     parameters = [
        #         'webapp', 'deployment', 'source', 'config',
        #         '-n', para_dict['webapp'],
        #         '-g', resource_group,
        #         '--repo-url', "https://github.com/KennethBWSong/dotnetcore-sqldb-tutorial.git",
        #         '--branch', 'msi',
        #         '--manual-integration'
        #     ]
        #     DEFAULT_CLI.invoke(parameters)

    elif service[0] == 'aks':
        # parameters = [
        #     'aks', 'show', 
        #     '--resource-group', resource_group,
        #     '--name', para_dict['aks'],
        #     '--query', 'servicePrincipalProfile.clientId',
        #     '--output', 'none'
        # ]
        # DEFAULT_CLI.invoke(parameters)
        # sp_id = DEFAULT_CLI.result.result
        # print('Service Principal id: %s' % sp_id)
        # if 'aks_secret' in para_dict:
        #     sp_password = para_dict['aks_secret']
        #     print('Password of Service Principal %s: %s' % (sp_id, sp_password))
        # else:
        #     print('Reset service principal password.')
        #     parameters = [
        #     'ad', 'sp', 'credential', 'reset',
        #     '--name', sp_id,
        #     '--query', 'password'
        #     ]
        #     DEFAULT_CLI.invoke(parameters)
        #     sp_password = DEFAULT_CLI.result.result
        #     print('Password of Service Principal %s: %s' % (sp_id, sp_password))
        #     time.sleep(30)
        #     parameters = [
        #     'aks', 'update-credentials', 
        #     '-n', para_dict['aks_name'],
        #     '-g', resource_group,
        #     '--service-principal', sp_id,
        #     '--client-secret', sp_password,
        #     '--reset-service-principal'
        #     ]
        #     DEFAULT_CLI.invoke(parameters)
        parameters = [
            'aks', 'update', 
            '-n', para_dict['aks'],
            '-g', resource_group,
            '--attach-acr', para_dict['acr'],
            '--output', 'none'
        ]
        DEFAULT_CLI.invoke(parameters)
    elif service[0] == 'cosmosdb':
        cosmosdb_handler(resource_group, deployment_id, settings, para_dict)
    elif service[0] == 'mysql':
        mysql_handler(resource_group, deployment_id, settings, para_dict)
    elif service[0] == 'spring-cloud':
        spring_cloud_handler(resource_group, deployment_id, settings, para_dict)


def _is_resourcid(resource):
    return resource.startswith('/subscriptions/')


def _get_target_id(scope, sql=None, mysql=None, cosmos=None, database=None, signalR=None):
    if sql and database:
        sql = sql if _is_resourcid(sql) else '{0}/providers/Microsoft.Sql/servers/{1}'.format(scope, sql)
        return '{0}/databases/{1}/'.format(sql, database)
    if mysql and database:
        mysql = mysql if _is_resourcid(mysql) else '{0}/providers/Microsoft.DBforMySQL/servers/{1}'.format(scope, mysql)
        return '{0}/databases/{1}'.format(mysql, database)
    if cosmos and database:
        cosmos = cosmos if _is_resourcid(cosmos) else '{0}/providers/Microsoft.DocumentDb/databaseAccounts/{1}'.format(scope, cosmos)
        return '{0}/databases/{1}'.format(cosmos, database)
    if signalR:
        return signalR if _is_resourcid(signalR) else '{0}/providers/Microsoft.SignalRService/signalR/{1}'.format(scope, signalR)
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
        end = result.text.find('\r\n\r\nHEADERS\r\n=======')
        msg = result.text[:end] if end > -1 else result.text
        err_msg = 'Fail to bind {0} with {1}. Code:{2}. Detail:{3}'.format(source, target, result.status_code, msg)
        raise Exception(err_msg)
    res_obj = json.loads(result.text)
    return res_obj


def bind_webapp(
    cmd, resource_group, name, appname, authtype='MSI', permission=None,
    sql=None, cosmos=None, database=None, client_id=None,
    client_secret=None, username=None, password=None
):
    try:
        subscription = get_subscription_id(cmd.cli_ctx)
        scope = '/subscriptions/{0}/resourceGroups/{1}'.format(subscription, resource_group)
        source = '{0}/providers/Microsoft.Web/sites/{1}'.format(scope, appname)
        target = _get_target_id(scope, sql=sql, cosmos=cosmos, database=database)
        result = _bind(
            cmd, subscription, resource_group, name, source,
            target, authtype, permission, client_id, client_secret, username, password
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(e)
        logger.error(e)


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


def validate_general(cmd, resource_group, name):
    try:
        subscription = get_subscription_id(cmd.cli_ctx)
        api = _create_api(cmd)
        result = api.validate(subscription, resource_group, name)
        if result.ok is not True:
            end = result.text.find('\r\n\r\nHEADERS\r\n=======')
            msg = result.text[:end] if end > -1 else result.text
            err_msg = 'Fail to validate the connection {0}. Code:{1}. Detail:{2}'.format(name, result.status_code, msg)
            raise Exception(err_msg)
        res_obj = json.loads(result.text)
        print(json.dumps(res_obj, indent=2))
    except Exception as e:
        print(e)
        logger.error(e)


def init_app(cmd):
    from ._app_sample import sample_source_list, sample_name_list
    sample_index = prompt_choice_list("select one", sample_name_list,
                                      default=0)

    from ._gitClient import download_source
    download_source(url=sample_source_list[sample_index], location=".")

    from ._app import App
    from ._appClient import create_app
    with open("./app_samples/"+sample_name_list[sample_index]+".json", 'r') as f:
        import uuid
        app_hash = uuid.uuid4().hex
        app = App(data=f)
        app.name = sample_name_list[sample_index]+app_hash
        app.save()

