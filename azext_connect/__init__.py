# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from knack.help_files import helps
from .commands import load_command_table
from ._params import load_arguments


helps['connect'] = """
    type: command
    short-summary: Connect Azure services.
    examples:
        - name: Provision and deploy demo code for Azure services.
          text: az connect --webapp myWebApp --sql mySql --resource-group rg
"""


class ConnectCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        custom_type = CliCommandType(operations_tmpl='azext_connect.custom#{}')
        super(ConnectCommandsLoader, self).__init__(
            cli_ctx=cli_ctx, custom_command_type=custom_type)

    def load_command_table(self, args):
        load_command_table(self,args)
        return self.command_table

    def load_arguments(self, command):
        load_arguments(self, command)


COMMAND_LOADER_CLS = ConnectCommandsLoader