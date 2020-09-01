from knack.help_files import helps  # pylint: disable=unused-import

helps['connect webapp bind'] = """
    type: command
    short-summary: Connect webapp and other Azure services.
    examples:
        - name: Connect webapp and sql db.
          text: az connect webapp bind --connection-name myconnection --sql-server mysqlserver --database-name dbname --resource-group rg --auth-type Secret
"""

helps['connect webapp postgres bind'] = """
    type: command
    short-summary: Connect webapp and postgres database.
    examples:
        - name: Connect webapp and postgres database with local-context turns on.
          text: az connect webapp postgres bind
"""

helps['connect springcloud bind'] = """
    type: command
    short-summary: Connect springcloud and other Azure services.
    examples:
        - name: Connect springcloud and mysql database.
          text: az connect springcloud bind --connection-name myconnection -spc spcaccount -app appname --mysql-server mySql --database-name dbname -user username -pwd password --resource-group rg
"""

helps['connect function bind'] = """
    type: command
    short-summary: Connect function and other Azure services.
    examples:
        - name: Connect function and signalR.
          text: az connect function bind --connection-name myconnection -app appname -func funcname -signalr signalrname -binding input --resource-group rg
"""

helps['connect validate'] = """
    type: command
    short-summary: Validate the connection.
    examples:
        - name: Validate the connection.
          text: az connect validate -n connectionname --resource-group rg
"""

helps['connect get'] = """
    type: command
    short-summary: Get the connection properties.
    examples:
        - name: Get the connection properties.
          text: az connect get -name connectionname --resource-group rg
"""
