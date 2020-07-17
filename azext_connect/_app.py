class Service:
    def __init__(self, name, type):
        self.name = name
        self.type = type


class Database:
    def __init__(self, name, type):
        self.name = name
        self.type = type


class Environment:
    def __init__(self, name, resource_group_name, location):
        self.name = name
        self.resource_group_name = resource_group_name
        self.location = location


class App:
    self.app_version = "v1"
    self.name = None
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

    def add_env(self, env):
        self.environments.append(env)
