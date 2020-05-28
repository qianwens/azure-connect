from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import (
    name_type,
    resource_group_name_type,
    get_enum_type,
    get_location_type,
    get_resource_name_completion_list,
    get_three_state_flag
)



webapp_name_type = CLIArgumentType(
    completer=get_resource_name_completion_list('Microsoft.Web/sites'),
    help='Web App name.',
)

sql_name_type = CLIArgumentType(
    completer=get_resource_name_completion_list('Microsoft.Sql/servers'),
    help='SQL Server name.',
)

def load_arguments(self, _):
    with self.argument_context('connect') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resouce group to provision services.')
        c.argument('acr', options_list = ['--acr'], help = 'ACR name.')
        c.argument('aks', options_list = ['--aks'], help = 'AKS name.')
        c.argument('webapp', options_list = ['--webapp'], help = 'Webapp Name')
        c.argument('sql', options_list = ['--sql'], help = 'SQL Server name')
        c.argument('mysql', options_list = ['--mysql'], help = 'MySQL Server name')
        c.argument('asc', options_list = ['--asc'], help = 'Azure Spring Cloud name')
        c.argument('ascapp', options_list = ['--ascapp'], help = 'Azure Spring Cloud App name')

    with self.argument_context('cupertino webapp') as c:
        c.argument('name', options_list=['--app-name', 'n'], arg_type=webapp_name_type)
        c.argument('sql', option_list=['--sql-name', 'n'], arg_type=sql_name_type)
