# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from knack.help_files import helps


helps['connect'] = """
    type: command
    short-summary: Connect Azure services.
    examples:
        - name: Provision and deploy demo code for Azure services.
          text: az connect 'webapp signalr' --resource-group rg
"""


class ConnectCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        custom_type = CliCommandType(operations_tmpl='azext_connect.custom#{}')
        super(ConnectCommandsLoader, self).__init__(
            cli_ctx=cli_ctx, custom_command_type=custom_type)

    def load_command_table(self, _):
        with self.command_group('') as g:
            g.custom_command('connect', 'connect')
        return self.command_table

    def load_arguments(self, _):
        with self.argument_context('connect') as c:
            c.positional('service', help='Service you want to connect, use space as delimiter for multiple services.')
            c.argument('resource_group', options_list=['--resource-group', '-g'], help='Resouce group to provision services.')
            # c.argument('app_name', options_list = ['--app-name'], help = 'Webapp name.')
            # c.argument('server', options_list = ['--server'], help = 'Server name.')
            # c.argument('sql', options_list = ['--sql'], help = 'SQL name.')
            # c.argument('username', options_list = ['--user-name'], help = 'User name of the SQL db.')
            # c.argument('password', options_list = ['--password'], help = 'User password of the SQL db.')
            # c.argument('aks_name', options_list = ['--aks-name'], help = 'AKS Name.')
            # c.argument('acr_name', options_list = ['--acr-name'], help = 'ACR Name.')
            c.argument('para_list', options_list = ['--para-list'], help = 'All the necessary parameters.')


COMMAND_LOADER_CLS = ConnectCommandsLoader