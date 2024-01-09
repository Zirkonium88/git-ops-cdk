import json

class TestCDKConfig:
    def setup(self):
        self.environment = "networking-dev"
        self.key = "AccountId"
        self.value = "012345678910"

        with open(f"config/{self.environment}.json") as json_inline:
            self.data = json.load(json_inline)

    def test_init(self):
        from config import CDKConfig as uat

        response = uat(environment=self.environment)
        assert response.load_config() == self.data

    def test_get_value(self):
        from config import CDKConfig as uat

        config = uat(environment=self.environment)
        response = config.get_value(self.key)
        assert response == self.value
