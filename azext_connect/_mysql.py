from knack.util import CLIError
from azure.cli.core import get_default_cli

DEFAULT_CLI = get_default_cli()

def mysql_handler(resource_group, deployment_id, settings, para_dict):
    # parse the parameters
    mysql_server_name = para_dict['mysql_server_name']
    admin_user = para_dict['admin_user']
    admin_password = para_dict['admin_password']
    subscription_id = para_dict['subscription_id']
    database_name = para_dict['database_name']

    # check if mysql server availability
    parameters = [
        'mysql', 'server', 'show',
        '--name', mysql_server_name,
        '--resource-group', resource_group
    ]
    try:
        DEFAULT_CLI.invoke(parameters)
    except:
        # not exists, create a new one
        parameters = [
            'mysql', 'server', 'create',
            '--resource-group', resource_group,
            '--name', mysql_server_name,
            '--location', 'westus2',
            '--admin-user', admin_user,
            '--admin-password', admin_password,
            '--sku-name', 'GP_Gen5_2',
            '--version', '5.7'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create MySQL server %s.' % mysql_server_name)
    # config firewall rule
    parameters = [
        'mysql', 'server', 'firewall-rule', 'create',
        '--resource-group', resource_group,
        '--server-name', mysql_server_name,
        '--name', 'AllowMyIp',
        '--start-ip-address', '0.0.0.0',
        '--end-ip-address', '255.255.255.255'
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to configure firewall rule for %s.' % mysql_server_name)

    # config SSL settings
    parameters = [
        'mysql', 'server', 'update',
        '--resource-group', resource_group,
        '--name', mysql_server_name,
        '--ssl-enforcement', 'Disabled'
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to configure SSL settings for %s.' % mysql_server_name)

    # Create database, check if it exists, if not create it
    parameters = [
        'mysql', 'db', 'show',
        '--name', database_name,
        '--server-name', mysql_server_name,
        '--resource-group', resource_group
    ]
    try:
        DEFAULT_CLI.invoke(parameters)
    except:
        parameters = [
            'mysql', 'db', 'create',
            '--name', database_name,
            '--server-name', mysql_server_name,
            '--resource-group', resource_group
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create database %s for server %s.' % (database_name, mysql_server_name))
        
    # optional get connection info
    parameters = [
        'mysql', 'server', 'show',
        '--name', mysql_server_name,
        '--resource-group', resource_group
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to get %s server info.' % mysql_server_name)
    resource_id = "/subscriptions/" + subscription_id + "/resourceGroups/" + resource_group + "/providers/Microsoft.DBforMySQL/servers/" + mysql_server_name
    settings['mysql_resource_id'] = resource_id
    settings['binding_type'] = 'Azure Database for MySQL'
    settings['username'] = admin_user
    settings['key'] = admin_password
    settings['database_name'] = database_name
    print('MySQL Server %s is ready.' % mysql_server_name)