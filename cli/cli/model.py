from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Route(object):
    relative_url: str
    target: str

    http_methods: Optional[List[str]] = None
    cors: Optional[bool] = False

    @property
    def name(self):
        return self.relative_url.replace("/", "_")

    def route_json(self):
        return {
            "name": self.name,
            "paths": [self.relative_url],
            "service": {"name": self.name},
            "methods": self.http_methods,
        }

    def service_json(self):
        return {"name": self.name, "url": self.target}

    def cors_json(self):
        return {
            "name": "cors",
            "config": {"origins": ["*"], "headers": ["*"], "credentials": True},
        }

    def __eq__(self, other):
        equal = True
        equal &= self.relative_url == other.relative_url
        equal &= self.target == other.target
        equal &= self.http_methods == other.http_methods
        equal &= self.cors == other.cors

        return equal
