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
    'webapp': ('webapp', 'Azure Web App Service', 2)
}
DEFAULT_CLI = get_default_cli()


def connect(service, resource_group=None):
    if not resource_group:
        raise CLIError('--resource-group not specified')
    service_list = validate(service)
    check_resource(service_list, resource_group)
    deploy(service_list, resource_group)


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


def deploy(service_list, resource_group):
    start = time.monotonic()
    deployment_id = random.randint(0, 1000000)
    settings = {}
    for service in service_list:
        create_resource(service, resource_group, deployment_id, settings)
    print('Complete in %d seconds' % (time.monotonic() - start))


def get_resource_name(resource, deployment_id):
    return '%s%d' % (resource.lower(), deployment_id)


def create_resource(service, resource_group, deployment_id, settings):
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
    elif service[0] == 'webapp':
        # create App Service plan
        plan_name = get_resource_name('myAppService', deployment_id)
        print('Create App Service Plan: %s' % plan_name)
        parameters = [
            'appservice', 'plan', 'create',
            '--name', plan_name,
            '--resource-group', resource_group,
            '--sku', 'FREE'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % plan_name)
        # create Web App resource
        resource_name = get_resource_name('myWebApp', deployment_id)
        print('Create %s resource: %s' % (service[1], resource_name))
        parameters = [
            'webapp', 'create',
            '--name', resource_name,
            '--resource-group', resource_group,
            '--plan', plan_name
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create resource %s' % resource_name)
        # config app settings
        print('Config app settings')
        parameters = [
            'webapp', 'config', 'appsettings', 'set',
            '--name', resource_name,
            '--resource-group', resource_group,
            '--settings'
        ]
        settings['PROJECT'] = 'samples/ChatRoom/ChatRoom.csproj'
        for k, v in settings.items():
            parameters.append('%s=%s' % (k, v))
        DEFAULT_CLI.invoke(parameters)
        # deploy sample code
        url = 'https://github.com/aspnet/AzureSignalR-samples'
        print('Deploy sample code from %s/samples/ChatRoom' % url)
        parameters = [
            'webapp', 'deployment', 'source', 'config',
            '--name', resource_name,
            '--resource-group', resource_group,
            '--repo-url', url,
            '--branch', 'master',
            '--manual-integration'
        ]
        DEFAULT_CLI.invoke(parameters)
        print('App url: http://%s.azurewebsites.net/' % resource_name)
