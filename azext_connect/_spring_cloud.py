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
    binding_type = settings['binding_type']
    if binding_type == SERVICE_BINDING_TYPE[0]:
        binding_name = '%s%d' % ('cosmos', deployment_id)
        resource_id = settings['cosmosdb_resource_id']
        database_name = settings['database_name']
    elif binding_type == SERVICE_BINDING_TYPE[2]:
        binding_name = '%s%d' % ('mysql', deployment_id)
        username = settings['username']
        key = settings['key']
        resource_id = settings['mysql_resource_id']
        database_name = settings['database_name']
        
    if binding_type == SERVICE_BINDING_TYPE[0]:
        parameters = [
            'spring-cloud', 'app', 'binding', 'cosmos', 'add',
            '--api-type', 'sql',
            '--service', asc_name,
            '--app', app_name,
            '--name', binding_name,
            '--resource-id', resource_id,
            '--database-name', database_name,
            '--resource-group', resource_group
        ]
        print('Creating service binding for Spring Cloud App %s and CosmosDB database %s...' % (app_name, database_name))
    elif binding_type == SERVICE_BINDING_TYPE[2]:
        parameters = [
            'spring-cloud', 'app', 'binding', 'mysql', 'add',
            '--name', binding_name,
            '--service', asc_name,
            '--app', app_name,
            '--database-name', database_name,
            '--key', key,
            '--username', username,
            '--resource-id', resource_id,
            '--resource-group', resource_group
        ]
        print('Creating service binding for Spring Cloud App %s and MySQL database %s...' % (app_name, database_name))
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to bind %s to App %s.' % (resource_id, app_name))