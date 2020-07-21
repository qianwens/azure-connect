class Service:
    def __init__(self, name, type, env, **kwargs):
        self.name = name
        self.type = type
        self.properties = kwargs
        self.env = env


class Database:
    def __init__(self, name, type):
        self.name = name
        self.type = type


class Environment:
    def __init__(self, resource_group, location):
        self.resource_group = resource_group
        self.location = location


class App:
    self.app_version = "v1"
    self.name = None
    self.resource_name_suffix = None
    self.services = []
    self.databases = []
    self.environments = {}

    def __init__(self, data):
        if data:
            import json
            self.__dict__ = json.loads(data)

    def add_service(self, service):
        self.services.append(service)

    def add_db(self, db):
        self.databases.append(db)

    def add_env(self, name, env):
        self.environments[name] = env
