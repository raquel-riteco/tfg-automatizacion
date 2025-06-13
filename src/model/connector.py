from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from ciscoconfparse import CiscoConfParse

class Connector:
    def __init__(self):
        pass
      
    def get_device_info(self, connect_info: dict) -> dict:
        """
        Retrieves the running configuration of the device matching the given IP address.
        Params:
            connect_info (dict): Dictionary with connection data, must include 'ip'.
        Returns:
            dict: Dictionary with the running configuration, or empty if not found.
        """

        nr = InitNornir(config_file="config/config.yaml")

        target = nr.filter(name=connect_info["name"])

        result = target.run(task=napalm_get, getters=["config"])
        hostname = list(target.inventory.hosts.keys())[0]

        task_result = result[hostname]

        if task_result.failed:
            raise RuntimeError(f"NAPALM task failed: {task_result.exception}")

        running_config = result[hostname].result["config"]["running"]
        parse = CiscoConfParse(running_config.splitlines(), syntax='ios')


        device_info = dict()
        return device_info