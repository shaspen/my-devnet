###########################################################################
#
#   This script deploy configurateions declared in config.yml file on
#   Cisco devices dclared in same config.yml file.
#
#   Author: Maosud Maghsoudi
#   Github: https://github.com/shaspen
#   Gitlab: https://gitlab.com/shaspen
#   Email:  masoud_maghsoudi@yahoo.com
#
###########################################################################

from netmiko import ConnectHandler
from datetime import datetime
from yaml import safe_load
import os

# load interface configuration from config.yml file
def load_config():
    with open("config.yml", 'r') as file:
        config = safe_load(file)
        return config['interface_configuration']

# load device IPs from config.yml file
def load_devices():
    with open("config.yml", 'r') as file:
        config = safe_load(file)
        return config['device_list']

# backup running configuration to file
def backup_config(device):
    conn_handler = {
        'device_type': 'cisco_ios',
        'ip': device ,
        'username': username ,
        'password': password
    }
    net_connect = ConnectHandler(**conn_handler)
    folder = "config_backup_files"
    if not os.path.isdir(folder):
        os.makedirs(folder)
    filename = "{}-{}-backup.config".format(datetime.now().strftime('%Y-%m-%d-%H-%M-%S'), conn_handler['ip'])
    with open(os.path.join(folder,filename),'w') as file:
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
    return net_connect.send_command('show ip interface brief')

# return the list of interfaces with an IP address set on them
def l3_interfaces_list(interfaces):
    interface_list = []
    for line in (interfaces.splitlines()):
        if line.split()[1] != "unassigned":
            interface_list.append(line.split()[0])
    interface_list.pop(0)
    return interface_list

# configure the interface configuration loaded form config.yml file on each device
# before deploying any config it make a backup file via backup_config function
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
        configs.insert(0,"interface {}".format(interface))
        command = net_connect.send_config_set(configs)
        print(command)

#MAIN function            
if __name__=="__main__":
    
    notice = """    ##############################################################################################################################
    #                                                                                                                            #
    # NOTICE: You are changing the configration on Cisco devices based on configuratoni and devices declarted in config.yml file #
    #         Please do not proceed if you do not know the effects of deplying configurations you are applying.                  #
    #                                                                                                                            #
    ##############################################################################################################################"""

    print(notice)
    username = input("please enter the username for devices: ").strip()
    password = input("Please enter password for devices: ").strip()
    devices = load_devices()
    
    for device_ip in devices:
        interfaces = show_interfaces(device_ip)
        l3_interfaces = l3_interfaces_list(interfaces)
        config_interfaces(device_ip, l3_interfaces)

    save_prompt = input("Are you sure to write configuration on Start-up conifuration? [y/n] (default=no) ").strip()
    if save_prompt[0] == 'y' or save_prompt[0] == 'Y':
        for device in devices:
            write_startup_config(device)
    else:
        print("Deplyed configurations has not been written on Startup configuration")