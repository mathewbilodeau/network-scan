import subprocess
import socket
import ipaddress

from sys import platform


class NetworkDevice:
    def __init__(self, hostname, ip_address, mac_address):
        self.hostname = hostname
        self.ip_address = ip_address
        self.mac_address = mac_address


def get_host_info_in_linux():
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
    host_ip_address = output.split("inet ")[1].split(" ")[0]
    print("Host IP address is: " + host_ip_address)

    # We can repeat this process three more times to obtain the host MAC address, netmask, and
    # broadcast address of the network.
    host_mac_address = output.split("ether ")[1].split(" ")[0]
    print("Host MAC address is: " + host_mac_address)

    netmask = output.split("netmask ")[1].split(" ")[0]
    print("Netmask is: " + netmask)

    broadcast_address = output.split("broadcast ")[1].split(" ")[0]
    print("Broadcast address is " + broadcast_address)

    host = NetworkDevice(host_ip_address, host_mac_address)
    return host


def get_netmask_in_windows():
    return


def net_scan():

    hostname = socket.gethostname()
    print("Hostname is: " + hostname)

    if platform == "linux" or platform == "linux2":
        netmask = get_host_info_in_linux()
    elif platform == "win32":
        netmask = get_netmask_in_windows()

    # calculate_address_range(netmask)


net_scan()
