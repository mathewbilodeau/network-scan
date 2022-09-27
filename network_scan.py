import subprocess
import socket
import ipaddress
import sys


class Network:
    network_devices = []

    def __init__(self, network_address: ipaddress, netmask: ipaddress, broadcast_address: ipaddress,
                 gateway: ipaddress):
        self.network_address = network_address
        self.netmask = netmask
        self.broadcast_address = broadcast_address
        self.gateway = gateway


class NetworkDevice:
    def __init__(self, hostname: str, ip_address: ipaddress, mac_address: str):
        self.hostname = hostname
        self.ip_address = ip_address
        self.mac_address = mac_address


def linux_discovery():
    print("Checking ifconfig...")

    # To obtain the netmask, we will run the ifconfig command and extract it from the output.
    process = subprocess.Popen("ifconfig", stdout=subprocess.PIPE)
    output = str(process.communicate()).replace("\\n", "")

    # The host IP begins immediately following "inet " (important to note the space)
    # and immediately before the next space (" "). First we split the whole output at
    # "inet ". This creates a list with two string elements. The particular string we're
    # interested in is the second element, as this contains the host IP. However, we need
    # to dis-join the host IP from the remainder of the string, so we also split this list
    # into another list of two elements at the first " ". We can then assign our host_ip_address
    # variable to the first element of the resulting list.
    host_ip_address = ipaddress.ip_address(output.split("inet ")[1].split(" ")[0])

    # We can repeat this process three more times to obtain the host MAC address, netmask, and
    # broadcast address of the network.
    host_mac_address = output.split("ether ")[1].split(" ")[0]
    netmask = output.split("netmask ")[1].split(" ")[0]
    broadcast_address = ipaddress.ip_address(output.split("broadcast ")[1].split(" ")[0])

    return host_ip_address, host_mac_address, netmask, broadcast_address


def net_scan():
    print("Initial discovery...")

    hostname = socket.gethostname()
    print("Hostname is: " + hostname)

    if sys.platform == "win32":
        print("Windows based host...")
        pass
    elif sys.platform == "linux" or sys.platform == "linux2":
        print("Linux based host...")
        host_ip_address, host_mac_address, netmask, broadcast_address = linux_discovery()
    else:
        print("Unsupported platform... exiting")
        sys.exit()

    print("Performing additional processing...")

    cidr_suffix = 0
    octets = netmask.split(".")
    for octet in octets:
        # We need to determine the number of bits that have a value of 1 in our IP address. We currently have
        # a list of strings representing each octet, eg ["255", "255", "192", "0"]. We can easily convert each
        # string to an integer, and each integer to binary using built in Python methods. Then, we can convert
        # the binary representation back to a string and find the length of the string. Since a netmask is
        # guaranteed to be an uninterrupted sequence of 1s, we can add the length string together to compute
        # the CIDR suffix. When Python converts binary numbers to strings, it appends "0b" to the front for
        # clarity, so this has to be stripped off when the conversion from binary to string is made.
        cidr_suffix += len(str(bin(int(octet))).strip("0b"))

    total_number_of_addresses = 2 ** (32 - cidr_suffix) - 2

    network = ipaddress.ip_network((host_ip_address, cidr_suffix), strict=False)

    print("Host IP address is: " + str(host_ip_address))
    print("Host MAC address is: " + host_mac_address)
    print("Netmask is: " + netmask)
    print("The number of usable addresses on the network is: " + str(total_number_of_addresses))
    print("The network address is: " + str(network.network_address))
    print("Broadcast address is " + str(broadcast_address))


net_scan()
