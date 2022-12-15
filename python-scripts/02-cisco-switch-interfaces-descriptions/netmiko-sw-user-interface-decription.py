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
from dns import resolver, reversename
import os


# load interface configuration from config.yml file

def load_configuration():
    params = {}
    file_path = os.path.dirname(__file__)
    with open(os.path.join(file_path, "config.yml"), 'r') as file:
        config = safe_load(file)
        params['router'] = config['router']
        params['switch'] = config['switch_list']
        params['user_vlan'] = config['user_vlan']
        params['dns_servers'] = config['dns_server_list']
        return params


# arp_table function connects to a router and returns arp table of the router in dictionary

def arp_table(router):
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': router,
        'username': username,
        'password': password
    }
    result = {}
    net_connect = ConnectHandler(**conn_handler)
    command = net_connect.send_command('show ip arp', use_textfsm=True)
    for entry in command:
        result[entry['mac']] = entry['address']
    return result


# mac_table function connects to switches and returns mac table of switch for
#  access ports with vlans defined in configuration file

def mac_table(sw, vlans):
    access_ports = []
    result = []
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': sw,
        'username': username,
        'password': password
    }
    net_connect = ConnectHandler(**conn_handler)
    command = net_connect.send_command(
        'show interfaces status', use_textfsm=True)
    for item in command:
        if item['vlan'] in vlans:
            access_ports.append(item['port'])
    for vlan in vlans:
        command = net_connect.send_command(
            'show mac address-table vlan {}'.format(vlan), use_textfsm=True)
        for entry in command:
            # with this condition check we try to exclude textfsm parsing errors
            if type(entry) != dict:
                continue
            if entry['vlan'] in vlans and entry['destination_port'][0] in access_ports:
                result.append(
                    (entry['destination_port'][0], entry['destination_address']))
    return result

# ip table function uses result of mac table of switches and arp table of routers to cunstruct
#  a list consist of port, mac and ip address of active devices on the switch port

def ip_table(mac_tuple_list, arp_dict):
    result = []
    for mac_tuple in mac_tuple_list:
        for key, value in arp_dict.items():
            if mac_tuple[1] == key:
                result.append((*mac_tuple, value))
            else:
                continue
    return result

# dns query function queries the ip addresses and add the stripped form of associated
# "A" record to data structure

def dns_query(mac_ip_tuple_list, dns_servers):
    result = []
    res = resolver.Resolver(configure=True)
    res.nameservers = dns_servers
    q_type = 'PTR'
    for mac_ip_tuple in mac_ip_tuple_list:
        q_addr = reversename.from_address(mac_ip_tuple[2])
        try:
            query = res.resolve(q_addr, q_type)[0]
        except:
            result.append((*mac_ip_tuple, "DNS Not Found"))
        else:
            query_stripped = str(query).partition('.')[0]
            result.append((*mac_ip_tuple, query_stripped))
    return result

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
    arp_dict = arp_table(parameters['router'][0])

    for sw in parameters['switch']:
        mac_tuple = mac_table(sw, parameters['user_vlan'])
        parameters[sw] = mac_tuple

    for sw in parameters['switch']:
        mac_ip_tuple = ip_table(parameters[sw], arp_dict)
        parameters[sw] = mac_ip_tuple

    for sw in parameters['switch']:
        mac_ip_dns_tuple = dns_query(parameters[sw], parameters['dns_servers'])
        parameters[sw] = mac_ip_dns_tuple

    print('**************************************************', sep='\n')
    print(parameters)

    #    interfaces = show_interfaces(device_ip)
    #    l3_interfaces = l3_interfaces_list(interfaces)
    #    config_interfaces(device_ip, l3_interfaces)

    # save_prompt = input(
    #    "Are you sure to write configuration on Start-up conifuration? [y/n] (default=no) ").strip()
    # if save_prompt[0] == 'y' or save_prompt[0] == 'Y':
    #    for device in devices:
    #        write_startup_config(device)
    # else:
    #    print("Deplyed configurations has not been written on Startup configuration")
