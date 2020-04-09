# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.core import get_default_cli
import random
import time


SERVICE_MAP = {
    'signalr': ('signalr', 'Azure SignalR Service', 1),
    'sql': ('sql', 'Azure SQL Database', 2),
    'webapp': ('webapp', 'Azure Web App Service', 3),
    'acr': ('acr', 'Azure Container Registry', 4),
    'aks': ('aks', 'Azure Kubernetes Service', 5)
}
DEFAULT_CLI = get_default_cli()


def connect(service, resource_group, para_list):
    if not resource_group:
        raise CLIError('--resource-group not specified')
    service_list = validate(service)
    check_resource(service_list, resource_group)
    para_dict = parseParameter(para_list)
    # print(para_dict)
    deploy(service_list, resource_group, para_dict)

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
    print('Resource Group %s already exists.' % resource_group)
    print('Connecting %s in resource group %s.' % (', '.join([s[1] for s in service_list]), resource_group))
    for s in service_list:
        print('No %s found.' % s[1])


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
            '--service-mode', 'Default'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % resource_name)
        # get SignalR connection string
        parameters = [
            'signalr', 'key', 'list',
            '--name', resource_name,
            '--resource-group', resource_group,
            '--query', 'primaryConnectionString',
            '-o', 'tsv'
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
        connection_string = "Server=tcp:" + para_dict['server'] + ".database.windows.net,1433;Database=" + para_dict['sql'] + ";User ID=" + para_dict['username'] + ";Password=" + para_dict['password'] + ";Encrypt=true;Connection Timeout=30;"
        settings['MyDbConnection'] = connection_string
        print('Connection string of %s: %s' % (para_dict['sql'], connection_string))
    
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
        parameters = [
            'webapp', 'config', 'connection-string', 'set',
            '--name', para_dict['app_name'],
            '--resource-group', resource_group,
            '--connection-string-type', 'SQLServer',
            '--settings'
        ]
        for k, v in settings.items():
            parameters.append('%s=%s' % (k, v))
        DEFAULT_CLI.invoke(parameters)
        parameters = [
            'webapp', 'config', 'appsettings', 'set',
            '--name', para_dict['app_name'],
            '--resource-group', resource_group,
            '--settings', 'ASPNETCORE_ENVIRONMENT=Production'
        ]
        DEFAULT_CLI.invoke(parameters)

    elif service[0] == 'aks':
        parameters = [
        'aks', 'update', 
        '-n', para_dict['aks_name'],
        '-g', resource_group,
        '--attach-acr', para_dict['acr_name']
        ]
        DEFAULT_CLI.invoke(parameters)
