def load_command_table(self, _):
    with self.command_group('connect') as g:
        g.custom_command('services', 'connect')
        g.custom_command('test', 'connect_test')

    with self.command_group('cupertino webapp') as g:
        g.custom_command('bind', 'bind_webapp')
        # g.custom_command('remove', '')
        # g.custom_command('list', '')
    with self.command_group('cupertino webapp postgres') as g:
        g.custom_command('bind', 'bind_webapp_postgres')
    with self.command_group('cupertino springcloud') as g:
        g.custom_command('bind', 'bind_springcloud')
    with self.command_group('cupertino function') as g:
        g.custom_command('bind', 'bind_function')
    with self.command_group('cupertino') as g:
        g.custom_command('validate', 'validate_general')
    with self.command_group('cupertino') as g:
        g.custom_command('get', 'get_general')
