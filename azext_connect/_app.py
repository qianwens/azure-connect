class Service:
    def __init__(self, name, type, env, source, **kwargs):
        self.name = name
        self.type = type
        self.properties = kwargs
        self.env = env
        self.source = source


class Addon:
    def __init__(self, name, type):
        self.name = name
        self.type = type


class Environment:
    def __init__(self, resource_group, location):
        self.resourceGroup = resource_group
        self.location = location


class App:
    app_version = "v1"
    name = None
    id_suffix = None
    services = []
    addons = []
    environments = {}

    def __init__(self, data):
        if data:
            import json
            self.__dict__ = json.loads(data)

    def add_service(self, service):
        self.services.append(service)

    def add_db(self, db):
        self.addons.append(db)

    def add_env(self, name, env):
        self.environments[name] = env
