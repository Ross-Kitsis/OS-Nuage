'''
Created on Sep 12, 2016

@author: t916355
'''

import sys
import operator
from tabulate import tabulate
sys.path.append("./")

from vspk.v4_0 import *

class ObjectPrinter(object):
    '''
    Print various NURest Objects
    Single class responsible for all printer functions
    '''
    def print_enterprises(self,enterprises):
        #Create table and table headers
        table = []
        headers = ["Name","Description","ExternalId","EnterpriseProfileId"]
        
        #Print enterprise parameters
        for ent in enterprises:
            entry = []
            entry.append(ent.name)
            entry.append(ent.description)
            entry.append(ent.external_id)
            entry.append(ent.enterprise_profile_id)
            table.append(entry)
        
        print tabulate(table,headers)
    
    def print_enterprise_profiles(self,enterprise_profiles):
                #Create table and table headers
        table = []
        headers = ["Name","Description","EnterpriseProfileId"]
    
        for profile in enterprise_profiles:
            entry = []
            entry.append(profile.name)
            entry.append(profile.description)
            entry.append(profile.id)
            table.append(entry)
    
        print tabulate(table,headers)
    
    def print_domains(self, domains): 
        #Create table and table headers
        table = []
        headers = ["Name","Description","DomainId","Maintenance Status", "Policy Change Status"]        
        for domain in domains:
            entry = []
            entry.append(domain.name)
            entry.append(domain.description)
            entry.append(domain.id)
            entry.append(domain.maintenance_mode)
            entry.append(domain.policy_change_status)
            table.append(entry)
        
        table = self.sort_table(table, col=0)
        
        print tabulate(table,headers)
        print 'Number of domains found:\t' + str(len(table))
        
    def print_domain_templates(self,templates):
    #Create table and table headers
        table = []
        headers = ["Name","Description","TemplateId"]
        
        for template in templates:
            entry = []
            entry.append(template.name)
            entry.append(template.description)
            entry.append(template.id)
            table.append(entry)
        
        print tabulate(table,headers)
    
    def print_zones(self,zones):
        
        '''
        table = []
        headers = ["Enterprise","Domain","Zone","Description"]
        
        for enterprise in enterprises:
            domains = enterprise.domains
            for domain in domains:
                zones = domain.zones
                for zone in zones:
                    entry = []
                    entry.append(enterprise.name)
                    entry.append(domain.name)
                    entry.append(zone.name)
                    entry.append(zone.description)
                    table.append(entry)
        
        print tabulate(table,headers)
        '''
        table = []
        headers = {'Name', "ID"}
        for zone in zones:
            entry = []
            entry.append(zone.name)
            entry.append(zone.id)
            table.append(entry)
        
        print tabulate(table,headers)    
        
        
    def print_subnets(self,subnets):
    
        #Create table and table headers
        table = []
        headers = ["Subnet","Network","Netmask","Description"]
        
        for subnet in subnets:
            entry = []
            #entry.append(enterprise.name)
            #entry.append(domain.name)
            #entry.append(zone.name)
            entry.append(subnet.name)
            entry.append(subnet.address)
            entry.append(subnet.netmask)
            entry.append(subnet.description)
            table.append(entry)
        
        table = self.sort_table(table, 0)
        print tabulate(table,headers)
        print 'Number of subnets found: ' + str(len(table))
    
    def print_nsgs(self,nsgs):
        
        table = []
        headers = ["Name","Description","Bootstrap Status","TemplateID"]
        
        for nsg in nsgs:
                    
            entry = []
            entry.append(nsg.name)
            entry.append(nsg.description)
            entry.append(nsg.bootstrap_status)
            entry.append(nsg.template_id)
            table.append(entry)
        
        print tabulate(table,headers)
    
    def print_nsg_templates(self,nsg_templates):
        #Create table and table headers
        table = []
        headers = ["Name","Description","Template ID"]
        
        for template in nsg_templates:
            entry = []
            entry.append(template.name)
            entry.append(template.description)
            entry.append(template.id)
            table.append(entry)
        
        print tabulate(table,headers)
    
    def print_nsg_vlans(self,storage_object):    
        #Create table and table headers
        table = []
        headers = ["NSG Name","Port Name","Vlan Value"]
        
        i = 0
        
        print len(storage_object)
        
        for storage in storage_object:
            print i
            nsg = storage.nsg
            port = storage.port
            vlans = storage.vlans
            
            '''
            for vlan in vlans:
                print vlan.value
            '''
            
            for vlan in vlans:
                entry = []
                entry.append(nsg.name)
                entry.append(port.name)
                entry.append(vlan.value)
                table.append(entry)
            
            #i = i + 1
            
        print tabulate(table,headers)
    
            
        ''' 
        for nsg in nsgs:
            nsg.ns_ports.fetch(filter=port_prefix)
            ports = nsg.ns_ports
            for port in ports:
                port.vlans.fetch()
                vlans = port.vlans
                for vlan in vlans:
                    entry = []
                    entry.append(nsg.name)
                    entry.append(port.name)
                    entry.append(vlan.value)
                    table.append(entry)
        '''
    def print_bridge_interfaces(self,storage_object):
        #Create table and table headers
        table = []
        headers = ["Enterprise","Domain,","Zone","Subnet","vPort","Bridge"]
        
        for storage in storage_object:
            enterprise = storage.enterprise
            domain = storage.domain
            zone = storage.zone
            subnet = storage.subnet
            vport = storage.vport
            bridge = storage.interface
        
            entry = []
            entry.append(enterprise.name)
            entry.append(domain.name)
            entry.append(zone.name)
            entry.append(subnet.name)
            entry.append(vport.name)
            entry.append(bridge.name)

            table.append(entry)
                    
        print tabulate(table,headers)
    def print_ingress_security_policies(self,storage_object):
        #Create table and table headers
        table = []
        headers = ["Enterprise","Domain,","Policy Name","Priority","Enable Status","Forward IP Default","Forward Non-IP Default", "Allow Address Spoofing"]
        
        for storage in storage_object:
            enterprise = storage.enterprise
            domain = storage.domain
            security_policy = storage.security_policy
            
            entry = []
            entry.append(enterprise.name)
            entry.append(domain.name)
            entry.append(security_policy.name)
            entry.append(security_policy.priority)
            entry.append(security_policy.default_allow_ip)
            entry.append(security_policy.default_allow_non_ip)
            entry.append(security_policy.allow_address_spoof)
            
            table.append(entry)
        
        print tabulate(table,headers)
    
    def print_enterprise_auto_assignments(self, zfbs):
        table = []
        headers = ["Enterprise Auto Assignments","Match Attribute","Values"]
        
        for zfb in zfbs:
            entry = []
            entry.append(zfb.name) 
            entry.append(zfb.zfb_match_attribute)
            entry.append(zfb.zfb_match_attribute_values)
           
           
            table.append(entry)
        
        print tabulate(table,headers)
            
    #Sort table based on the passed column
    def sort_table(self,table,col=0):
        return sorted(table, key=operator.itemgetter(col))
    
    def __init__(self):
        '''
        Constructor
        '''
        