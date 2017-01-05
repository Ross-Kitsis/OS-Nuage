'''
Author: Ross Kitsis
Contact: Ross.Kitsis@telus.com
'''
from sys_config_parser import *
import math

class MultiPageFetch(object):
    '''
    General object fetch class.
    This class performs all object fetch operations. Object fetching is performed one page at 
    a time, all pages are consolidated into a list before returning the results. 
    Fetching multiple pages ensures all defined objects are found. 
    
    '''
   
    def fetch_enterprises(self, predicate=None): 
        """ Fetches defined enterprises, compiles all pages into a list before returning
        
        Retrieves globally defined enterprise objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        :returns: list -- The list of retrieved enterprises 
        """
        
        csproot = self.__session.user

        if predicate is None:
                
            #count = parent.domains.count(filter = domain_predicate)[2]
            count = csproot.enterprises.count()[2]
            num_page = int(math.ceil(count/float(self.__max_page_size)))
                    
            for i in range(num_page):
                #parent.domains.fetch(filter = domain_predicate, page=str(i))
                csproot.enterprises.fetch(page=str(i))            
        else:    
            count = csproot.enterprises.count(filter = predicate)[2]
            num_page = int(math.ceil(count/float(self.__max_page_size)))
                        
            for i in range(num_page):
                csproot.enterprises.fetch(filter = predicate, page=str(i))
                            
        return csproot.enterprises
    
    def fetch_enterprise_profiles(self,predicate=None):
        """ Fetches defined enterprise profiles, compiles all pages into a list before returning
        
        Retrieves globally defined enterprise profile objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        :returns: list -- The list of retrieved enterprise profiles 
        """
        
        csproot = self.__session.user

        if predicate is None:
            count = csproot.enterprise_profiles.count()[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                csproot.enterprise_profiles.fetch(page=str(i))
        else:
            count = csproot.enterprise_profiles.count(filter=predicate)[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                csproot.enterprise_profiles.fetch(filter=predicate,page=str(i))
        
        return csproot.enterprise_profiles
        
    def fetch_domains(self,predicate, enterprise):
        """ Fetches defined domains, compiles all pages into a list before returning
        
        Retrieves globally defined domain objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param enterprise: The enterprise object under which to search
        :type enterprise: NUEnterprise
        
        :returns: list -- The list of retrieved domains 
        """
        domains = []
        if predicate is None:
            count = enterprise.domains.count()[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                enterprise.domains.fetch(page=str(i))
                for domain in enterprise.domains:
                    domains.append(domain)
                enterprise.domains.flush()
        else:
            count = enterprise.domains.count(filter=predicate)[2]          
            num_page = self.get_num_page(count)
            for i in range(num_page):
                enterprise.domains.fetch(filter=predicate,page=str(i))
                for domain in enterprise.domains:
                    domains.append(domain)
                enterprise.domains.flush()
        return domains
    
    def fetch_domain_templates(self,predicate,enterprise):
        """ Fetches defined domain templates, compiles all pages into a list before returning
        
        Retrieves globally defined domain template objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param enterprise: The enterprise object under which to search
        :type enterprise: NUEnterprise
        
        :returns: list -- The list of retrieved domain templates
        """
        
        if predicate is None:
            count = enterprise.domain_templates.count()[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                enterprise.domain_templates.fetch(page=str(i))            
        else:
            count = enterprise.domain_templates.count(filter=predicate)[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                enterprise.domain_templates.fetch(filter=predicate,page=str(i))
            
        return enterprise.domain_templates
    
    def fetch_zones(self,predicate,domain):
        """ Fetches defined zones, compiles all pages into a list before returning
        
        Retrieves globally defined zone objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param domain: The domain object under which to search
        :type domain: NUDomain
        
        :returns: list -- The list of retrieved zones 
        """
        if predicate is None:
            count = domain.zones.count()[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                domain.zones.fetch(page=str(i))
        else:
            count = domain.zones.count(filter=predicate)[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                domain.zones.fetch(filter=predicate,page=str(i))
        
        #print domain.zones[0].name
        
        return domain.zones
    
    def fetch_subnets(self,predicate,zone):
        """ Fetches defined subnets, compiles all pages into a list before returning
        
        Retrieves globally defined subnets objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param zone: The zone object under which to search
        :type zone: NUZone
        
        :returns: list -- The list of retrieved subnets 
        """
        subnets = []
        if predicate is None:
            #print 'Predicate none'
            count = zone.subnets.count()[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                zone.subnets.fetch(page=str(i))
                for subnet in zone.subnets:
                    subnets.append(subnet)
                zone.subnets.flush()
        else:
            #print 'Predicate not none'
            count = zone.subnets.count(filter=predicate)[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                zone.subnets.fetch(filter=predicate,page=str(i))
                for subnet in zone.subnets:
                    subnets.append(subnet)
                zone.subnets.flush()
                
        return subnets
    
    def fetch_vports(self,predicate,subnet):
        """ Fetches defined vports, compiles all pages into a list before returning
        
        Retrieves globally defined vport objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param subnet: The subnet object under which to search
        :type subnet: NUSubnet
        
        :returns: list -- The list of retrieved vports 
        """
        ports = []
        count = subnet.vports.count(filter=predicate)[2]
        num_page = self.get_num_page(count)
        for i in range(num_page):
            subnet.vports.fetch(filter=predicate, page=str(i))
            for port in subnet.vports:
                ports.append(port)
            subnet.vports.flush()
        
        return ports
        
    def fetch_bridge_interfaces(self,predicate,vport):
        """ Fetches defined bridge interfaces, compiles all pages into a list before returning
        
        Retrieves globally defined bridge interface objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param domain: The vport object under which to search
        :type domain: NUVPort
        
        :returns: list -- The list of retrieved bridge interfaces 
        """
        
        interfaces = []
        count = vport.bridge_interfaces.count(filter=predicate)[2]
        num_page = self.get_num_page(count)
        for i in range(num_page):
            vport.bridge_interfaces.fetch(filter=predicate,page=str(i))
            for bridge in vport.bridge_interfaces:
                interfaces.append(bridge)
            vport.bridge_interfaces.flush()
        
        return interfaces
        
    def fetch_nsg(self,predicate,enterprise): 
        """ Fetches defined NSGs, compiles all pages into a list before returning
        
        Retrieves globally defined NSG objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param domain: The enterprise object under which to search
        :type domain: NUEnterprise
        
        :returns: list -- The list of retrieved zones 
        """
        nsgs = []
        if predicate is None:
            count = enterprise.ns_gateways.count()[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                enterprise.ns_gateways.fetch(page=str(i))
                for ent in enterprise.ns_gateways:
                    nsgs.append(ent)
                enterprise.ns_gateways.flush()
        else:
            count = enterprise.ns_gateways.count(filter=predicate)[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                enterprise.ns_gateways.fetch(filter=predicate,page=str(i))
                for ent in enterprise.ns_gateways:
                    nsgs.append(ent)
                enterprise.ns_gateways.flush()
        return nsgs
    
    def fetch_nsg_templates(self,predicate,enterprise):
        """ Fetches defined NSG templates, compiles all pages into a list before returning
        
        Retrieves globally defined NSG template objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param domain: The enterprise object under which to search
        :type domain: NUEnterprise
        
        :returns: list -- The list of retrieved zones 
        """
        nsg_templates = []
    
        count = enterprise.ns_gateway_templates.count(filter=predicate)[2]
        num_page = self.get_num_page(count)
        for i in range(num_page):
            enterprise.ns_gateway_templates.fetch(filter=predicate,page=str(i))
            for template in enterprise.ns_gateway_templates:
                nsg_templates.append(template)
            enterprise.ns_gateway_templates.flush()
            
        return nsg_templates
        
        '''
        if predicate is None:
            count = enterprise.ns_gateway_templates.count()[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                enterprise.ns_gateway_templates.fetch(page=str(i))
                for template in enterprise.ns_gateway_templates:
                    nsg_templates.append(template)
        else:
            count = enterprise.ns_gateway_templates.count(filter=predicate)[2]
            num_page = self.get_num_page(count)
            for i in range(num_page):
                enterprise.ns_gateway_templates.fetch(filter=predicate,page=str(i))
                for template in enterprise.ns_gateway_templates:
                    nsg_templates.append(template)
        '''
    
    def fetch_port_vlans(self,port):
        """ Fetches defined port vlans, compiles all pages into a list before returning
        
        Retrieves globally defined port vlan objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param domain: The port object under which to search
        :type domain: NUPort
        
        :returns: list -- The list of retrieved port vlans 
        """
        vlans = []
        count = port.vlans.count()[2]
        num_page = self.get_num_page(count)
        for i in range(num_page):
            port.vlans.fetch(page=str(i))
            for vlan in port.vlans:
                
                #print vlan.value
                
                vlans.append(vlan)
            port.vlans.flush()
        return vlans
     
    def fetch_ingress_security_policies(self,predicate, domain):     
        """ Fetches defined ingress security policies, compiles all pages into a list before returning
        
        Retrieves globally defined ingress security objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param domain: The domain object under which to search
        :type domain: NUDomain
        
        :returns: list -- The list of retrieved ingress security policies 
        """
        security_templates = []
    
        count = domain.ingress_acl_templates.count(filter=predicate)[2]
        num_page = self.get_num_page(count)
        for i in range(num_page):
            domain.ingress_acl_templates.fetch(filter=predicate,page=str(i))
            for template in domain.ingress_acl_templates:
                security_templates.append(template)
            domain.ingress_acl_templates.flush()
            
        return security_templates
    
    def fetch_egress_security_policies(self,predicate, domain):
        """ Fetches egress security policies, compiles all pages into a list before returning
        
        Retrieves globally defined egress security policy objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param domain: The domain object under which to search
        :type domain: NUDomain
        
        :returns: list -- The list of retrieved egress security policies
        """
        security_templates = []
    
        count = domain.egress_acl_templates.count(filter=predicate)[2]
        num_page = self.get_num_page(count)
        for i in range(num_page):
            domain.egress_acl_templates.fetch(filter=predicate,page=str(i))
            for template in domain.egress_acl_templates:
                security_templates.append(template)
            domain.egress_acl_templates.flush()
            
        return security_templates
        
        
    def fetch_enterprise_auto_assignments(self,predicate):
        """ Fetches defined enterprise auto assignments, compiles all pages into a list before returning
        
        Retrieves globally defined enterprise auto assignment objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :returns: list -- The list of retrieved zones 
        """
        zfbs = []
        
        csproot = self.__session.user
        
        count = csproot.zfb_auto_assignments.count(filter=predicate)[2]
        num_page = self.get_num_page(count)
        for i in range(num_page):
            csproot.zfb_auto_assignments.fetch(filter=predicate,page=str(i))
            for assign in csproot.zfb_auto_assignments:
                zfbs.append(assign)
            csproot.zfb_auto_assignments.flush()
        
        return zfbs    
    
    def fetch_domain_qos(self, predicate, domain):
        """ Fetches defined domain QoS policies, compiles all pages into a list before returning
        
        Retrieves globally defined domain QoS policy objects, compiles results and finally returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        
        :param domain: The domain object under which to search
        :type domain: NUDomain
        
        :returns: list -- The list of retrieved domain QoS policies 
        """
        
        policies = []
        
        count = domain.qoss.count(filter=predicate)[2]
        num_page = self.get_num_page(count)
        for i in range(num_page):
            domain.qoss.fetch(filter=predicate,page=str(i))
            for qos in domain.qoss:
                policies.append(qos)
            domain.qoss.flush()
            
        return policies
    
    def get_num_page(self,count):
        return int(math.ceil(count/float(self.__page_size)))
    
    def __init__(self, session):
        '''
        Constructor
        '''
        
        self.__session = session
        self.__enterprises = None
        self.__enterprise_profiles = None
        self.__domains = None
        self.__domain_templates = None
        self.__zones = None
        self.__subnets = None
        self.__bridge_interfaces = None
        
        cparser = SysConfigParser(session)
        self.__page_size = cparser.get_page_size()
        self.__max_page_size = cparser.get_max_page_size()
        
        