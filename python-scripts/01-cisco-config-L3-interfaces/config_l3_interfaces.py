"""
   This script deploy configurateions declared in config.yml file on
   Cisco devices dclared in same config.yml file.

   Author: Masoud Maghsoudi
   Github: https://github.com/masoud-maghsoudi
   Email:  masoud_maghsoudi@yahoo.com
"""

import os
from datetime import datetime
from getpass import getpass
from netmiko import ConnectHandler
from yaml import safe_load


def load_config() -> list:
    """ Loads interface configurations from config.yml file

    Returns:
        list: Interface configurations
    """
    with open("config.yml", 'r', encoding="utf-8") as file:
        config = safe_load(file)
        return config['interface_configuration']


def load_devices() -> list:
    """ Load device IPs from config.yml file

    Returns:
        list: IP address of devices to be configured
    """
    with open("config.yml", 'r', encoding="utf-8") as file:
        config = safe_load(file)
        return config['device_list']


def backup_config(device: str) -> None:
    """ Backup running configuration to file

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


def write_startup_config(device: str) -> None:
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


def show_interfaces(device: str) -> list:
    """ Returns the output of command <show ip interface brief>

    Args:
        device (str): Device IP address

    Returns:
        list: <show ip interface brief> output
    """
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': device,
        'username': USERNAME,
        'password': PASSWORD
    }
    net_connect = ConnectHandler(**conn_handler)
    return net_connect.send_command('show ip interface brief', use_textfsm=True)


def l3_interfaces_list(interfaces: list) -> list:
    """ Returns the list of interfaces with an IP address set on them

    Args:
        interfaces (list): All interfaces

    Returns:
        list: Interfaces with IP address
    """
    interface_list = []
    for interface in interfaces:
        if interface['ipaddr'] != "unassigned":
            interface_list.append(interface['intf'])
    return interface_list


def config_interfaces(device: str, interface_list: list) -> None:
    """ Configures the interface configuration loaded form config.yml file
        on each device before deploying any config it make a backup file
        via backup_config function

    Args:
        device (str): Device IP address
        interface_list (list): Interfaces to be configured
    """
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': device,
        'username': USERNAME,
        'password': PASSWORD
    }
    net_connect = ConnectHandler(**conn_handler)
    backup_config(device)
    configs = load_config()
    for interface in interface_list:
        interface_fullname = f'interface {interface}'
        command = net_connect.send_config_set([interface_fullname] + configs)
        print(command)


# MAIN function
if __name__ == "__main__":

    NOTICE = """    ###############################################################################
    #                                                                             #
    #     NOTICE: You are changing the configration on Cisco devices based on     #
    #        configuration and devices declarted in config.yml file               #
    #                                                                             #
    #      Please do not proceed if you do not know the effects of deplying       #
    #                     configurations you are applying.                        #
    #                                                                             #
    ###############################################################################"""

    print(NOTICE)
    USERNAME = input("Please enter the username for devices: ").strip()
    PASSWORD = getpass(prompt="Please enter password for devices: ")
    DEVICES = load_devices()

    for device_ip in DEVICES:
        interfaces_list = show_interfaces(device_ip)
        l3_interfaces = l3_interfaces_list(interfaces_list)
        config_interfaces(device_ip, l3_interfaces)

    SAVE_PROMPT = input(
        "Are you sure to write configuration on Start-up conifuration? [y/n] (default=no) ").strip()
    if SAVE_PROMPT[0] in ('y', 'Y'):
        for device_ip in DEVICES:
            write_startup_config(device_ip)
    else:
        print("Deplyed configurations has not been written on Startup configuration")
