import ipaddress
import re
import socket
import subprocess
import sys
from uuid import getnode


class NetworkDevice:
    def __init__(self, hostname: str, ip_address: ipaddress, mac_address: str):
        self.hostname = hostname
        self.ip_address = ip_address
        self.mac_address = mac_address


def get_netmask_linux():
    print("Checking ifconfig for netmask...")

    # To obtain the netmask, we will run the ifconfig command and extract it from the output.
    process = subprocess.Popen("ifconfig", stdout=subprocess.PIPE)
    output = str(process.communicate()).replace("\\n", "")

    # The netmask begins immediately following "netmask " (important to note the space)
    # and immediately before the next space (" "). First we split the whole output at
    # "netmask ". This creates a list with two string elements. The particular string we're
    # interested in is the second element, as this contains the netmask. However, we need
    # to dis-join the host IP from the remainder of the string, so we also split this list
    # into another list of two elements at the first " ". We can then assign our netmask
    # variable to the first element of the resulting list.
    netmask = output.split("netmask ")[1].split(" ")[0]
    return netmask


def get_netmask_windows():
    print("Checking ipconfig for netmask...")

    # To obtain the netmask, we will run the ipconfig command and extract it from the output.
    process = subprocess.Popen("ipconfig", stdout=subprocess.PIPE)
    output = str(process.communicate()).replace("\\n", "")

    # The netmask begins immediately following "netmask " (important to note the space)
    # and immediately before the next space (" "). First we split the whole output at
    # "netmask ". This creates a list with two string elements. The particular string we're
    # interested in is the second element, as this contains the netmask. However, we need
    # to dis-join the host IP from the remainder of the string, so we also split this list
    # into another list of two elements at the first " ". We can then assign our netmask
    # variable to the first element of the resulting list.
    netmask = output.split("netmask ")[1].split(" ")[0]
    return netmask


def net_scan():
    network_devices = []

    print("Getting host information...")
    this_hostname = socket.gethostname()
    host_ip_address = socket.gethostbyname(this_hostname + ".local")
    host_mac_address = str(hex(getnode())).strip("0x")

    print("Hostname is: " + this_hostname)
    print("Host IP address is: " + host_ip_address)
    print("Host MAC address is: " + host_mac_address)

    print("Storing host information...\n")
    host = NetworkDevice(this_hostname, host_ip_address, host_mac_address)
    network_devices.append(host)

    print("Initial discovery...")
    if sys.platform == "win32":
        print("Windows based host...")
        netmask = get_netmask_windows()
    if sys.platform == "linux" or sys.platform == "linux2":
        print("Linux based host...")
        netmask = get_netmask_linux()
    else:
        print("Unsupported platform... exiting")
        sys.exit()

    print("Netmask is: " + netmask + "\n")

    print("Extrapolating additional information...")
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

    number_of_host_addresses = 2 ** (32 - cidr_suffix) - 2
    print("Number of host addresses is: " + str(number_of_host_addresses))

    network = ipaddress.ip_network((host_ip_address, cidr_suffix), strict=False)
    print("Network address is: " + str(network.network_address))

    all_host_addresses = list(network.hosts())
    print("First usable address is: " + str(all_host_addresses[0]))
    print("Last usable address is: " + str(all_host_addresses[number_of_host_addresses - 1]))

    print("Broadcast address is: " + str(network.broadcast_address) + "\n")

    print("Pinging all addresses to populate ARP table...")
    for address in all_host_addresses:
        subprocess.Popen(["ping", "-c", "4", str(address)], stdout=subprocess.PIPE)

    print("Loading regular expressions...")
    re_ipv4 = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
    re_mac = re.compile(r"(?:[0-9a-fA-F]:?){12}")

    print("Checking the ARP table...")
    process = subprocess.Popen(["arp"], stdout=subprocess.PIPE)
    output = str(process.communicate())
    table_entries = output.split("\\n")
    for entry in table_entries:
        if "ether" in entry:

            ip_address = ""
            mac_address = ""

            try:
                ip_address = ipaddress.ip_address(re_ipv4.findall(entry)[0])
            except IndexError:
                pass

            try:
                mac_address = re_mac.findall(entry)[0].replace(":", "")
            except IndexError:
                pass

            if ip_address and mac_address:
                try:
                    _, hostname, _ = socket.gethostbyaddr(str(ip_address))
                except socket.herror:
                    hostname = "unknown"

                print("Found host " + hostname + " at IP address " + str(ip_address) + " with MAC address " + mac_address)
                device = NetworkDevice(hostname, ip_address, mac_address)
                network_devices.append(device)








net_scan()
