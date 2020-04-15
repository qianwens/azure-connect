from knack.util import CLIError
from azure.cli.core import get_default_cli
import time
import os
import sys

DEFAULT_CLI = get_default_cli()

SERVICE_BINDING_TYPE = [
    'Azure Cosmos DB',
    'Azure Cache for Redis',
    'Azure Database for MySQL'
]

def spring_cloud_handler(resource_group, deployment_id, settings, para_dict):
    # parse the parameter
    asc_name = para_dict['asc_name']
    app_name = para_dict['app_name']
    jar_path = para_dict['jar_path']
    binding_name = para_dict['binding_name']
    binding_type = settings['binding_type']
    if binding_type == SERVICE_BINDING_TYPE[0]:
        resource_id = settings['cosmosdb_resource_id']
        database_name = settings['database_name']
    elif binding_type == SERVICE_BINDING_TYPE[2]:
        username = settings['username']
        key = settings['key']
        resource_id = settings['mysql_resource_id']
        database_name = settings['database_name']
    # check azure spring-cloud service
    parameters = [
        'spring-cloud', 'show',
        '--resource-group', resource_group,
        '--name', asc_name
    ]
    try:
        DEFAULT_CLI.invoke(parameters)
    except:
        # not exists, create a new one
        parameters = [
            'spring-cloud', 'create',
            '--name', asc_name,
            '--resource-group', resource_group
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create Azure Spring Cloud service %s.' % asc_name)
    # create app
    # check if app exists
    parameters = [
        'spring-cloud', 'app', 'show',
        '--name', app_name,
        '--service', asc_name,
        '--resource-group', resource_group
    ]
    try:
        DEFAULT_CLI.invoke(parameters)
    except:
        print('App %s does not exists, creating it...' % app_name)
        parameters = [
            'spring-cloud', 'app', 'create',
            '--name', app_name,
            '--service', asc_name,
            '--resource-group', resource_group,
            '--runtime-version', 'Java_11',
            '--is-public', 'true'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to crreat App %s for Azure Spring Cloud %s.' % (app_name, asc_name))
    finally:
        print('App %s created.' % app_name)
        parameters = [
            'spring-cloud', 'app', 'update',
            '--name', app_name,
            '--service', asc_name,
            '--resource-group', resource_group,
            '--runtime-version', 'Java_11'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to update App %s configuration.' % app_name)
    # deploy app
    parameters = [
        'spring-cloud', 'app', 'deploy',
        '--name', app_name,
        '--service', asc_name,
        '--resource-group', resource_group,
        '--jar-path', jar_path
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to deploy jar file %s to App %s.' % (jar_path, app_name))
    # binding DB
    if binding_type == SERVICE_BINDING_TYPE[0]:
        parameters = [
            'spring-cloud', 'app', 'binding', 'cosmos', 'add',
            '--api-type', 'sql',
            '--app', app_name,
            '--name', binding_name,
            '--resource-id', resource_id,
            '--service', asc_name,
            '--database-name', database_name,
            '--resource-group', resource_group
        ]
    elif binding_type == SERVICE_BINDING_TYPE[2]:
        parameters = [
            'spring-cloud', 'app', 'binding', 'mysql', 'add',
            '--name', binding_name,
            '--app', app_name,
            '--database-name', database_name,
            '--key', key,
            '--username', username,
            '--resource-id', resource_id,
            '--resource-group', resource_group
        ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to bind %s to App %s.' % (resource_id, app_name))
    # restart app
    parameters = [
        'spring-cloud', 'app', 'restart',
        '--name', app_name,
        '--service', asc_name,
        '--resource-group', resource_group
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to restart App %s.' % app_name)
    # check app status
    print("Polling App %s status..." % app_name)
    timeout = 10
    wait = 15
    f = open(os.devnull, 'w')
    while timeout > 0:
        parameters = [
            'spring-cloud', 'app', 'show',
            '--name', app_name,
            '--service', asc_name,
            '--resource-group', resource_group
        ]
        if DEFAULT_CLI.invoke(parameters, out_file=f):
            raise CLIError('Fail to show App %s status.' % app_name)
        if DEFAULT_CLI.result.result['properties']['activeDeployment']['properties']['status'] == 'Running':
            print('App %s running up.' % app_name)
            break
        timeout -= 1
        print('Wait %d seconds...' % wait)
        time.sleep(wait)
    if timeout <= 0:
        raise CLIError('Timeout polling App instance %s status for running up.' % app_name)
    print('App url: %s' % DEFAULT_CLI.result.result['properties']['url'])
