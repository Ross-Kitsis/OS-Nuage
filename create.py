'''
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
from netaddr import *

sys.path.append("./")

from vspk.v4_0 import *

from list import *
from Parsers import *

class Create(object):
    '''
    This class is the primary interface for creating objects in the Nuage VSD
    '''
    
    def create_enterprise(self, name = None, description = None, profile = None, local_as = None):
        """This function creates an enterprise object in the VSD
        
        :param name: The name of the enterprise
        :type name: str
        
        :param description: The description of the enterprise
        :type description: str
        
        :param profile_name: The name of the enterprise profile used as a template to create a new enterprise
        :type profile_name: str
        
        :param local_as: The local AS of the enterprise
        :type local_as: int
        
        :returns: enterprise - The enterprise object found or created
            
        """
        logger = logging.getLogger('create')
        logger.info("Creating new enterprises")
        
        csproot = self.__session.user
        
        profile_predicate = 'name == "%s"' % profile
        enterprise_profiles = self.__vspk_list.list_enterprise_profiles(predicate = profile_predicate)
        
        pid = enterprise_profiles[0].id
        
        # Create an enterprise
        enterprise = NUEnterprise(name=name, description=description, local_as = local_as, enterprise_profile_id = pid)
        csproot.create_child(enterprise)
        
        return enterprise
    
    def create_nsg(self,enterprise = None, name= None, description = None, template_name = None,
                   location = None, egress_qos_name = None, zfb_match_attribute = None, 
                   zfb_match_value = None):
        """This function searches creates a new NSg under the top level enerprise object passed. Once the enterprise has been 
        created the location, QoS properties and bootstrap information are also updated. 
        
        :param enterprise: The top level enterprise object
        :type enterprise: NUEnterprise
        
        :param nsg_name: The nsg name to search for or name of new nsg to create. 
        :type nsg_name: str
        
        :param template: The name of the NSG template to use when creating a new NSG
        :type template: str
        
        :param location: The location of the NSG
        :type location: str
        
        :param zfb_match_value: The MAC address of the NSG
        :type zfb_match_value: str
        
        :returns nsg - The NSG object found or created 
        """
        
        logger = logging.getLogger('create')
        logger.info("Creating new nsg " + name )
        
        template_predicate = None
        if template_name is not None:
            template_predicate = 'name beginswith "%s"' % template_name
            
        nsg_templates = self.__mpf.fetch_nsg_templates(predicate = template_predicate, enterprise = enterprise)
        
        template_id = nsg_templates[0].id
        
        nsg = NUNSGateway(name = name, description=description, template_id = template_id)
        
        enterprise.create_child(nsg)    
        
        logger.info('Updating NSG location')
        #Create location            
        nsg.locations.fetch()
        locations = nsg.locations            
        nsg_location = locations[0]
        nsg_location.address = location
        nsg_location.save()
        
        logger.info('Updating NSG bootstrap')
        #Create bootstrap info
        if zfb_match_value is not None:
            nsg.bootstraps.fetch()
            bootstrap = nsg.bootstraps[0]
            bootstrap.zfb_match_attribute = zfb_match_attribute
            bootstrap.zfb_match_value = zfb_match_value
            bootstrap.save()
        
        logger.info('Fetching and updating NSG WAN QoS profile')
        #Create QoS policies under existing VLANs
        csproot = self.__session.user
        qos_predicate = 'name beginswith "%s"' % egress_qos_name
        csproot.egress_qos_policies.fetch(filter = qos_predicate)
        qos_policies = csproot.egress_qos_policies[0]
        
        #print port
        for i in range(1,3):
            port_predicate = 'physicalName like "%s"' % ('port' + str(i))
        
            nsg.ns_ports.fetch(filter=port_predicate)
            ports = nsg.ns_ports
                    
            port = ports[0]
    
            port.vlans.fetch()
            vlans = port.vlans
            vlan = vlans[0]
            
            vlan.associated_egress_qos_policy_id = qos_policies.id  
            vlan.save()    

        return nsg
    
    def create_uplink_properties(self, nsg, physical_name ,mtu = None, speed = None, nat_traversal = None, role = None, pppoeConfig = None, 
                             username = None, password = None, mode = None, netmask = None, address = None, 
                             gateway = None, dns_address = None):
        """This function creates and modifies NSG uplink properties as required in 4.0R3
        
        :param nsg: The NSG to update
        :type nsg: NUNSGateway
        
        :param physical_name: The physical name of the port to modify
        :type physical_name: str
        
        :param mtu: The port MTU
        :type nsg_name: int
        
        :param speed: The speed of the port
        :type template: int
        
        :param nat_traversal: Determines if the port is behind NAT 
        :type location: str
        
        :param role: The role of the port
        :type role: str
        
        :param pppoeConfig: PPPoECOnfig (Unused - may be required for future)
        :type role: str
        
        :param username: (Unused - may be required for future)
        :type role: str
        
        :param password (Unused - may be required for future)
        :type password: str
        
        :param mode: Port mode
        :type role: str
        
        :param netmask: Unused
        :type netmask: str
        
        :param address: Tunused
        :type role: str
        
        :param gateway: unused
        :type role: str
        
        :param dns_address: unused
        :type role: str
        """
        
        logger = logging.getLogger('create')
        logger.info("Updating NSG uplink properties")
        
        port_predicate = 'physicalName like "%s"' % physical_name

        nsg.ns_ports.fetch(filter=port_predicate)
        ports = nsg.ns_ports
        port = ports[0]
        
        logger.info('Setting NSPort properties')
        #Set nsport properties and save
        port.mtu = mtu
        port.speed = speed
        port.nat_traversal = nat_traversal
        port.save()
    
        port.vlans.fetch()
        vlans = port.vlans
        vlan = vlans[0]
        
        logger.info('Setting uplink properties')    
        vlan.uplink_connections.fetch()
        uplink_connections = vlan.uplink_connections
        
        uplink_connection = uplink_connections[0]
        
        uplink_connection.role = role
        uplink_connection.username = username
        uplink_connection.password = password
        uplink_connection.mode = mode
        uplink_connection.netmask = netmask
        uplink_connection.gateway = gateway
        uplink_connection.dns_address = dns_address
        uplink_connection.save()
    
    def create_enterprise_auto_assignment(self,name = None, description = None, priority = None, match_attribute = None,
                                          match_values = None, enterprise = None):
        """This function creates ZFB entries with the specified entry values
        
        :param name: The name of the new ZFB entry
        :type name: str
        
        :param description: The description of the entry
        :type description: str
        
        :param priority: The priority of the entry
        :type priority: int
        
        :param match_attribute: The NSG attribute to match
        :type match_attribute: str
        
        :param match_values: The values to match
        :type match_values: list
        
        :param enterprise: The enterprise associated with the ZFB object
        :type role: NUEnterprise
        
        """
        
        logger = logging.getLogger('create')
        logger.info("Creating new ZFB entry")
        
        csproot = self.__session.user            
        enterprise_id = enterprise.id
        zfb = NUZFBAutoAssignment(name = name, description = description, priority = priority, 
                                      zfb_match_attribute = match_attribute, zfb_match_attribute_values = match_values,
                                      associated_enterprise_id = enterprise_id)    
        
        csproot.create_child(zfb)
        
        return zfb
    
    def create_domain_template(self, enterprise = None, template_name= None, description = None,
                               encryption = None, multicast = None, scope = None):
        """This function creates a new domain template
        
        :param enterprise: The enterprise under which to create the template
        :type enterprise: NUEnterprise
        
        :param template_name: The name of the template to create
        :type template_name: str
        
        :param description: The description of the template
        :type description: str
        
        :param encryption: Determines if the template has encryption enabled
        :type encryption: str
        
        :param multicast: Determines if the template has multicast enabled
        :type multicast: str
        
        :param scope: Determines the template entity scope
        :type scope: str
        
        """
        
        logger = logging.getLogger('create')
        logger.info("Creating new domain template")
        
        template = NUDomainTemplate(name=template_name, description=description, encryption = encryption, 
                                        multicast=multicast, entity_scope = scope)
        enterprise.create_child(template)
            
        return template
    
    def create_zone_template(self, domain_template = None, name = None, description = None, 
                             encryption = None, multicast = None, public = None):
        """This function creates a new domain template
        
        :param domain_template: The domain_template under which to create the zone_template
        :type enterprise: NUDomainTemplate
        
        :param name: The name of the template to create
        :type name: str
        
        :param description: The description of the template
        :type description: str
        
        :param encryption: Determines if the template has encryption enabled
        :type encryption: str
        
        :param multicast: Determines if the template has multicast enabled
        :type multicast: str
        
        :param scope: Determines if template is public
        :type scope: str
        
        """
        
        logger = logging.getLogger('create')
        logger.info("Creating new zone template")
        
        zone_template = NUZoneTemplate(name = name, description = description, encryption = encryption, 
                                       multicast=multicast, public_zone = public)
        
        domain_template.create_child(zone_template)
        
        return zone_template
    
    def create_ingress_policy_template(self, domain_template = None, name = None, active = None, 
                         allow_l2_spoof = None, default_allow_IP = None, default_allow_non_IP = None, priority = None, 
                         priority_type = None):
        """This function creates a new ingress policy
        
        :param domain_template: The domain_template under which to create the policy
        :type enterprise: NUDomainTemplate
        
        :param name: The name of the policy to create
        :type name: str
        
        :param active: Determines if the policy is active
        :type active: str
        
        :param allow_l2_spoof: Determines if the policy allows l2 spoofing
        :type allow_l2_spoof: str
        
        :param default_allow_ip: Determines if the policy allows IP traffic by default
        :type default_allow_ip: str
        
        :param default_allow_non_ip: Determines if the policy allows non IP traffic by default
        :type default_allow_non_ip: str
        
        :param priority: Determines if the policy priority (Only used if policy position is not top or bottom)
        :type priority: int
        
        :param priority_type: Determines if the policy type (top, middle,bottom)
        :type priority_type: str
        
        """
        
        logger = logging.getLogger('create')
        logger.info('Creating new policy template "%s"' %name )
        
        ingress_template = NUIngressACLTemplate(name = name, active=active, allow_l2_address_spoof=allow_l2_spoof, default_allow_ip = default_allow_IP,
                                                default_allow_non_ip = default_allow_non_IP, priority_type = priority_type, priority = priority)
        
        domain_template.create_child(ingress_template)
        
        return ingress_template
    
    def create_ingress_policy_entry(self,ingress_template = None, description = None, location = None, 
                                   network_type = None, protocol = None, action = None, etherType = None, DSCP = None,
                                   priority = None, source_port = None, destination_port = None, location_id = None, 
                                   stateful = None, flow_logging = None, stats_logging = None):
        """This function creates a new ingress policy entry
        
        :param ingress_template: The ingress_template under which to create the entry
        :type ingress_template: NUIngressIngressTemplate
        
        :param description: The description of the policy to entry
        :type description: str
        
        :param location: The location type of the entry
        :type location: str
        
        :param network_type: The type of network entry is applicable to
        :type network_type: str
        
        :param protocol: The protocol the entry applies to
        :type protocol: str
        
        :param action: The action to take (Drop/forward)
        :type action: str
        
        :param priority: Determines if the policy priority (Only used if policy position is not top or bottom)
        :type priority: int
        
        :param source_port: Source port to apply entry to
        :type source_port: str
        
        :param destination_port: Destination port to apply entry to
        :type destination_port: str
        
        :param location_id: ID of the location to which the entry applies
        :type location_id: str
        
        :param stateful: Determines if the entry is stateful
        :type stateful: str
        
        :param flow_logging: Determines if the entry to log flows
        :type flow_logging: str
        
        :param stats_logging: Determines if the entry should log stats
        :type stats_logging: str
        """
        
        logger = logging.getLogger('create')
        logger.info('Creating new ingress policy entry "%s"' % description)
        
        entry = NUIngressACLEntryTemplate(description = description, location_type=location, network_type = network_type, protocol = protocol,
                                          action = action, ether_type = etherType, dscp = DSCP, priority = priority,
                                          source_port = source_port, destination_port = destination_port, location_id = location_id,
                                          stateful = stateful, stats_logging_enabled = stats_logging, flow_logging_enabled = flow_logging)
        ingress_template.create_child(entry)
        
        return entry
    
    def create_egess_policy_template(self, domain_template = None, name = None, active = None, 
                                  default_allow_IP = None, default_allow_non_IP = None, priority = None, 
                                  priority_type = None, default_install_implicit_rules = None):
        
        """This function creates a new ingress policy
        
        :param domain_template: The domain_template under which to create the policy
        :type enterprise: NUDomainTemplate
        
        :param name: The name of the policy to create
        :type name: str
        
        :param active: Determines if the policy is active
        :type active: str
        
        :param default_allow_ip: Determines if the policy allows IP traffic by default
        :type default_allow_ip: str
        
        :param default_allow_non_ip: Determines if the policy allows non IP traffic by default
        :type default_allow_non_ip: str
        
        :param priority: Determines if the policy priority (Only used if policy position is not top or bottom)
        :type priority: int
        
        :param priority_type: Determines if the policy type (top, middle,bottom)
        :type priority_type: str
        
        :param default_install_implicit_rules: Install implicit rules
        :type default_install_implicit_rules: bool
        
        
        """
        logger = logging.getLogger('create')
        logger.info('Creating new ingress policy entry "%s"' % name)
        
        egress_template = NUEgressACLTemplate(name=name, active=active, default_allow_ip = default_allow_IP, default_allow_non_ip = default_allow_non_IP,
                                              priority_type = priority_type, default_install_acl_implicit_rules = default_install_implicit_rules,
                                              priority = priority)
        
        domain_template.create_child(egress_template)
        
        return egress_template
    
    def create_egress_policy_entry(self, egress_template = None, description = None, location = None, 
                                            network_type = None, protocol = None, action = None, etherType = None, DSCP = None,
                                            priority = None, source_port = None, destination_port = None, num = None, location_id = None, 
                                            stateful = None, flow_logging = None, stats_logging = None):
        """This function creates a new ingress policy entry
        
        :param ingress_template: The ingress_template under which to create the entry
        :type ingress_template: NUIngressIngressTemplate
        
        :param description: The description of the policy to entry
        :type description: str
        
        :param location: The location type of the entry
        :type location: str
        
        :param network_type: The type of network entry is applicable to
        :type network_type: str
        
        :param protocol: The protocol the entry applies to
        :type protocol: str
        
        :param action: The action to take (Drop/forward)
        :type action: str
        
        :param priority: Determines if the policy priority (Only used if policy position is not top or bottom)
        :type priority: int
        
        :param source_port: Source port to apply entry to
        :type source_port: str
        
        :param destination_port: Destination port to apply entry to
        :type destination_port: str
        
        :param location_id: ID of the location to which the entry applies
        :type location_id: str
        
        :param stateful: Determines if the entry is stateful
        :type stateful: str
        
        :param flow_logging: Determines if the entry to log flows
        :type flow_logging: str
        
        :param stats_logging: Determines if the entry should log stats
        :type stats_logging: str
        """
        
        logger = logging.getLogger('create')
        logger.info('Creating new egress policy entry "%s"' % description)
        
        egress_policy = NUEgressACLEntryTemplate(description = description, location_type=location, network_type = network_type, protocol = protocol,
                                          action = action, ether_type = etherType, dscp = DSCP, priority = priority,
                                          source_port = source_port, destination_port = destination_port, location_id = location_id,
                                          stateful = stateful, flow_logging = flow_logging, stats_logging = stats_logging)
        
        egress_template.create_child(egress_policy)
    
    def create_domain(self, enterprise, template, name, description, encryption, pat_enabled, underlay_enabled):
        """This function creates a new ingress policy entry
        
        :param enterprise: The enterprise under which to create the domain
        :type enterprise: NUEnterprise
        
        :param template: The domain template to instantiate
        :type template: NUDomainTemplate
        
        :param name: The name of the new domain
        :type name: str
        
        :param description: The description of the policy to entry
        :type description: str
        
        :param encryption: Determines if domain is encrypted
        :type encryption: bool
        
        :param pat_enabled: Determines if PAT is supported
        :type pat_enabled: bool
        
        :param underlay_enabled: Determines if underlay enabled
        :type underlay_enabled: str
        """
        logger = logging.getLogger('create')
        logger.info('Creating new egress policy entry "%s"' % description)
        
        domain = NUDomain(name = name, description = description, template_id = template.id,underlay_enabled= underlay_enabled
                                                , pat_enabled=pat_enabled, encryption = encryption)
    
        enterprise.create_child(domain)
    
        return domain
    
    def create_zone(self, name = None, description = None, encryption = None, 
                    multicast = None, public = None, domain = None):
        
        """This function creates a new zone
        
        :param domain: The enterprise under which to create the zone
        :type domain: NUDomain
        
        :param name: The name of the new zone
        :type name: str
        
        :param description: The description of the zone
        :type description: str
        
        :param multicast: Determines if multicast is supported
        :type multicast: bool
        
        :param public: Determines if zone is public
        :type public: bool
        """
        
        logger = logging.getLogger('create')
        logger.info('Creating new zone policy entry "%s"' % name)
        zone = NUZone(name = name, description = description, encryption = encryption, multicast = multicast,
                      public_zone = public)
        
        domain.create_child(zone)
        
        return zone
    
    def create_subnets(self, zone = None, name = None, encryption = None, pat_enable = None, 
                       underlay_enabled = None, dns_values = None, network = None,
                       mask = None):
        
        """This function creates a new zone
        
        :param zone: The zone under which to create the subnet
        :type zone: NUZone
        
        :param name: The name of the new subnet
        :type name: str
        
        :param encryption: Determines if subnet supports encryption
        :type encryption: bool
        
        :param pat_enable: Determines if pat is supported
        :type pat_enable: bool
        
        :param underlay_enabled: Determines if underlay is enabled
        :type underlay_enabled: bool
        
        :param dns_values: List of DNS values
        :type dns_values: list
        
        :param network: Network address of the subnet
        :type network: str
        
        :param mask: subnet mask of network
        :type mask: str
        
        """
        
        logger = logging.getLogger('create')
        logger.info('Creating new subnet "%s"' % name)
        
        subnet = NUSubnet(name=name, address = network, netmask = mask, pat_enabled = pat_enable, encryption = encryption,
                  underlay_enabled = underlay_enabled)

        zone.create_child(subnet)
        
        if dns_values:
            dns_op = NUDHCPOption(type = '06', value = dns_values)
            subnet.create_child(dns_op)
        
        return subnet
    
    def create_dhcp_range(self, subnet = None, network = None, mask = None, reserve = 0.5, bridge_type = u'BRIDGE'):
        """This function creates a DHCP range under a specified subnet. By default 50% of the subnets network is
        used for DHCP - the lower range of the network is used for dhcp.
        
        :param subnet: The subnet under which to create the options
        :type zone: NUSubnet
        
        :param network: The subnet network
        :type network: str
        
        :param mask: The subnet mask
        :type mask: bool
        
        :param reserve: Percentage of range ot reserve
        :type reserve: bool
        
        :param bridge_type: Type of bridge
        :type bridge_type: str
        
        """
        logger = logging.getLogger('create')
        logger.info('Creating new dhcp range')

        #Build a range; leave first 50% of addresses outside of range
        ip_net = network+"/"+ mask
        net = IPNetwork(ip_net)
        
        net_add = IPAddress(network)
        
        net_size = net.size
        min_address = str(net_add + int(net_size * reserve))
        max_address = str(net_add + net.size - 2)
        pool_type = bridge_type
        
        dhcp_range = NUAddressRange(dhcp_pool_tpye = pool_type, min_address = min_address, max_address = max_address)
        
        subnet.create_child(dhcp_range)
    
        return dhcp_range    
    
    def create_vport(self, port = None, subnet = None, nsg = None,vlan = None, vport_name = None):
        """This function creates a DHCP range under a specified subnet. By default 50% of the subnets network is
        used for DHCP - the lower range of the network is used for dhcp.
        
        :param port: The physical name of the vPort
        :type port: str
        
        :param subnet: The subnet to which to attach the vPort
        :type subnet: NUSubnet
        
        :param nsg: The NSG to attach to the vPor
        :type nsg: NUNSGateway
        
        :param vlan: Vlan number to attach to vport
        :type vlan: int
        
        :param vport_name: Name of the vport
        :type vport_name: str
        
        """
        
        logger = logging.getLogger('create')
        logger.info('Creating new vport "%s"' % vport_name)
        
        #print port
        port_predicate = 'physicalName like "%s"' % port
        vlan_predicate = 'value == "%s"' % vlan
        
        nsg.ns_ports.fetch(filter=port_predicate)
        ports = nsg.ns_ports
                
        port = ports[0]
        
        port.vlans.fetch()
        vlans = port.vlans
        
        for v in vlans:
            if int(v.value) == int(vlan):
                vlan = v
                break
        
        vport = NUVPort(name = vport_name, decription = vport_name, type = u'BRIDGE', address_spoofing = u'ENABLED', vlanid = vlan.id )
        subnet.create_child(vport)
        return vport
    
    def create_bridge_interface(self, vport = None, bridge_interface_name = None):
        """This function creates a DHCP range under a specified subnet. By default 50% of the subnets network is
        used for DHCP - the lower range of the network is used for dhcp.
        
        :param vport: The vPort to which the interface is attached
        :type vport: NUVport
        
        :param bridge_interface_name: Name of the BI to create
        :type bridge_interface_name: str
        
        """
        
        logger = logging.getLogger('create')
        logger.info('Creating new bridge interface "%s"' % bridge_interface_name)
        
        BI = NUBridgeInterface(name = bridge_interface_name)
        vport.create_child(BI)
        
        return BI
    
    def create_domain_qos(self, domain = None, name = None, description = None, trust = None, forwarding_class = None, active = None):
        """This function creates a domain QoS policy under the specified domain
        
        :param domain: The domain in which to create the QoS policy
        :type domain: NUDomain
        
        :param name: Name of the policy to create
        :type name: str
        
        :param description: Description of the policy
        :type description: str
        
        :param trust: Enable/Disable trust
        :type trust: bool
        
        :param forwarding_class: Forwarding class of the policy
        :type forwarding_class: str
        
        :param active: Enable/Disable policy
        :type active: bool
        
        """
        
        logger = logging.getLogger('create')
        logger.info('Creating new domain QoS policy "%s"' % name)
        
        policy = NUQOS(name = name, description = description, trusted_forwarding_class = trust, service_class = forwarding_class, active= active)
        domain.create_child(policy)
        
        return policy
            
    def __init__(self, session):
        '''
        Constructor
        
        The passed connection is used when making calls to the VSD
        
        '''
        self.__session = session
        self.__log = logging.getLogger("create_service")
        self.__vspk_list = List(session)
        self.__mpf = MultiPageFetch(session)
                
        
        
        