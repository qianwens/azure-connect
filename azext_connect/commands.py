def load_command_table(self, _):
    with self.command_group('connect') as g:
        g.custom_command('services', 'connect')
        g.custom_command('test', 'connect_test')

    with self.command_group('cupertino webapp') as g:
        g.custom_command('bind', '')
        g.custom_command('remove', '')
        g.custom_command('list', '')