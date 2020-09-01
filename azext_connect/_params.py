from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import (resource_group_name_type, get_location_type,
                                                get_resource_name_completion_list, file_type,
                                                get_three_state_flag, get_enum_type, tags_type)
from azure.cli.core.local_context import LocalContextAction, LocalContextAttribute
from ._model import AuthType


def load_arguments(self, _):
    webapp_name_argument_type = CLIArgumentType(options_list=['--app-name', '-app'],
                                                help="name of the web app. You can configure the default using `az configure --defaults web=<name>`",
                                                local_context_attribute=LocalContextAttribute(name='web_name', actions=[LocalContextAction.GET]))
    postgres_server_name_argument_type = CLIArgumentType(options_list=['--server-name', '-s'],
                                                         help="name of the Postgres server or PostgreSql server ID.",
                                                         local_context_attribute=LocalContextAttribute(name='postgres_server_name', actions=[LocalContextAction.GET]))
    postgres_database_name_argument_type = CLIArgumentType(options_list=['--database-name', '-db'],
                                                           help="Database name",
                                                           local_context_attribute=LocalContextAttribute(name='postgres_database_name', actions=[LocalContextAction.GET]))
    postgres_database_username_argument_type = CLIArgumentType(options_list=['--user-name', '-user'],
                                                               help="User name of the database. Only valid when auth type is secret",
                                                               local_context_attribute=LocalContextAttribute(name='postgres_admin_user_name', actions=[LocalContextAction.GET]))
    with self.argument_context('connect webapp') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resource group to provision services.')
        c.argument('name', options_list=['--connection-name', '-n'], help='Connection name')
        c.argument('appname', options_list=['--app-name', '-app'], help='Webapp name')
        c.argument('sql', options_list=['--sql-server', '-sql'], help='SQL server name in the same resource group or SQL server ID')
        c.argument('mysql', options_list=['--mysql-server', '-mysql'], help='SQL server name in the same resource group or mysql server ID')
        c.argument('postgres', options_list=['--postgresql-server', '-postgres'], help ='PostgreSql server name in the same resource group or PostgreSql server ID')
        c.argument('cosmos', options_list=['--cosmos-account', '-cosmos'], help='CosmosDB Account name')
        c.argument('database', options_list=['--database-name', '-db'], help='Database name')
        c.argument(
            'authtype', options_list=['--auth-type', '-auth'], help='Auth type could be MSI, SP, Secret',
            arg_type=get_enum_type(AuthType)
        )
        c.argument('permission', options_list=['--permission', '-per'], help='The permission assigned to the identity or SP')
        c.argument('client_id', options_list=['--client-id', '-cid'], help='Client Id assigned to webapp. Only valid when auth type is SP')
        c.argument('client_secret', options_list=['--client-secret', '-secret'], help='Client secret of the client id. Only valid when auth type is SP')
        c.argument('username', options_list=['--user-name', '-user'], help='User name of the database. Only valid when auth type is secret')
        c.argument('password', options_list=['--password', '-pwd'], help='Password of the database. Only valid when auth type is secret')
        c.argument('keyvault', options_list=['--keyvault', '-kvt'], help='Keyvault name in the same resource group.')

    with self.argument_context('connect webapp postgres') as c:
        c.argument('resource_group', arg_type=resource_group_name_type)
        c.argument('name',  options_list=['--connection-name', '-n'], help='Connection name')
        c.argument('appname', arg_type=webapp_name_argument_type)
        c.argument('server', arg_type=postgres_server_name_argument_type)
        c.argument('database', arg_type=postgres_database_name_argument_type)
        c.argument(
            'authtype', options_list=['--auth-type', '-auth'], help='Auth type could be MSI, SP, Secret',
            arg_type=get_enum_type(AuthType))
        c.argument('permission', options_list=['--permission', '-per'], help='The permission assigned to the identity or SP')
        c.argument('client_id', options_list=['--client-id', '-cid'], help='Client Id assigned to webapp. Only valid when auth type is SP')
        c.argument('client_secret', options_list=['--client-secret', '-secret'], help='Client secret of the client id. Only valid when auth type is SP')
        c.argument('username', arg_type=postgres_database_username_argument_type)
        c.argument('password', options_list=['--password', '-pwd'], help='Password of the database. Only valid when auth type is secret')

    with self.argument_context('connect springcloud') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resource group to provision services.')
        c.argument('name', options_list=['--connection-name', '-n'], help='Connection name')
        c.argument('springcloud', options_list=['--spring-cloud', '-spc'], help='spring cloud name')
        c.argument('appname', options_list=['--app-name', '-app'], help='Webapp name')
        c.argument('mysql', options_list=['--mysql-server', '-mysql'], help='SQL server name in the same resource group or mysql server ID')
        c.argument('cosmos', options_list=['--cosmos-account', '-cosmos'], help='CosmosDB Account name')
        c.argument('database', options_list=['--database-name', '-db'], help='Database name')
        c.argument('username', options_list=['--user-name', '-user'], help='User name of the database. Only valid when auth type is secret')
        c.argument('password', options_list=['--password', '-pwd'], help='Password of the database. Only valid when auth type is secret')

    with self.argument_context('connect function') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resource group to provision services.')
        c.argument('name', options_list=['--connection-name', '-n'], help='Connection name')
        c.argument('appname', options_list=['--app-name', '-app'], help='Function app name')
        c.argument('function_name', options_list=['--function-name', '-func'], help='Function name')
        c.argument('signalR', options_list=['--signalr', '-signalr'], help='SignalR service name')
        c.argument('binding', options_list=['--binding-type', '-binding'], help='The binding type of the function: input or output')

    with self.argument_context('connect validate') as c:
        c.argument('resource_group', arg_type=resource_group_name_type)
        c.argument('name', options_list=['--connection-name', '-n'], help='Connection name')

    with self.argument_context('connect get') as c:
        c.argument('resource_group', arg_type=resource_group_name_type)
        c.argument('name', options_list=['--connection-name', '-n'], help='Connection name')
