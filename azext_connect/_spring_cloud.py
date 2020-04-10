from knack.util import CLIError
from azure.cli.core import get_default_cli
import time

DEFAULT_CLI = get_default_cli()

def spring_cloud_handler(resource_group, deployment_id, settings, para_dict):
    # parse the parameter
    asc_name = para_dict['asc_name']
    app_name = para_dict['app_name']
    binding_name = para_dict['binding_name']
    jar_path = para_dict['jar_path']
    resource_id = settings['cosmosdb_resource_id']
    database_name = settings['database_name']
    # check azure spring-cloud service
    parameters = [
        'spring-cloud', 'show',
        '--resource-group', resource_group,
        '--name', asc_name
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Azure Spring Cloud service %s does not exist, please create it and retry the command.' % asc_name)
    # create app
    # check if app exists
    parameters = [
        'spring-cloud', 'app', 'show',
        '--name', app_name,
        '--service', asc_name,
        '--resource-group', resource_group
    ]
    if DEFAULT_CLI.invoke(parameters):
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
    else:
        print('App %s already exists.' % app_name)
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
    wait = 30
    print('Waiting %d seconds for APP instance running up...' % wait)
    time.sleep(wait)
    parameters = [
        'spring-cloud', 'app', 'show',
        '--name', app_name,
        '--service', asc_name,
        '--resource-group', resource_group
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to show App %s status.' % app_name)
    print('App url: %s' % DEFAULT_CLI.result.result['properties']['url'])
