"""Fixtures for tests."""
import json


def load_json(path):
    """Load a json file."""
    with open(path, encoding="utf-8") as file:
        return json.loads(file.read())


SITE_FIXTURE = load_json("./nautobot_ssot_citrix_adm/tests/fixtures/get_sites.json")
DEVICE_FIXTURE = load_json("./nautobot_ssot_citrix_adm/tests/fixtures/get_devices.json")
