"""
   This script deploy configurateions declared in config.yml file on
   Cisco devices dclared in same config.yml file.

   Author: Masoud Maghsoudi
   Github: https://github.com/shaspen
   Gitlab: https://gitlab.com/shaspen
   Email:  masoud_maghsoudi@yahoo.com
"""

import os
from datetime import datetime
from getpass import getpass
from netmiko import ConnectHandler
from yaml import safe_load
from dns import resolver, reversename


def load_configuration() -> dict:
    """ Loads interface configuration from config.yml file

    Returns:
        dict: loaded parameters from config file
    """
    params = {}
    file_path = os.path.dirname(__file__)
    with open(os.path.join(file_path, "config.yml"), 'r', encoding="utf-8") as file:
        config = safe_load(file)
        params['router'] = config['router']
        params['switch'] = config['switch_list']
        params['user_vlan'] = config['user_vlan']
        params['dns_servers'] = config['dns_server_list']
        return params

def arp_table(device) -> dict:
    """arp_table function connects to a router and returns arp table of the router in dictionary

    Args:
        device (str): router IP address

    Returns:
        dict: router arp table
    """
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': device,
        'username': USERNAME,
        'password': PASSWORD
    }
    result = {}
    net_connect = ConnectHandler(**conn_handler)
    command = net_connect.send_command('show ip arp', use_textfsm=True)
    for entry in command:
        result[entry['mac']] = entry['address']
    return result

def mac_table(device, vlans) -> list:
    """mac_table function connects to switches and returns switch mac table
    for access ports with vlans defined in configuration file

    Args:
        device (str): switch IP address
        vlans (list): list of user vlans

    Returns:
        list: switch mac table for specified vlans
    """
    access_ports = []
    result = []
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': device,
        'username': USERNAME,
        'password': PASSWORD
    }
    net_connect = ConnectHandler(**conn_handler)
    command = net_connect.send_command(
        'show interfaces status', use_textfsm=True)
    for item in command:
        if item['vlan'] in vlans:
            access_ports.append(item['port'])
    for vlan in vlans:
        command = net_connect.send_command(f'show mac address-table vlan {vlan}', use_textfsm=True)
        for entry in command:
            # with this condition check we try to exclude textfsm parsing errors
            if not isinstance(entry, dict):
                continue
            if entry['vlan'] in vlans and entry['destination_port'][0] in access_ports:
                result.append(
                    (entry['destination_port'][0], entry['destination_address']))
    return result

def ip_table(mac_tuple_list, arp_dict) -> list:
    """ ip table function uses result of mac table of switches and arp table of
        routers to cunstruct a list consist of port, mac and ip address of
        active devices on the switch port

    Args:
        mac_tuple_list (list): MAC address table
        arp_dict (dict): router ARP table

    Returns:
        list: add IP address to corresponding MAC data
    """
    result = []
    for mac_tuple in mac_tuple_list:
        for key, value in arp_dict.items():
            if mac_tuple[1] == key:
                result.append((*mac_tuple, value))
            else:
                continue
    return result

def dns_query(mac_ip_tuple_list, dns_servers) -> list:
    """ This function queries the ip addresses and add the stripped form of
        associated "A" record to data structure

    Args:
        mac_ip_tuple_list (list): list of data including IP addresses
        dns_servers (list): nameservers used for DNS query

    Returns:
        list: adds corresponfing name resolved from DNS to data structure
    """
    result = []
    res = resolver.Resolver(configure=True)
    res.nameservers = dns_servers
    q_type = 'PTR'
    for mac_ip_tuple in mac_ip_tuple_list:
        q_addr = reversename.from_address(mac_ip_tuple[2])
        try:
            query = res.resolve(q_addr, q_type)[0]
        # DNS resovler raises an NXDOMAIN exception if could not find any answer for query
        except:
            result.append((*mac_ip_tuple, "DNS Not Found"))
        else:
            query_stripped = str(query).partition('.')[0]
            result.append((*mac_ip_tuple, query_stripped))
    return result

def backup_config(device) -> None:
    """ Backup running configuration to file# backup running configuration to file

    Args:
        device (str): Device IP address
    """
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': device,
        'username': USERNAME,
        'password': PASSWORD
    }
    net_connect = ConnectHandler(**conn_handler)
    folder = "config_backup_files"
    if not os.path.isdir(folder):
        os.makedirs(folder)
    filename = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{conn_handler['ip']}-backup.config"
    with open(os.path.join(folder, filename), 'w', encoding="utf-8") as file:
        backup = net_connect.send_command("show running-config")
        file.write(backup)

def write_startup_config(device) -> None:
    """ Writes running-config to startup-config

    Args:
        device (str): Device IP address
    """
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': device,
        'username': USERNAME,
        'password': PASSWORD
    }
    net_connect = ConnectHandler(**conn_handler)
    command = net_connect.send_command('write memory')
    print(command)

#def config_interfaces(device, interface_list) -> None:
#    """ Configure the interface configuration loaded form config.yml file
#        on each device before deploying any config it make a backup file via
#        backup_config function
#
#    Args:
#        device (str): Device IP address
#        interface_list (list): Interfaces to be configured
#    """
#    conn_handler = {
#        'device_type': 'cisco_ios',
#        'ip': device,
#        'username': USERNAME,
#        'password': PASSWORD
#    }
#    net_connect = ConnectHandler(**conn_handler)
#    backup_config(device)
#    configs = load_config()
#    for interface in interface_list:
#        interface_fullname = ''
#        interface_fullname = "interface {}".format(interface)
#        command = net_connect.send_config_set([interface_fullname] + configs)
#        print(command)

# MAIN function
if __name__ == "__main__":

    NOTICE = """    #############################################################################################
    #                                                                                           #
    # NOTICE: You are changing the configration on Cisco devices based on configuration         #
    #         and devices declarted in config.yml file                                          #
    #                                                                                           #
    #         Please do not proceed if you do not know the effects of deplying                  #
    #                         configurations you are applying.                                  #
    #                                                                                           #
    #############################################################################################"""
    print(NOTICE)
    #USERNAME = input("Please enter the username for devices: ").strip()
    USERNAME = 'm.maghsoudi'
    #PASSWORD = getpass(prompt = "Please enter password for devices: ")
    PASSWORD = '123qwe'

    configs = load_configuration()
    ARP = arp_table(configs['router'][0])
    switch_data = {}

    for switch in configs['switch']:
        switch_data[switch] = mac_table(switch, configs['user_vlan'])

    for switch in configs['switch']:
        switch_data[switch] = ip_table(switch_data[switch], ARP)

    for switch in configs['switch']:
        switch_data[switch] = dns_query(
            switch_data[switch], configs['dns_servers'])

    print('################################################################', sep='\n')
    print(configs)
    print('################################################################', sep='\n')
    print(switch_data)
    print('################################################################', sep='\n')

    #    config_interfaces(device_ip, l3_interfaces)

    # save_prompt = input(
    #    "Are you sure to write configuration on Start-up conifuration? [y/n] (default=no)").strip()
    # if save_prompt[0] == 'y' or save_prompt[0] == 'Y':
    #    for device in devices:
    #        write_startup_config(device)
    # else:
    #    print("Deplyed configurations has not been written on Startup configuration")
