'''    
This class is the primary interface for listing objects in the Nuage VSD

Author: Ross Kitsis
Contact: Ross.Kitsis@telus.com
'''
import sys
import argparse
import os
import ConfigParser
from tabulate import tabulate
import requests
import bambou
import logging

sys.path.append("./")

from vspk.v4_0 import *
from vspk.utils import set_log_level

from Parsers import *

class List(object):

    
    def list_enterprise_profiles(self, predicate = None):
        """ Fetches defined enterprise profiles
        
        Retrieves globally defined enterprise profile objects and returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        :returns: list -- The list of retrieved enterprise profiles 
        """
        
        logger = logging.getLogger('list')
        logger.info("Fetching enterprise profiles")
        
        profiles = self.__mpf.fetch_enterprise_profiles(predicate)
        
        return profiles
    
    def list_enterprises(self, predicate = None):
        """ Fetches defined enterprises 
        
        Retrieves globally defined enterprise objects and returns all retrieved objects in a list. 
        The objects retrieved may be filtered by passing a search predicate as defined by Nuage
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str
        :returns: list -- The list of retrieved enterprises 
        """
        logger = logging.getLogger('list')
        logger.info("Fetching enterprises")
        enterprises = self.__mpf.fetch_enterprises(predicate)
        
        return enterprises
    
    def list_nsgs(self, predicate = None, enterprise = None):
        """Fetches NSGs defined under the specified enterprise 
        
        Retrieves NSGs defined under the specified enterprise, the search may be filtered by passing a predicate as defined by Nuage. 
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str        
        
        :param enterprise: The enterprise object under which to search
        :type enterprise: NUEnterprise
        
        :returns: list -- The list of retrieved NSGs
        
        """
        logger = logging.getLogger('list')
        logger.info("Fetching nsgs")
        
        nsgs = self.__mpf.fetch_nsg(predicate = predicate, enterprise = enterprise)
                
        return nsgs
    
    def list_enterprise_auto_assignments(self, predicate = None):
        """Fetches ZFBs defined under the specified enterprise 
        
        Retrieves NSGs defined under the specified enterprise, the search may be filtered by passing a predicate as defined by Nuage. 
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str        
        
        :returns: list -- The list of retrieved ZFBs
        
        """
        logger = logging.getLogger('list')
        logger.info("Fetching ZFB auto assignments")
        
        zfb_auto_assign = self.__mpf.fetch_enterprise_auto_assignments(predicate = predicate)
        return zfb_auto_assign
    
    def list_domain_templates(self,enterprise = None , predicate =None):
        """Fetches domain templates defined under the passed enterprise. results may be filtered by passing a predicate as
        defined by Nuage.
        
        :param enterprise: The enterprise in which to search
        :type enterprise: NUEnterprise
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str        
        
        :returns: list -- The list of retrieved domain template
        
        """
        logger = logging.getLogger('list')
        logger.info("Fetching domain templates")
        
        return self.__mpf.fetch_domain_templates(predicate, enterprise)
    
    def list_domains(self, enterprise = None, predicate=None):
        """Fetches domains defined under the passed enterprise. results may be filtered by passing a predicate as
        defined by Nuage.
        
        :param enterprise: The enterprise in which to search
        :type enterprise: NUEnterprise
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str        
        
        :returns: list -- The list of retrieved domains
        
        """
        logger = logging.getLogger('list')
        logger.info("Fetching defined domains")
        
        return self.__mpf.fetch_domains(predicate, enterprise)
    
    def list_zones(self, domain = None, predicate=None):
        """Fetches zones defined under the passed domain. results may be filtered by passing a predicate as
        defined by Nuage.
        
        :param domain: The domain in which to search
        :type domain: NUDomain
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str        
        
        :returns: list -- The list of retrieved zones
        
        """
        logger = logging.getLogger('list')
        logger.info("Fetching defined zones")
        
        zones = self.__mpf.fetch_zones(predicate = predicate, domain = domain)
        return zones
    
    def list_ingress_policies(self, predicate = None, domain = None):
        
        """Fetches ingress policies defined under the passed domain. results may be filtered by passing a predicate as
        defined by Nuage.
        
        :param domain: The domain in which to search
        :type domain: NUDomain
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str        
        
        :returns: list -- The list of retrieved ingress policies
        
        """
        logger = logging.getLogger('list')
        logger.info("Fetching defined ingress policies")        
             
        policies = self.__mpf.fetch_ingress_security_policies(predicate = predicate, domain= domain)

        return policies
    
    def list_subnet(self, predicate = None, zone = None):
        """Fetches subnets defined under the passed zone. results may be filtered by passing a predicate as
        defined by Nuage.
        
        :param zone: The zone in which to search
        :type zone: NUZone
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str        
        
        :returns: list -- The list of retrieved subnets
        
        """
        logger = logging.getLogger('list')
        logger.info("Fetching defined subnets")   
        
        subnets = []
        subnets = subnets + self.__mpf.fetch_subnets(predicate = predicate, zone=zone)
        
        return subnets
    
    def list_vports(self,predicate = None,subnet = None):
        """Fetches vports defined under the passed subnet. results may be filtered by passing a predicate as
        defined by Nuage.
        
        :param subnet: The subnet in which to search
        :type subnet: NUSubnet
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str        
        
        :returns: list -- The list of retrieved vports
        
        """
        logger = logging.getLogger('list')
        logger.info("Fetching defined vports")  
        
        vports = self.__mpf.fetch_vports(predicate = predicate, subnet = subnet)
        return vports
        #subnet = subnet, vport_prefix = vport_name
    
    def list_bridge_interfaces(self, predicate = None, vport = None):
        """Fetches bridge interfaces defined under the passed vPort. results may be filtered by passing a predicate as
        defined by Nuage.
        
        :param vport: The vPort in which to search
        :type vport: NUVPort
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str        
        
        :returns: list -- The list of retrieved bridge interfaces
        
        """
        logger = logging.getLogger('list')
        logger.info("Fetching defined bridge interfaces")  
        
        interfaces = self.__mpf.fetch_bridge_interfaces(predicate = predicate, vport = vport)    
        
        return interfaces

    def list_egress_policies(self, predicate = None, domain = None):
        """Fetches egress policies defined under the passed domain. results may be filtered by passing a predicate as
        defined by Nuage.
        
        :param domain: The domain in which to search
        :type domain: NUDomain
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str        
        
        :returns: list -- The list of retrieved bridge interfaces
        
        """
        logger = logging.getLogger('list')
        logger.info("Fetching defined egress policies")        
        policies = self.__mpf.fetch_egress_security_policies(predicate = predicate, domain= domain)
        return policies
    
    def list_domain_qos_policies(self, predicate = None, domain = None):
        """Fetches qos defined under the passed domain. results may be filtered by passing a predicate as
        defined by Nuage.
        
        :param domain: The domain in which to search
        :type domain: NUDomain
        
        :param predicate: The search predicate used to filter search results to return (Default = None)
        :type predicate: str        
        
        :returns: list -- The list of retrieved qos policies
        """
        logger = logging.getLogger('list')
        logger.info("Fetching defined qos policies")        
        policies = self.__mpf.fetch_domain_qos(predicate = predicate, domain= domain)
        return policies
    
    def __init__(self, session):
        '''
        Constructor
        '''
        self.__session = session
        self.__mpf =  MultiPageFetch(self.__session)
        self.__log = logging.getLogger("list")
                