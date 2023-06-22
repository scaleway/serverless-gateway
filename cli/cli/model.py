from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Route(object):
    relative_url: str
    target: str

    http_methods: Optional[List[str]] = None
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
class Consumer(object):
    pub_key: str
    iss: str
    username: Optional[str] = None
    custom_id: Optional[str] = None

    def get_consumer_name(self):
        return self.custom_id if self.custom_id else self.username

    def consumer_json(self):
        if self.custom_id:
            return {
                "custom_id": self.custom_id,
            }
        else:
            return {
                "username": self.username,
            }

    def jwt_json(self):
        return {
            "algorithm": "RS256",
            "rsa_public_key": self.pub_key,
            "key": self.iss,
        }
