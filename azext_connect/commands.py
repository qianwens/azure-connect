def load_command_table(self, _):
    with self.command_group('app') as g:
        g.custom_command('create', 'init_app')
        g.custom_command('deploy', 'deploy_app')
        g.custom_command('run', 'run_command')
        g.custom_command('log', 'download_log')
        g.custom_command('show', 'show_app')
        g.custom_command('db migrate', 'migrate_db')
        g.custom_command('local', 'local')
        g.custom_command('open', 'open_app')

    with self.command_group('connect') as g:
        g.custom_command('services', 'connect')
        g.custom_command('test', 'connect_test')

    with self.command_group('cupertino webapp') as g:
        g.custom_command('bind', 'bind_webapp')
        # g.custom_command('remove', '')
        # g.custom_command('list', '')
    with self.command_group('cupertino springcloud') as g:
        g.custom_command('bind', 'bind_springcloud')
    with self.command_group('cupertino function') as g:
        g.custom_command('bind', 'bind_function')
    with self.command_group('cupertino') as g:
        g.custom_command('validate', 'validate_general')
