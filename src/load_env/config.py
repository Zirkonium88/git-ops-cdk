import json
import logging

logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] - %(message)s", force=True
)


class CDKConfig:
    """Generate CDK config object for multi environment deployments."""

    def __init__(self, environment: str) -> None:
        """Initialize config object.

        Args:
            environment (str): name of the environment. Need to be in line with names of JSON config files.
        """
        self._environment = environment
        self.load_config()

    def load_config(self) -> dict:
        """Load the config object.

        Returns:
            dict:  json config object
        """
        with open(f"config/{self._environment}.json") as json_inline:
            self.data = json.load(json_inline)
        return self.data

    def get_value(self, key: str) -> str:
        """Get value from config object.

        Args:
            key (str): name of the key of the key-value pair

        Returns:
            str: value of the key-value-pair
        """
        try:
            return self.data[key]
        except KeyError as e:
            logging.error(e)
            logging.error(self.data)
