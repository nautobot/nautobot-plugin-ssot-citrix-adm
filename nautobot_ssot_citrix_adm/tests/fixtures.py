"""Fixtures for tests."""
import json


def load_json(path):
    """Load a json file."""
    with open(path, encoding="utf-8") as file:
        return json.loads(file.read())


SITE_FIXTURE_SENT = load_json("./nautobot_ssot_citrix_adm/tests/fixtures/get_sites_sent.json")
SITE_FIXTURE_RECV = load_json("./nautobot_ssot_citrix_adm/tests/fixtures/get_sites_recv.json")
DEVICE_FIXTURE_SENT = load_json("./nautobot_ssot_citrix_adm/tests/fixtures/get_devices_sent.json")
DEVICE_FIXTURE_RECV = load_json("./nautobot_ssot_citrix_adm/tests/fixtures/get_devices_recv.json")
PORT_FIXTURE = load_json("./nautobot_ssot_citrix_adm/tests/fixtures/get_ports.json")
