from azure.cli.core.commands.parameters import get_enum_type
from ._model import AuthType


def load_arguments(self, _):
    with self.argument_context('connect') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resource group to provision services.')
        c.argument('acr', options_list=['--acr'], help='ACR name.')
        c.argument('aks', options_list=['--aks'], help='AKS name.')
        c.argument('webapp', options_list=['--webapp'], help='Webapp Name')
        c.argument('sql', options_list=['--sql'], help='SQL Server name')
        c.argument('mysql', options_list=['--mysql'], help='MySQL Server name')
        c.argument('asc', options_list=['--asc'], help='Azure Spring Cloud name')
        c.argument('ascapp', options_list=['--ascapp'], help='Azure Spring Cloud App name')

    with self.argument_context('cupertino webapp') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resource group to provision services.')
        c.argument('name', options_list=['--connection-name', '-n'], help='Connection name')
        c.argument('appname', options_list=['--app-name', '-app'], help='Webapp name')
        c.argument('sql', options_list=['--sql-server', '-sql'], help='SQL server name in the same resource group or SQL server ID')
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

    with self.argument_context('cupertino springcloud') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resource group to provision services.')
        c.argument('name', options_list=['--connection-name', '-n'], help='Connection name')
        c.argument('springcloud', options_list=['--spring-cloud', '-spc'], help='spring cloud name')
        c.argument('appname', options_list=['--app-name', '-app'], help='Webapp name')
        c.argument('mysql', options_list=['--mysql-server', '-mysql'], help='SQL server name in the same resource group or mysql server ID')
        c.argument('cosmos', options_list=['--cosmos-account', '-cosmos'], help='CosmosDB Account name')
        c.argument('database', options_list=['--database-name', '-db'], help='Database name')
        c.argument('username', options_list=['--user-name', '-user'], help='User name of the database. Only valid when auth type is secret')
        c.argument('password', options_list=['--password', '-pwd'], help='Password of the database. Only valid when auth type is secret')

    with self.argument_context('cupertino function') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resource group to provision services.')
        c.argument('name', options_list=['--connection-name', '-n'], help='Connection name')
        c.argument('appname', options_list=['--app-name', '-app'], help='Function app name')
        c.argument('function_name', options_list=['--function-name', '-func'], help='Function name')
        c.argument('signalR', options_list=['--signalr', '-signalr'], help='SignalR service name')
        c.argument('binding', options_list=['--binding-type', '-binding'], help='The binding type of the function')

    with self.argument_context('cupertino validate') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resource group to provision services.')
        c.argument('name', options_list=['--connection-name', '-n'], help='Connection name')
