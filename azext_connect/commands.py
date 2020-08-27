def load_command_table(self, _):
    with self.command_group('connect webapp') as g:
        g.custom_command('bind', 'bind_webapp')
    with self.command_group('connect webapp postgres') as g:
        g.custom_command('bind', 'bind_webapp_postgres')
    with self.command_group('connect springcloud') as g:
        g.custom_command('bind', 'bind_springcloud')
    with self.command_group('connect function') as g:
        g.custom_command('bind', 'bind_function')
    with self.command_group('connect') as g:
        g.custom_command('validate', 'validate_general')
    with self.command_group('connect') as g:
        g.custom_command('get', 'get_general')
