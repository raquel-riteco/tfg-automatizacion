from ipaddress import IPv4Network

class Subnetting:
    def __init__(self, info: dict):
        self.info = info

    def generate_subnetting(self):
        """
        Automatically generates subnets from a base network, allocating address space
        based on the number of devices required per subnet.

        Returns:
            list of IPv4Network: The generated subnets in the original input order.

        Raises:
            ValueError: If there is not enough address space in the base network
                        to accommodate all requested subnets.
        """
        base_network = self.info["network"]
        devices_per_network = self.info["list_num_devices"]

        networks = [(i, devices) for i, devices in enumerate(devices_per_network)]

        for j in range(1, len(networks)):
            key = networks[j]
            i = j - 1
            while i >= 0 and networks[i][1] < key[1]:
                networks[i + 1] = networks[i]
                i -= 1
            networks[i + 1] = key

        subnets = []
        current_subnet_pool = [base_network]

        for idx, devices in networks:
            needed_hosts = devices + 2
            prefix = 32
            while (2 ** (32 - prefix)) < needed_hosts:
                prefix -= 1

            for i, pool in enumerate(current_subnet_pool):
                try:
                    new_subnets = list(pool.subnets(new_prefix=prefix))
                    subnet = new_subnets[0]
                    subnets.append((idx, subnet))

                    # Update the subnet pool: remove the used block and add remaining ones
                    del current_subnet_pool[i]
                    current_subnet_pool.extend(new_subnets[1:])
                    break
                except ValueError:
                    continue
            else:
                raise ValueError("Not enough address space in the base network to accommodate all subnets.")

        # Restore original input order based on index
        result = [subnet for _, subnet in sorted(subnets)]
        return result

