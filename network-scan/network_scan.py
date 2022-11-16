import ipaddress
import re
import socket
import subprocess
import sys
from uuid import getnode

from mac_vendor_lookup import MacLookup, VendorNotFoundError


class NetworkDevice:
    print("Updating MAC address OUI database...\n")
    vendor_data = MacLookup()
    vendor_data.update_vendors()

    def __init__(self, ip_address: ipaddress, mac_address, hostname):
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.hostname = hostname

        try:
            self.vendor = NetworkDevice.vendor_data.lookup(mac_address)
        except VendorNotFoundError:
            self.vendor = "unknown"

    def __str__(self):
        return str(self.ip_address)


def get_host_device():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname + ".local")
    mac_address = str(hex(getnode())).strip("0x")
    mac_address = ':'.join(mac_address[i:i + 2] for i in range(0, 12, 2))  # format the MAC address
    return NetworkDevice(ip_address, mac_address, hostname)


def get_netmask():
    # To obtain the netmask, we will run the ifconfig command and extract it from the output.
    process = subprocess.Popen("ifconfig", stdout=subprocess.PIPE)
    output = str(process.communicate()).replace("\\n", "")

    # The netmask begins immediately following "netmask " (important to note the space) and immediately before the next
    # space (" "). First we split the whole output at "netmask ". This creates a list with two string elements. The
    # particular string we're interested in is the second element, as this contains the netmask. However, we need to
    # dis-join the host IP from the remainder of the string, so we also split this list into another list of two
    # elements at the first " ". We can then assign our netmask variable to the first element of the resulting list.
    netmask = output.split("netmask ")[1].split(" ")[0]
    return netmask


def determine_netmask_suffix(netmask: str):
    netmask_suffix = 0  # Count up number of bits starting at 0
    octets = netmask.split(".")
    for octet in octets:
        # We need to determine the number of bits that have a value of 1 in our IP address. We currently have a list of
        # strings representing each octet, eg ["255", "255", "192", "0"]. We can easily convert each string to an
        # integer, and each integer to binary using built in Python methods. Then, we can convert the binary
        # representation back to a string and find the length of the string. Since a netmask is guaranteed to be an
        # uninterrupted sequence of 1s, we can add the lengths of each string together to compute the netmask suffix.
        # When Python converts binary numbers to strings, it appends "0b" to the front for clarity, so this has to be
        # stripped off when the conversion from binary to string is made.
        netmask_suffix += len(str(bin(int(octet))).strip("0b"))
    return netmask_suffix


def ping_ip_addresses(list_of_ip_addresses: list):
    for ip_address in list_of_ip_addresses:
        subprocess.Popen(["ping", "-c", "1", str(ip_address)], stdout=subprocess.PIPE)


def get_hostname_from_ip(ip_address: str):
    try:
        return socket.gethostbyaddr(ip_address)[1]
    except socket.herror:
        return ip_address


def get_hosts_in_arp_table():
    # List of all hosts in ARP table.
    hosts = []

    # We'll use regular expressions to filter the IP and mac addresses out of the ARP table.
    re_ipv4 = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
    re_mac = re.compile(r"(?:[0-9a-fA-F][:|-]?){12}")

    # Run ARP command.
    process = subprocess.Popen("arp", stdout=subprocess.PIPE)
    table_entries = str(process.communicate()).split("\\n")  # Isolate ARP table entries by splitting at new line

    # Check all entries in table for IP and mac addresses.
    for entry in table_entries:
        try:
            ip_address = ipaddress.ip_address(re_ipv4.findall(entry)[0])
            mac_address = re_mac.findall(entry)[0].replace("-", ":")  # Replace - with : on Windows
            hostname = get_hostname_from_ip(str(ip_address))
            hosts.append(NetworkDevice(ip_address, mac_address, hostname))
        except IndexError:  # Index error occurs if regular expression did not find IP or mac address
            pass

    return hosts


def get_device_vendor(mac_data: MacLookup, mac_address: str):
    try:
        return mac_data.lookup(mac_address)
    except VendorNotFoundError:
        return "unknown"


def network_scan():
    # Get host information
    print("Getting host information...")
    host = get_host_device()
    print("Hostname is: " + host.hostname)
    print("Host IP address is: " + str(host.ip_address))
    print("Host MAC address is: " + host.mac_address + "\n")

    # Determine operating system and get the netmask from command line
    print("Initial discovery...")
    if sys.platform == "linux" or sys.platform == "linux2":
        print("Linux based host...")
        print("Checking ifconfig for netmask...")
        netmask = get_netmask()
    else:
        print("Unsupported platform... exiting")
        sys.exit()

    print("Netmask is: " + netmask + "\n")
    netmask_suffix = determine_netmask_suffix(netmask)
    number_of_host_addresses = 2 ** (32 - netmask_suffix) - 2
    print("Number of host addresses is: " + str(number_of_host_addresses))

    # Use host IP address and netmask to allow ip_network object to compute network address, broadcast address, and all
    # host addresses
    network = ipaddress.ip_network((host.ip_address, netmask_suffix), strict=False)
    print("Network address is: " + str(network.network_address))
    all_host_addresses = list(network.hosts())  # Convert iterator object to list for ease of use
    print("First usable address is: " + str(all_host_addresses[0]))
    print("Last usable address is: " + str(all_host_addresses[number_of_host_addresses - 1]))
    print("Broadcast address is: " + str(network.broadcast_address) + "\n")

    # Ping all IP addresses
    print("Pinging all addresses to populate ARP table...\n")
    ping_ip_addresses(all_host_addresses)

    # Check ARP table
    print("Constructing device list from ARP table...\n")
    network_devices = get_hosts_in_arp_table()  # Receive list of all devices in ARP table
    network_devices.append(host)  # Append host machine to the list for completion

    # Lookup device manufacturer and print results
    print("Printing contents...")
    for device in network_devices:
        print(str(device))

    return network.network_address, network_devices
