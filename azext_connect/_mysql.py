from knack.util import CLIError
from azure.cli.core import get_default_cli

DEFAULT_CLI = get_default_cli()

def mysql_handler(resource_group, deployment_id, settings, para_dict):
    # parse the parameters
    mysql_server_name = para_dict['mysql_server_name']
    admin_user = para_dict['admin_user']
    admin_password = para_dict['admin_password']
    database_name = para_dict['database_name']

    # Get azure resource id which is needed by asc app binding service
    parameters = [
        'mysql', 'server', 'show',
        '--name', mysql_server_name,
        '--resource-group', resource_group,
        '--output', 'None'
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to get information of MySQL server %s.' % mysql_server_name)
    resource_id = DEFAULT_CLI.result.result['id']
    '''
    # config firewall rule
    parameters = [
        'mysql', 'server', 'firewall-rule', 'create',
        '--resource-group', resource_group,
        '--server-name', mysql_server_name,
        '--name', 'AllowMyIp',
        '--start-ip-address', '0.0.0.0',
        '--end-ip-address', '255.255.255.255'
        '--output', 'None'
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to configure firewall rule for %s.' % mysql_server_name)
    # config SSL settings
    parameters = [
        'mysql', 'server', 'update',
        '--resource-group', resource_group,
        '--name', mysql_server_name,
        '--ssl-enforcement', 'Disabled'
        '--output', 'None'
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to configure SSL settings for %s.' % mysql_server_name)
    '''
    settings['mysql_resource_id'] = resource_id
    settings['binding_type'] = 'Azure Database for MySQL'
    settings['username'] = admin_user
    settings['key'] = admin_password
    settings['database_name'] = database_name