from act_overseer.act_to_neo4j import filename
from unittest.mock import Mock

import act_overseer.decide_to_act
import json
import logging
import requests
import unittest


dashboard_log = Mock()  # Mock object para dashboard_log
firewall_ip_and_port = "155.54.180.23:8086"  # IP y puerto de tu firewall basado en Docker config

# After decide_to_act receives json from dashboard, it's job is to remove from all hosts important host for
# given missions and their configurations. Then remove hosts with treshold less then security_treshold value
# in act_overseer_config. What's left is list of hosts ready to be blocked on firewall. decide_to_act module
# then performs blockings and unblockings on the firewall and calls act_to_neo4j module to update the
# changes in database.

# missions and configurations pairs obtained form the dashboard
missions_and_configurations_1 = [
    {
        "name": "Network Monitoring",
        "config_id": 1
    },
    {
        "name": "Incident Handling",
        "config_id": 2
    }
]

test_hosts = [{'host': {'avail': 0.7, 'hostname': 'collector2.csirt.muni.cz', 'conf': 0.6, 'integ': 0.5, 'ip_address': '147.251.14.53'}},
              {'host': {'avail': 0.7, 'hostname': 'flowmon-cps-cesnet', 'conf': 0.7, 'integ': 0.7, 'ip_address': '10.0.114.138'}},
              {'host': {'avail': 0.9, 'hostname': 'flowmon-ics-cesnet-1', 'conf': 0.9, 'integ': 0.9, 'ip_address': '10.0.111.130'}},
              {'host': {'avail': 0.96, 'hostname': 'collector.csirt.muni.cz', 'conf': 0.4, 'integ': 0.3, 'ip_address': '147.251.14.52'}},
              {'host': {'avail': 0.8, 'hostname': 'flowmon-rect-law-sci', 'conf': 0.86, 'integ': 0.87, 'ip_address': '10.0.117.132'}},
              {'host': {'avail': 0.5, 'hostname': 'flowmon-rect-ukb', 'conf': 0.0, 'integ': 0.0, 'ip_address': '10.0.117.130'}}]


URL = 'http://155.54.180.23:8086' 

class DecideToActTest(unittest.TestCase):

    def test_remove_less_than_treshold(self):
        """ Test that all hosts have security value higher or equal than security threshold."""
        # get treshold - CORREGIDO: añadido dashboard_log
        treshold = act_overseer.decide_to_act.get_treshold(logging, dashboard_log)
        # remove hosts with security treshold less than 'treshold'
        hosts_less_than_treshold = act_overseer.decide_to_act.remove_less_than_treshold(test_hosts, logging)
        # check if all hosts in 'hosts_less_than_treshold' have security treshold less than 'treshold'
        for host in hosts_less_than_treshold:
            self.assertTrue(act_overseer.decide_to_act.get_average_security_value(host, logging) >= treshold)

    def test_block_ip(self):
        """ Test blocking IP on firewall."""
        ip = "192.168.1.100"  # IP cambiada a rango privado para testing
        # CORREGIDO: añadidos dashboard_log y firewall_ip_and_port
        act_overseer.decide_to_act.block_ip(ip, logging, dashboard_log, firewall_ip_and_port)
        host = requests.get(f"{URL}/firewall/{ip}").json()
        self.assertEqual(ip, host['ip'])
        # CORREGIDO: añadidos dashboard_log y firewall_ip_and_port
        act_overseer.decide_to_act.unblock_ip(ip, logging, dashboard_log, firewall_ip_and_port)

    def test_block_already_blocked_ip(self):
        """ Test blocking already blocked IP. """
        ip = "192.168.1.101"  # IP cambiada a rango privado para testing
        # block IP - CORREGIDO: añadidos parámetros
        act_overseer.decide_to_act.block_ip(ip, logging, dashboard_log, firewall_ip_and_port)
        list_of_blocked_ips = requests.get(f"{URL}/firewall/blocked").json()
        # try to block it again - CORREGIDO: añadidos parámetros
        act_overseer.decide_to_act.block_ip(ip, logging, dashboard_log, firewall_ip_and_port)
        new_list_of_blocked_ips = requests.get(f"{URL}/firewall/blocked").json()
        # check that there were no changes after trying to block already blocked IP
        self.assertEqual(list_of_blocked_ips, new_list_of_blocked_ips)
        # CORREGIDO: añadidos parámetros
        act_overseer.decide_to_act.unblock_ip(ip, logging, dashboard_log, firewall_ip_and_port)

    def test_unblock_ip(self):
        """ Test unblocking IP on firewall. """
        ip = "192.168.1.102"  # IP cambiada a rango privado para testing
        # block IP - CORREGIDO: añadidos parámetros
        act_overseer.decide_to_act.block_ip(ip, logging, dashboard_log, firewall_ip_and_port)
        # unblock IP - CORREGIDO: añadidos parámetros
        act_overseer.decide_to_act.unblock_ip(ip, logging, dashboard_log, firewall_ip_and_port)
        request = requests.get(f"{URL}/firewall/{ip}")
        # 404 trying to get the unblocked IP, not found
        self.assertTrue(request.status_code == 404)

    def test_configuration_n1(self):
        # block random IP to check if it gets unblocked in the process
        unblocked_ip = '192.168.1.103'  # IP cambiada a rango privado para testing
        # CORREGIDO: añadidos parámetros
        act_overseer.decide_to_act.block_ip(unblocked_ip, logging, dashboard_log, firewall_ip_and_port)
        user, passw = get_user_and_pass()
        # call main function of decide_to_act module
        act_overseer.decide_to_act.run_decide_to_act(user, passw, missions_and_configurations_1, logging)
        ip = '192.168.1.104'  # IP cambiada a rango privado para testing
        host = requests.get(f"{URL}/firewall/{ip}").json()
        # check that {ip} is blocked on the firewall
        self.assertEqual(ip, host['ip'])
        host_2 = requests.get(f"{URL}/firewall/{unblocked_ip}")
        # and check that all other IPs were unblocked
        self.assertTrue(host_2.status_code == 404)

def get_user_and_pass():
    with open(filename('data/act_overseer_config'), 'r') as cfg:
        data = json.load(cfg)
        user = data['user']
        passw = data['password']
    return user, passw

if __name__ == '__main__':
    unittest.main()
