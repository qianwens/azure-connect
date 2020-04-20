from knack.help_files import helps  # pylint: disable=unused-import

helps['connect services'] = """
    type: command
    short-summary: Connect Azure services.
    examples:
        - name: Connect two Azure services.
          text: az connect services --webapp myWebApp --sql mySql --resource-group rg
"""

helps['connect test'] = """
    type: command
    short-summary: Test connection of Azure services.
    examples:
        - name: Test whether two Azure services are connected.
          text: az connect test --webapp myWebApp --sql mySql --resource-group rg
"""