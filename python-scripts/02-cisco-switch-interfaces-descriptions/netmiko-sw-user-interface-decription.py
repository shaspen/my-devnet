###########################################################################
#
#   This script deploy configurateions declared in config.yml file on
#   Cisco devices dclared in same config.yml file.
#
#   Author: Masoud Maghsoudi
#   Github: https://github.com/shaspen
#   Gitlab: https://gitlab.com/shaspen
#   Email:  masoud_maghsoudi@yahoo.com
#
###########################################################################

from netmiko import ConnectHandler
from getpass import getpass
from datetime import datetime
from yaml import safe_load
import os

# load interface configuration from config.yml file

def load_configuration():
    params = {}
    file_path = os.path.dirname(__file__)
    with open(os.path.join(file_path,"config.yml"), 'r') as file:
        config = safe_load(file)
        params['router'] = config['router']
        params['switch'] = config['switch_list']
        params['user_vlan'] = config['user_vlan']
        params['dns_server'] = config['dns_server']
        return params

        

# MAC TABLE FUNC

def mac_table(sw, vlans):
    access_ports = []
    access_port_mac = []
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': sw,
        'username': username,
        'password': password
    }
    net_connect = ConnectHandler(**conn_handler)
    command = net_connect.send_command('show interfaces status', use_textfsm=True)
    for item in command:
        if item['vlan'] in vlans: 
            access_ports.append(item['port'])
#    print(vlans)
    for vlan in vlans:
#        print(vlan)
        command = net_connect.send_command(
            'show mac address-table vlan {}'.format(vlan), use_textfsm=True)
        print(command)
#        for entry in command:
#            if entry['vlan'] in vlans and entry['destination_port'][0] in access_ports:
#                access_port_mac.append(
#                    (entry['destination_port'][0], entry['destination_address']))
#    return access_port_mac

# backup running configuration to file


def backup_config(device):
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': device,
        'username': username,
        'password': password
    }
    net_connect = ConnectHandler(**conn_handler)
    folder = "config_backup_files"
    if not os.path.isdir(folder):
        os.makedirs(folder)
    filename = "{}-{}-backup.config".format(
        datetime.now().strftime('%Y-%m-%d-%H-%M-%S'), conn_handler['ip'])
    with open(os.path.join(folder, filename), 'w') as file:
        backup = net_connect.send_command("show running-config")
        file.write(backup)

# return the output of command <show ip interface brief> as string


def write_startup_config(device):
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': device,
        'username': username,
        'password': password
    }
    net_connect = ConnectHandler(**conn_handler)
    command = net_connect.send_command('write memory')
    print(command)

# return the output of command <show ip interface brief> as string


def show_interfaces(device):
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': device,
        'username': username,
        'password': password
    }
    net_connect = ConnectHandler(**conn_handler)
    return net_connect.send_command('show ip interface brief', use_textfsm=True)

# return the list of interfaces with an IP address set on them

"""
def l3_interfaces_list(interfaces):
    interface_list = []
    for interface in interfaces:
        if interface['ipaddr']!="unassigned":
            interface_list.append(interface['intf'])
    return interface_list
"""
# configure the interface configuration loaded form config.yml file on each device
# before deploying any config it make a backup file via backup_config function

"""
def config_interfaces(device, interface_list):
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': device,
        'username': username,
        'password': password
    }
    net_connect = ConnectHandler(**conn_handler)
    backup_config(device)
    configs = load_config()
    for interface in interface_list:
        interface_fullname = ''
        interface_fullname = "interface {}".format(interface)
        command = net_connect.send_config_set([interface_fullname] + configs)
        print(command)
"""

# MAIN function
if __name__ == "__main__":

    notice = """    ##############################################################################################################################
    #                                                                                                                            #
    # NOTICE: You are changing the configration on Cisco devices based on configuratoni and devices declarted in config.yml file #
    #         Please do not proceed if you do not know the effects of deplying configurations you are applying.                  #
    #                                                                                                                            #
    ##############################################################################################################################"""

#    print(notice)
    #username = input("Please enter the username for devices: ").strip()
    username = 'm.maghsoudi'
    #password = getpass(prompt = "Please enter password for devices: ")
    password = '123qwe'
    parameters = load_configuration()


    for sw in parameters['switch']:
        mac_tuple = mac_table(sw, parameters['user_vlan'])
        parameters[sw] = mac_tuple

    print(parameters)

        
    #    interfaces = show_interfaces(device_ip)
    #    l3_interfaces = l3_interfaces_list(interfaces)
    #    config_interfaces(device_ip, l3_interfaces)

    #save_prompt = input(
    #    "Are you sure to write configuration on Start-up conifuration? [y/n] (default=no) ").strip()
    #if save_prompt[0] == 'y' or save_prompt[0] == 'Y':
    #    for device in devices:
    #        write_startup_config(device)
    #else:
    #    print("Deplyed configurations has not been written on Startup configuration")