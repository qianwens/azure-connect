from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import (
    name_type,
    resource_group_name_type,
    get_enum_type,
    get_location_type,
    get_resource_name_completion_list,
    get_three_state_flag
)
from ._model import AuthType



def load_arguments(self, _):
    with self.argument_context('connect') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resource group to provision services.')
        c.argument('acr', options_list = ['--acr'], help = 'ACR name.')
        c.argument('aks', options_list = ['--aks'], help = 'AKS name.')
        c.argument('webapp', options_list = ['--webapp'], help = 'Webapp Name')
        c.argument('sql', options_list = ['--sql'], help = 'SQL Server name')
        c.argument('mysql', options_list = ['--mysql'], help = 'MySQL Server name')
        c.argument('asc', options_list = ['--asc'], help = 'Azure Spring Cloud name')
        c.argument('ascapp', options_list = ['--ascapp'], help = 'Azure Spring Cloud App name')

    with self.argument_context('cupertino webapp') as c:
        # c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resource group to provision services.')
        c.argument('name', options_list=['--app-name', '-n'], help='Webapp name')
        c.argument('sql', options_list=['--sql-name', '-sql'], help='SQL server name in the same resource group or SQL server ID')
        c.argument('database', options_list=['--database-name', '-db'], help='Database name')
        c.argument('authtype', options_list=['--auth-type', '-auth'], help='Auth type could be MSI, SP, Secret', arg_type=get_enum_type(AuthType))
        c.argument('client_id', options_list=['--client-id', '-cid'], help='Client Id assigned to webapp. Only valid when auth type is SP')
        c.argument('client_secret', options_list=['--client-secret', '-secret'], help='Client secret of the client id. Only valid when auth type is SP')
        c.argument('username', options_list=['--user-name', '-user'], help='User name of the database. Only valid when auth type is secret')
        c.argument('password', options_list=['--password', '-pwd'], help='Password of the database. Only valid when auth type is secret')
