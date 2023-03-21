import uuid

# Config file constants
CONSUMER_CONFIG_SECTION = "consumers"
KEY_AUTH_CONFIG_SECTION = "keyauth_credentials"


class KeyAuthManager(object):
    """
    Adds and removes key-auth configuration to support adding and removing tokens
    """

    def __init__(self):
        self.consumer_username = f"user-{uuid.uuid4()}"
        self._consumer = {}
        self._credential = {}

    def from_request(self):
        self._consumer = {"username": self.consumer_username}
        self._credential = {"consumer": self.consumer_username}

    def create(self, kong_conf):
        """
        Create a consumer/keyauth_credentials mapping in the config, and updates Kong
        """
        kong_conf.create_element(CONSUMER_CONFIG_SECTION, self._consumer, False)
        kong_conf.create_element(KEY_AUTH_CONFIG_SECTION, self._credential, False)

        kong_conf.update_config()

    def remove(self, kong_conf):
        """
        Remove a consumer/keyauth_credentials mapping in the config, and updates Kong
        """
        # TODO
        pass
