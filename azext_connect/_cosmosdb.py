from knack.util import CLIError
from azure.cli.core import get_default_cli

DEFAULT_CLI = get_default_cli()

def cosmosdb_handler(resource_group, deployment_id, settings, para_dict):
    # parse the parameters
    cosmosdb_name = para_dict['cosmosdb_name']
    database_name = para_dict['database_name']
    container_name = para_dict['container_name']
    partition_key_path = para_dict['partition_key_path']
    subscription_id = para_dict['subscription_id']
    # check if cosmosdb account exists
    parameters = [
        'cosmosdb', 'check-name-exists',
        '--name', cosmosdb_name
    ]
    DEFAULT_CLI.invoke(parameters)
    if DEFAULT_CLI.result.result == 'false':
        print('Azure CosmosDB Account %s does not exist, please create it and retry the command.' % cosmosdb_name)
        return
    # create database and container
    parameters = [
        'cosmosdb', 'sql', 'database', 'create',
        '--account-name', cosmosdb_name,
        '--name', database_name,
        '--resource-group', resource_group
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to create database %s' % database_name)
    # create container
    parameters = [
        'cosmosdb', 'sql', 'container', 'create',
        '--account-name', cosmosdb_name,
        '--database-name', database_name,
        '--name', container_name,
        '--partition-key-path', partition_key_path
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to create container %s' % container_name)
    resource_id = "/subscriptions/" + subscription_id + "/resourceGroups/" + resource_group + "/providers/Microsoft.DocumentDB/databaseAccounts/" + cosmosdb_name
    settings['cosmosdb_resource_id'] = resource_id
    settings['database_name'] = database_name
    print('CosmosDB %s database %s is ready.' % (cosmosdb_name, database_name))


