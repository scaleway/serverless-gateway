from dataclasses import dataclass
from typing import Optional


@dataclass
class Route:
    relative_url: str
    target: str

    http_methods: Optional[list[str]] = None
    cors: Optional[bool] = False
    jwt: Optional[bool] = False

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

    def jwt_json(self):
        return {
            "name": "jwt",
        }

    def __eq__(self, other):
        equal = True
        equal &= self.relative_url == other.relative_url
        equal &= self.target == other.target
        equal &= self.http_methods == other.http_methods
        equal &= self.cors == other.cors
        equal &= self.jwt == other.jwt

        return equal


@dataclass
class Consumer:
    username: Optional[str] = None

    @classmethod
    def from_json(cls, json_data: dict):
        c = Consumer(
            username=json_data.get("username"),
        )

        return c

    def json(self):
        return {
            "username": self.username,
        }

    def __eq__(self, other):
        return other.username == self.username


@dataclass
class JwtCredential:
    algorithm: str
    iss: str
    secret: str

    @classmethod
    def from_json(cls, json_data: dict):
        c = JwtCredential(
            algorithm=str(json_data.get("algorithm")),
            iss=str(json_data.get("key")),
            secret=str(json_data.get("secret")),
        )

        return c
