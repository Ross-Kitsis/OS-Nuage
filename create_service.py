'''Standard service creation script

.. moduleauthor:: Ross Kitsis <Ross.Kitsis@telus.com>
'''

import sys
import argparse
import os
import ConfigParser
import requests
import bambou
import xml.etree.ElementTree as ET
import logging
import netaddr

from lxml import etree, objectify
from lxml.etree import XMLSyntaxError

from vspk.v4_0 import *
from vspk.utils import set_log_level

from list import *
from create import *
from utils import update_zfb_values

default_params = dict()
session = None
mpf = None
op = None

BASE_CONFIG_FILE = "base_config.xml"

#Domain properties

BI_ENCRYPTION = "ENABLED"
BI_PATEnabled = "ENABLED"
BI_UNDERLAYENABLED = "ENABLED"
BI_ACL = "ACL-1"

L3_ENCRYPTION = 'ENABLED' 
L3_PATEnabled = "ENABLED"
L3_UNDERLAYENABLED = "ENABLED"

L3_BI_ENCRYPTION = 'ENABLED'
L3_BI_PATEnabled = "ENABLED"
L3_BI_UNDERLAYENABLED = "ENABLED"

#Zone properties

DEFAULT_ZONE_ENCRYPTION = u'INHERITED'
DEFAULT_ZONE_MULTICAST = u'INHERITED'
DEFAULT_ZONE_PUBLIC = False
DEFAULT_SPOKE_DESCRIPTION = u'Spoke'

#Subnet properties

BI_SUBNET_ENCRYPTION = u'DISABLED'
BI_SUBNET_PAT = u'INHERITED'
BI_SUBNET_UNDERLAY = u'INHERITED'

BI_ACL_SUBNET_ENCRYPTION = u'DISABLED'
BI_ACL_SUBNET_PAT = u'INHERITED'
BI_ACL_SUBNET_UNDERLAY = u'INHERITED'

L3_SUBNET_ENCRYPTION = u'ENABLED'
L3_SUBNET_PAT = u'DISABLED'
L3_SUBNET_UNDERLAY = u'DISABLED'

L3_BI_ACL_SUBNET_ENCRYPTION = u'ENABLED'
L3_BI_ACL_SUBNET_PAT = u'DISABLED'
L3_BI_ACL_SUBNET_UNDERLAY = u'DISABLED'

L3_BI_SUBNET_ENCRYPTION = u'ENABLED'
L3_BI_SUBNET_PAT = u'ENABLED'
L3_BI_SUBNET_UNDERLAY = u'ENABLED'

ZFB_MATCH_ATTRIBUTE = u'MAC_ADDRESS' 

def main():
    
    logger = logging.getLogger('create_service')
    
    path =  os.path.dirname(os.path.abspath(__file__)) + "/create_service.log"
    print path
    
    logging.basicConfig(level=logging.INFO,
                        format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename = path,
                        filemode='w')

    fh = logging.FileHandler(path)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    set_log_level(logging.INFO, fh)
    
    logger.info('Initializing')
    parser = ArgParser()
    parser = argparse.ArgumentParser(parents=[parser.getParser()], 
                                     description='Command line for running VSPK scripts.',)
    parser.add_argument('-template', help='Path to template file containing service definition')
    
    logger.info('Parsing default arguments')
    args = parser.parse_args()
    
    user = unicode(args.user)
    password = unicode(args.password)
    csp = unicode(args.organization)
    api = unicode(args.api)
    version = unicode(args.version)
    template_file = args.template
    
    #Read xml file and begin parsing tree
    tree = ET.parse(template_file)
    root = tree.getroot()
    
    global default_params
    
    default_params['api'] = api
    default_params['user'] = user
    default_params['password'] = password
    default_params['version'] =  version
    default_params['csp'] = csp
    default_params['root'] = root
    
    logger.info('Creating and starting session to VSD')
    global session
    session = NUVSDSession(username = user, password = password, enterprise = csp, api_url = api)
    session.start()
    
    logger.info('Instantiating utility objects')
    global mpf
    mpf = MultiPageFetch(session)
    
    global op
    op = ObjectPrinter()
    
    global create
    create = Create(session)
    
    global vspk_list
    vspk_list = List(session)
    
#Parse organization objects in the XML                    
def parse_organizations(root):
    organizations = root.find('organizations')       
    return organizations   

#parse nsg objects in XML
def parse_nsgs(root):
    nsgs = root.find('nsgs')
    return nsgs

#Parse service objects in XML
def parse_services(root):
    services = root.find('services')
    return services

#Parse zone objects
def parse_zones(root):
    zones = root.find('zones')
    return zones

#Parse subnet objects
def parse_subnets(root):
    subnets = root.find('subnets')
    return subnets

#Fetch vPort objects
def parse_vports(root):
    vports = root.find('vports')
    return vports

def parse_bridge_interfaces(root):
    bridge_interfaces = root.find('bridge_interfaces')
    return bridge_interfaces

def parse_qos(root):
    qos_policies = root.find('qos')
    return qos_policies

def fetch_default_dns():
    tree = ET.parse(BASE_CONFIG_FILE)
    root = tree.getroot()
        
    option = root.find('dns_dhcp_options')
    address = option.find('value').text    
    return address

def fetch_bi_standard_ingress():
    tree = ET.parse(BASE_CONFIG_FILE)
    root = tree.getroot()
        
    policies = root.find('ingressPolicies')
    
    for policy in policies:
        #print policy.attrib['name']
        if policy.attrib['name'] == "BI-Standard":
            return policy

def fetch_bi_stateful_ingress():
    tree = ET.parse(BASE_CONFIG_FILE)
    root = tree.getroot()
        
    policies = root.find('ingressPolicies')
    for policy in policies:
        #print policy.attrib['name']
        if policy.attrib['name'] == "BI-Stateful":
            return policy
    
def fetch_bi_stateful_egress():
    tree = ET.parse(BASE_CONFIG_FILE)
    root = tree.getroot()
        
    policies = root.find('egressPolicies')
    for policy in policies:
        #print policy.attrib['name']
        if policy.attrib['name'] == "BI-Stateful":
            return policy

def fetch_l3_stateful_ingress():
    tree = ET.parse(BASE_CONFIG_FILE)
    root = tree.getroot()
        
    policies = root.find('ingressPolicies')
    for policy in policies:
        #print policy.attrib['name']
        if policy.attrib['name'] == "L3-Stateful":
            return policy

def fetch_l3_stateful_egress():
    tree = ET.parse(BASE_CONFIG_FILE)
    root = tree.getroot()
        
    policies = root.find('egressPolicies')
    for policy in policies:
        #print policy.attrib['name']
        if policy.attrib['name'] == "L3-Stateful":
            return policy
    
def fetch_spoke_ingress():
    tree = ET.parse(BASE_CONFIG_FILE)
    root = tree.getroot()
        
    policies = root.find('ingressPolicies')
    for policy in policies:
        #print policy.attrib['name']
        if policy.attrib['name'] == "L3-Hub/Spoke":
            return policy
#Fetch enterprise based on its name; create the enterprise if it does not exist yet
def fetch_or_create_enterprise(name, profile_name, local_as):
    """This function searches all currently created enterprises for an enterprise matching the passed name. If the enterprise
    is found it is returned, otherwise a new enterprise is created with the name and AS and returned.
    
    :param name: The name of the enterprise
    :type name: str
    
    :param profile_name: The name of the enterprise profile used as a template to create a new enterprise
    :type profile_name: str
    
    :param local_as: The local AS of the enterprise
    :type local_as: int
    
    :returns: enterprise - The enterprise object found or created
    
    """
    logger = logging.getLogger('create_service')
    logger.info('Searching for enterprise object "%s"' %name)
    enterprise_predicate = 'name beginswith "%s"' %name
    enterprises = vspk_list.list_enterprises(enterprise_predicate)
    
    enterprise = None
    for ent in enterprises:
        if ent.name.strip() == name.strip():
            enterprise = ent
            logger.info('Enterprise "%s" found' %name)
            break
    
    #If enterprise still none, must not have found it in created enterprises, create it
    if enterprise is None:
        logger.info('Enterprise not found, creating new enterprise')        
        enterprise = create.create_enterprise(name = name, description = None, profile = profile_name, local_as = local_as)
        
    return enterprise

def fetch_or_create_nsg(enterprise, nsg_name, template, location, zfb_match_value):
    """This function searches all NSG objects created under the specified enterprise, the nsgs searched for may be filtered
    using the nsg_name parameter. If the nsg is not found a new NSG object is created. 
    
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
    logger = logging.getLogger('create_service')
    logger.info('Searching for NSG object "%s"' %nsg_name)
    
    nsg_predicate = 'name == "%s"' % nsg_name
    #nsgs = list_nsg(session = session, parent_enterprise = enterprise, nsg_prefix = nsg_name)
    nsgs = vspk_list.list_nsgs(predicate = nsg_predicate, enterprise = enterprise)
    
    nsg = None
    for n in nsgs:
        if n.name == nsg_name:
            nsg = n
            logger.info('NSG "%s" found' %name)
            break
    
    #If nsg still not must not have found it, create it instead
    if nsg is None:
        logger.info('NSG not found, creating new NSG')        
        tree = ET.parse(BASE_CONFIG_FILE)
        root = tree.getroot()
        egress_qos_name = root.find('EgressQOSPolicyName').text
        #nsg = create_ns_gateway_interactive(session = session, name_prefix = nsg_name, 
        #                                    template_id = template, enterprise = enterprise, location = location, 
        #                                    egress_qos_name = egress_qos_name, zfb_match_attribute = ZFB_MATCH_ATTRIBUTE, 
        #                                    zfb_match_value = zfb_match_value)
        #create_bootstrap(nsg= nsg, zfb_match_attribute = ZFB_MATCH_ATTRIBUTE, zfb_match_value = zfb_match_value)
        nsg = create.create_nsg(enterprise = enterprise, name = nsg_name, description = None, 
                                template_name = template, location = location, egress_qos_name = egress_qos_name, 
                                zfb_match_attribute = ZFB_MATCH_ATTRIBUTE, zfb_match_value = zfb_match_value)
        
    return nsg

    
def fetch_or_create_service_template(enterprise, name):
    service_template = None
    
    predicate = 'name == "%s"' % name
    
    #templates = list_domain_template_interactive(session = session, parent_enterprise=enterprise, template_prefix=name,
    #                                             to_return=True)
    
    logger = logging.getLogger('create_service')
    logger.info('Searching for service template "%s" (fetch_or_create_service_template)' %name)
    
    templates = vspk_list.list_domain_templates(enterprise = enterprise, predicate = predicate)
    
    if templates is None or len(templates) == 0:
        #Basic template note found, create it
        logger.info('Service template not found - creating')
        service_template = create_domain_template_from_config(enterprise, name)
    else:
        logger.info('Service template found')
        service_template = templates[0]
        
    return service_template
    
#Create domain template from config file (File must be in same folder as this script)
def create_domain_template_from_config(enterprise, to_return):
    logger = logging.getLogger('create_service')
    logger.info('Creating domain template from base config file (create_domain_template_from_config)')
    
    #Read xml file and begin parsing tree
    tree = ET.parse(BASE_CONFIG_FILE)
    root = tree.getroot()
    template_to_return = None
    
    
    service_templates = root.find('service_templates')    
    for template in service_templates:
        name = unicode(template.find('name').text)
        description = unicode(template.find('description').text)
        encryption = unicode(template.find('encryption').text)
        multicast = unicode(template.find('multicast').text)
        scope = unicode(template.find('scope').text)
        
        #service_template = create_domain_template_interactive(parent_enterprise = enterprise, 
        #                                              template_name= name, description = description, session = session,
        #                                              encryption = encryption, multicast = multicast, scope = scope)
        logger.info('Creating domain template')
        service_template = create.create_domain_template(enterprise = enterprise, template_name = name, 
                                                         description = description, encryption = encryption, 
                                                         multicast = multicast, scope = scope)
        
        #print name + "   " + description + "    " + encryption + "   " + multicast + "\t" + scope
        if name == to_return:
            template_to_return = service_template
        
        logger.info('Creating zone template')
        #Create zone templates
        zones = template.find('zones')
        for zone in zones:
            name = unicode(zone.find('name').text)
            description = unicode(zone.find('description').text)
            encryption = unicode(zone.find('encryption').text)
            multicast = unicode(zone.find('multicast').text)
            public = unicode(zone.find('public').text)
            
            if public[0].upper() == 'T':
                public = True
            else:
                public = False
            
            
            #zone = create_zone_template(session = session, name=name, description=description, encryption=encryption, multicast=multicast, 
            #                            public=public, domain_template = service_template)
            
            zone = create.create_zone_template(domain_template = service_template, name = name, 
                                               description = description, encryption=encryption, 
                                               multicast = multicast, public = public)
        
        logger.info('Creating service template default policies')
        #Create Ingress Policies
        ingress_policies = template.find('ingress_policies')
        for policy in ingress_policies:
            name = unicode(policy.find('name').text)
            active = unicode(policy.find('active').text)
            allow_L2_spoof = unicode(policy.find('allowL2Spoof').text)
            default_allow_ip = unicode(policy.find('defaultAllowIP').text)
            default_allow_non_ip = unicode(policy.find('defaultAllowNonIP').text)
            priority_type = unicode(policy.find('priority_type').text)
            
            if active[0].upper() == 'T':
                active = True
            else:
                active = False
                
            if allow_L2_spoof[0].upper() == 'T':
                allow_L2_spoof = True
            else:
                allow_L2_spoof = False
            
            if default_allow_ip[0].upper() == 'T':
                default_allow_ip = True
            else:
                default_allow_ip = False
            
            if default_allow_non_ip[0].upper() == 'T':
                default_allow_non_ip = True
            else:
                default_allow_non_ip = False            
            
            #ingress_template = create_ingress_policy_template(session = session, domain_template = service_template, 
            #                                                  name = name, active=active, allow_l2_spoof = allow_L2_spoof,
            #                                                  default_allow_IP = default_allow_ip, 
            #                                                  default_allow_non_IP = default_allow_non_ip, priority_type = priority_type)
            logger.info('Creating ingress policy')
            ingress_template = create.create_ingress_policy_template(domain_template = service_template, name = name, 
                                                                     active = active, allow_l2_spoof = allow_L2_spoof, 
                                                                     default_allow_IP = default_allow_ip, 
                                                                     default_allow_non_IP = default_allow_non_ip, 
                                                                     priority_type = priority_type, priority = None)
            logger.info('Creating ingress policy entry')
            entries = policy.find('entries')
            for entry in entries:
                description = unicode(entry.find('description').text)
                location = unicode(entry.find('location').text)
                network_type = unicode(entry.find('networkType').text)
                protocol = unicode(entry.find('protocol').text)
                action = unicode(entry.find('action').text)
                etherType = unicode(entry.find('etherType').text)
                DSCP = unicode(entry.find('DSCP').text)
                priority = unicode(entry.find('priority').text)
                source_port = unicode(entry.find('sourcePort').text)
                destination_port = unicode(entry.find('destinationPort').text)
                

                #create_ingress_policy_template_entry(ingress_template = ingress_template, description = description, location=location, network_type = network_type, protocol = protocol,
                #                          action = action, etherType = etherType, DSCP = DSCP, priority = priority)
                create.create_ingress_policy_entry(ingress_template = ingress_template, description = description, location=location, network_type = network_type, protocol = protocol,
                                                   action = action, etherType = etherType, DSCP = DSCP, priority = priority)
                
        logger.info('Creating egress template default policies')        
        #Create egress policies
        egress_policies = template.find('egress_policies')
        for policy in egress_policies:
            name = unicode(policy.find('name').text)
            active = unicode(policy.find('active').text)
            default_allow_ip = unicode(policy.find('defaultAllowIP').text)
            default_allow_non_ip = unicode(policy.find('defaultAllowNonIP').text)
            priority_type = unicode(policy.find('priority_type').text)
            default_install_implicit_rules = unicode(policy.find('defaultInstallACLImplicitRules').text)
            
            if active[0].upper() == 'T':
                active = True
            else:
                active = False
                
            if default_install_implicit_rules[0].upper() == 'T':
                default_install_implicit_rules = True
            else:
                default_install_implicit_rules = False
            
            if default_allow_ip[0].upper() == 'T':
                default_allow_ip = True
            else:
                default_allow_ip = False
            
            if default_allow_non_ip[0].upper() == 'T':
                default_allow_non_ip = True
            else:
                default_allow_non_ip = False
            
            #egress_template = create_egress_policy_template(session = session, domain_template = service_template, name = name, active = active, 
            #                                              default_allow_IP = default_allow_ip, default_allow_non_IP = default_allow_non_ip, 
            #                                              priority_type = priority_type, default_install_implicit_rules = default_install_implicit_rules)
            egress_template = create.create_egess_policy_template(domain_template = service_template, name = name, 
                                                                  active = active, default_allow_IP = default_allow_ip, 
                                                                  default_allow_non_IP = default_allow_non_ip, priority_type = priority_type, 
                                                                  default_install_implicit_rules = default_install_implicit_rules)
            logger.info('Creating egress template entry')
            entries = policy.find('entries')
            for entry in entries:
                description = unicode(entry.find('description').text)
                location = unicode(entry.find('location').text)
                network_type = unicode(entry.find('networkType').text)
                protocol = unicode(entry.find('protocol').text)
                action = unicode(entry.find('action').text)
                etherType = unicode(entry.find('etherType').text)
                DSCP = unicode(entry.find('DSCP').text)
                priority = unicode(entry.find('priority').text)
                source_port = unicode(entry.find('sourcePort').text)
                destination_port = unicode(entry.find('destinationPort').text)
                
                create.create_egress_policy_entry(egress_template = egress_template, description = description, 
                                                  location = location, network_type = network_type, protocol = protocol, action = action, 
                                                  etherType = etherType, DSCP = DSCP, priority = priority)
                
                #create_egress_policy_template_entry(session = session, egress_template = egress_template, description = description, 
                #                                    location = location, network_type = network_type, protocol = protocol, action = action, 
                #                                    etherType = etherType, DSCP = DSCP, priority = priority)
                
    return template_to_return

#Fetch zone if it exists, create and return otherwise
def fetch_or_create_zone(enterprise, domain, name, description, encryption, multicast, public):
    logger = logging.getLogger('create_service')
    logger.info('Fetching or creating zone (fetch_or_create_zone)')
    
    zone_predicate = 'name == "%s"' % name 
    #zones = list_zones(parent_enterprise = enterprise, zone_prefix = name, session = session, parent_domain = domain)
    zones = vspk_list.list_zones(domain, zone_predicate)
    zone = None
    
    if len(zones) == 1:
        zone = zones[0]
        logger.info('Zone "%s" found' %name)
    else:
        '''
        zone = create_zone(parent_enterprise = enterprise, 
                           zone_name = name, 
                           zone_description = description, 
                           zone_encryption = encryption, 
                           zone_multicast = multicast, 
                           zone_public = public, 
                           domain = domain)
                           
        '''
        logger.info('Zone "%s" not found, creating new zone' % name)
        zone = create.create_zone(name = name, description = description, 
                                  encryption = encryption, multicast = multicast, 
                                  public = public, domain = domain)
    return zone

#Fetch subnet if it exists, otherwise create it
def fetch_or_create_subnet(zone, name, network, mask, encryption, pat_enabled, underlay_enabled, dns_values):
    logger = logging.getLogger('create_service')
    logger.info('Fetching or creating subnet (fetch_or_create_subnet)')
    
    subnet_predicate = 'name == "%s"' %name
    #subnets = list_subnet(session = session, zone = zone, subnet_prefix = name)
    subnets = vspk_list.list_subnet(predicate = subnet_predicate, zone = zone)
    subnet = None
    
    if len(subnets) == 1:
        logger.info('Subnet "%s" found' % name)
        subnet = subnets[0]
        #print 'Found ' + str(subnet.name)

    else:
        #print 'Attempting to create:'
        logger.info('Subnet "%s" not found - creating' % name)
        '''     
        subnet = create_subnets_interactive(subnet_name = name, 
                               network = network, zone = zone, session = session,
                               mask = mask, encryption = encryption, pat_enable = pat_enabled, underlay_enabled = underlay_enabled, 
                               dns_values = dns_values)    
        '''
        subnet=create.create_subnets(zone = zone, name = name, encryption = encryption, 
                                     pat_enable = pat_enabled, underlay_enabled = underlay_enabled, dns_values = dns_values, 
                                     network = network, mask = mask)
        
        #print subnet
        #print ''
        #create_dhcp_range(subnet, network, mask)
        create.create_dhcp_range(subnet, network, mask)
        
    return subnet

def fetch_or_create_vports(nsg, subnet, port, vlan, vport_name, enterprise):
    
    tree = ET.parse(BASE_CONFIG_FILE)
    root = tree.getroot()
    
    #vports = list_vports(subnet = subnet, vport_prefix = vport_name, session = session)
    vport_predicate = 'name == "%s"' % vport_name
    vports = vspk_list.list_vports(predicate = vport_predicate, subnet = subnet)
    egress_qos_name = root.find('EgressQOSPolicyName').text
        
    if len(vports) == 1:
        vport = vports[0]
    else:
        port = "port" + port
        '''
        vport = create_bridge_vport_per_vlan_interactive(nsg = subnet_nsg,
                                                     subnet = subnet,
                                                     vlan = vport_vlan,
                                                     vport_name = vport_name,
                                                     port =  port, 
                                                     parent_enterprise = enterprise,
                                                     egress_qos_name = egress_qos_name, 
                                                     session = session)
        '''
        vport = create.create_vport(nsg = nsg, port = port, subnet = subnet, vlan = vlan, vport_name = vport_name)
    return vport

def fetch_create_bridge_interface(vport, bridge_interface_name):
    logger = logging.getLogger('create_service')
    logger.info('Running fetch or create bridge intrface')
    
    bridge_interface_predicate = 'name == "%s"' % bridge_interface_name
    #bridge_interfaces = list_bridge_interface( session = session, vport = vport, bridge_interface_prefix = bridge_interface_name)
    bridge_interfaces = vspk_list.list_bridge_interfaces(predicate = bridge_interface_predicate, vport = vport)
    
    bridge_interface = None
    if len(bridge_interfaces) == 0:
        logger.info('Bridge interface not found - creating')
        #bridge_interface = create_bridge_interface(vport = vport, bridge_interface_name = bridge_interface_name)
        bridge_interface = create.create_bridge_interface(vport = vport, bridge_interface_name = bridge_interface_name)
    else:
        logger.info('Bridge info found')
        bridge_interface = bridge_interfaces[0]
    
    return bridge_interface

def fetch_or_create_zfb(enterprise, name, values):  
    logger = logging.getLogger('create_service')
    
    predicate = 'name beginswith "%s"' % name
    #zfbs = list_enterprise_auto_assignments(zfb_prefix = name, session = session)
    zfbs = vspk_list.list_enterprise_auto_assignments(predicate=predicate)
       
    if len(zfbs) == 0:
        logger.info('ZFB entry not found; creating now ZFB entry')
        #zfb = create_enterprise_auto_assignments(zfb_name_prefix = name, match_attribute = ZFB_MATCH_ATTRIBUTE,
        #                       match_values = values, enterprise = enterprise, session = session)
        zfb = create.create_enterprise_auto_assignment(name = name, match_attribute = ZFB_MATCH_ATTRIBUTE, 
                                                       match_values = values, enterprise = enterprise)
    else:
        logger.info('ZFB entry found; appending values to entry if not currently present')
        zfb = zfbs[0]
        #update_zfb_values(zfb,values)
        update_zfb_values(zfb,values)
    return zfb
    
#return NSG, must have been created before
def fetch_nsg(enterprise, nsg_prefix):
    #nsgs = list_nsg(session = session, parent_enterprise = enterprise, nsg_prefix = nsg_prefix)  
    #print 'Prefix used: ' + nsg_prefix
    #print 'Returned; ' + nsgs[0].name
    #print 'Num Entries: ' + str(len(nsgs))
    #print ''
    
    logger = logging.getLogger('create_service')
    logger.info('Fetching previously created NSG')
    
    nsg_predicate = 'name == "%s"' % nsg_prefix
    nsgs =vspk_list.list_nsgs(predicate = nsg_predicate, enterprise = enterprise)
    
    return nsgs[0]
    
####################### CREATE SERVICES

def create_bi(enterprise, service_template, name, description = None):
    #Check if domain exists, if exists return it, otherwise create new domain
    logger = logging.getLogger('create_service')
    
    logger.info('Fetching domains where name begins with "%s"' %name)
    #domains = list_domain_interactive(parent_enterprise = enterprise, domain_prefix=name, session = session)
    predicate = 'name beginswith "%s"' % name
    domains = vspk_list.list_domains(enterprise = enterprise, predicate = predicate)
    domain = None
    
    if len(domains) == 1:
        logger.info('Domain found')
        domain = domains[0]
    else:
        logger.info('Specified domain not found, creating')
        #domain = create_domain_service_deployment(enterprise = enterprise, template = service_template, name = name, description = description, 
        #                                          encryption = BI_ENCRYPTION, pat_enabled = BI_PATEnabled, 
        #                                          underlay_enabled = BI_UNDERLAYENABLED)
        domain = create.create_domain(enterprise = enterprise, template = service_template, name = name, description = description, 
                                      encryption = BI_ENCRYPTION, pat_enabled = BI_PATEnabled, 
                                      underlay_enabled = BI_UNDERLAYENABLED)
        #create_bi_standard_acl(domain)
    
    return domain

def create_bi_acl(enterprise, service_template, name, description = None):
    #@domains = list_domain_interactive(parent_enterprise = enterprise, domain_prefix=name, session = session)
    logger = logging.getLogger('create_service')
    
    logger.info('Fetching domains where name begins with "%s" (create_bi_acl))' %name)
    #domains = list_domain_interactive(parent_enterprise = enterprise, domain_prefix=name, session = session)
    predicate = 'name beginswith "%s"' % name
    domains = vspk_list.list_domains(enterprise = enterprise, predicate = predicate)
    domain = None
        
    if len(domains) == 1:
        logger.info('Domain found')
        domain = domains[0]
    else:
        logger.info('Domain not found - creating')
        #domain = create_domain_service_deployment(enterprise = enterprise, template = service_template, name = name, description = description, 
        #                                          encryption = BI_ENCRYPTION, pat_enabled = BI_PATEnabled, 
        #                                          underlay_enabled = BI_UNDERLAYENABLED)
        #create_bi_standard_acl(domain)
        domain = create.create_domain(enterprise = enterprise, template = service_template, name = name, description = description, 
                              encryption = BI_ENCRYPTION, pat_enabled = BI_PATEnabled, 
                              underlay_enabled = BI_UNDERLAYENABLED)
    return domain

def create_l3(enterprise, service_template, name, description = None):
    #domains = list_domain_interactive(parent_enterprise = enterprise, domain_prefix=name, session = session)
    logger = logging.getLogger('create_service')
    
    logger.info('Fetching domains where name begins with "%s" (create_l3))' %name)
    predicate = 'name beginswith "%s"' % name
    domains = vspk_list.list_domains(enterprise = enterprise, predicate = predicate)
    
    domain = None
        
    if len(domains) == 1:
        logger.info('Specified domain found')
        domain = domains[0]
    else:
        logger.info('Specified domain not found - creating')
        #domain = create_domain_service_deployment(enterprise = enterprise, template = service_template, name = name, description = description, 
        #                                          encryption = L3_ENCRYPTION, pat_enabled = L3_PATEnabled, 
        #                                          underlay_enabled = L3_UNDERLAYENABLED)
        domain = create.create_domain(enterprise = enterprise, template = service_template, name = name, description = description, 
                              encryption = L3_ENCRYPTION, pat_enabled = L3_PATEnabled, 
                              underlay_enabled = L3_UNDERLAYENABLED)
    return domain

def create_l3_bi(enterprise, service_template, name, description = None):
    #domains = list_domain_interactive(parent_enterprise = enterprise, domain_prefix=name, session = session)
    
    logger = logging.getLogger('create_service')
    
    logger.info('Fetching domains where name begins with "%s" (create_l3_bi))' %name)
    predicate = 'name beginswith "%s"' % name
    domains = vspk_list.list_domains(enterprise = enterprise, predicate = predicate)
    
    domain = None
        
    if len(domains) == 1:
        logger.info('Specifed domain found')
        domain = domains[0]
    else:
        logger.info('Specified domain not found - creating')
        #domain = create_domain_service_deployment(enterprise = enterprise, template = service_template, name = name, description = description, 
        #                                         encryption = L3_BI_ENCRYPTION, pat_enabled = L3_BI_PATEnabled, 
        #                                          underlay_enabled = L3_BI_UNDERLAYENABLED)
        domain = create.create_domain(enterprise = enterprise, template = service_template, name = name, description = description, 
                              encryption = L3_BI_ENCRYPTION, pat_enabled = L3_BI_PATEnabled, 
                              underlay_enabled = L3_BI_UNDERLAYENABLED)
    return domain

def create_l3_bi_acl(enterprise, service_template, name, description = None):
    #domains = list_domain_interactive(parent_enterprise = enterprise, domain_prefix=name, session = session)
    
    logger = logging.getLogger('create_service')
    
    logger.info('Fetching domains where name begins with "%s" (create_l3_bi_acl))' %name)
    predicate = 'name beginswith "%s"' % name
    domains = vspk_list.list_domains(enterprise = enterprise, predicate = predicate)
    
    domain = None
        
    if len(domains) == 1:
        logger.info('Specified domain found')
        domain = domains[0]
    else:    
        logger.info('Specified domain not found - creating')
        #domain = create_domain_service_deployment(enterprise = enterprise, template = service_template, name = name, description = description, 
        #                                          encryption = L3_ENCRYPTION, pat_enabled = L3_PATEnabled, 
        #                                          underlay_enabled = L3_UNDERLAYENABLED)
        domain = create.create_domain(enterprise = enterprise, template = service_template, name = name, description = description, 
                      encryption = L3_ENCRYPTION, pat_enabled = L3_PATEnabled, 
                      underlay_enabled = L3_UNDERLAYENABLED)
    return domain


##############################################
def create_bi_policies(enterprise, domain, zone):
    logger = logging.getLogger('create_service')
    logger.info('Creating BI policies (create_bi_policies)')
    
    policy = fetch_bi_standard_ingress()
    name = unicode(policy.find('name').text)
    active = unicode(policy.find('active').text)
    allow_L2_spoof = unicode(policy.find('allowL2Spoof').text)
    default_allow_ip = unicode(policy.find('defaultAllowIP').text)
    default_allow_non_ip = unicode(policy.find('defaultAllowNonIP').text)
    priority = unicode(policy.find('priority').text)
    
    if active[0].upper() == 'T':
        active = True
    else:
        active = False
        
    if allow_L2_spoof[0].upper() == 'T':
        allow_L2_spoof = True
    else:
        allow_L2_spoof = False
    
    if default_allow_ip[0].upper() == 'T':
        default_allow_ip = True
    else:
        default_allow_ip = False
    
    if default_allow_non_ip[0].upper() == 'T':
        default_allow_non_ip = True
    else:
        default_allow_non_ip = False            
    
    
    #policies = list_ingress_policy(policy_prefix = name, domain = domain, session = session)
    policy_predicate = 'name beginswith "%s"' % name
    policies = vspk_list.list_ingress_policies(predicate = policy_predicate, domain = domain)
    in_policy = None
    if len(policies) == 1:
        logging.info('BI ingress policy found')
        in_policy = policies[0]
    else:
        logging.info('BI ingress policy not found - creating')    
        '''
        in_policy = create_ingress_policy_template(session = session, domain_template = domain, 
                                                name = name, active=active, allow_l2_spoof = allow_L2_spoof,
                                                default_allow_IP = default_allow_ip, 
                                                default_allow_non_IP = default_allow_non_ip, priority = priority)
        '''
        in_policy = create.create_ingress_policy_template(domain_template = domain, name = name, active = active, 
                                                          allow_l2_spoof = allow_L2_spoof, default_allow_IP = default_allow_ip, 
                                                          default_allow_non_IP = default_allow_non_ip, priority = priority)
        entries = policy.find('entries')
        for entry in entries:
            description = unicode(entry.find('description').text)
            location = unicode(entry.find('location').text)
            network_type = unicode(entry.find('networkType').text)
            protocol = unicode(entry.find('protocol').text)
            action = unicode(entry.find('action').text)
            etherType = unicode(entry.find('etherType').text)
            DSCP = unicode(entry.find('DSCP').text)
            priority = unicode(entry.find('priority').text)
            source_port = unicode(entry.find('sourcePort').text)
            destination_port = unicode(entry.find('destinationPort').text)
            location_id = zone.id
    
            #create_ingress_policy_template_entry(ingress_template = in_policy, description = description, location=location, network_type = network_type, protocol = protocol,
            #                          action = action, etherType = etherType, DSCP = DSCP, priority = priority, location_id = location_id)
            
            create.create_ingress_policy_entry(ingress_template = in_policy, description = description, location=location, network_type = network_type, protocol = protocol,
                                               action = action, etherType = etherType, DSCP = DSCP, priority = priority, location_id = location_id)
            
def create_bi_acl_policies(enterprise, domain, zone):    
    
    logger = logging.getLogger('create_service')
    logger.info('Creating BI policies (create_bi_acl_policies)')
    
    #Same policies as BI with additional reflexive policies
    create_bi_policies(enterprise, domain, zone)
    policy = fetch_bi_stateful_ingress()
    
    name = unicode(policy.find('name').text)
    active = unicode(policy.find('active').text)
    allow_L2_spoof = unicode(policy.find('allowL2Spoof').text)
    default_allow_ip = unicode(policy.find('defaultAllowIP').text)
    default_allow_non_ip = unicode(policy.find('defaultAllowNonIP').text)
    priority = unicode(policy.find('priority').text)
    
    if active[0].upper() == 'T':
        active = True
    else:
        active = False
        
    if allow_L2_spoof[0].upper() == 'T':
        allow_L2_spoof = True
    else:
        allow_L2_spoof = False
    
    if default_allow_ip[0].upper() == 'T':
        default_allow_ip = True
    else:
        default_allow_ip = False
    
    if default_allow_non_ip[0].upper() == 'T':
        default_allow_non_ip = True
    else:
        default_allow_non_ip = False            
        
    #policies = list_ingress_policy(policy_prefix = name, domain = domain, session = session)
    policy_predicate = 'name beginswith "%s"' % name
    policies = vspk_list.list_ingress_policies(predicate = policy_predicate, domain = domain)
    in_policy = None
    if len(policies) == 1:
        logger.info('Specified ingress policy found')
        in_policy = policies[0]
    else:
        logger.info('Specified ingress policy not found - creating policy and entries')
        #in_policy = create_ingress_policy_template(session = session, domain_template = domain, 
        #                                        name = name, active=active, allow_l2_spoof = allow_L2_spoof,
        #                                        default_allow_IP = default_allow_ip, 
        #                                        default_allow_non_IP = default_allow_non_ip, priority = priority)
        in_policy = create.create_ingress_policy_template(domain_template = domain, name = name, active = active, 
                                                          allow_l2_spoof = allow_L2_spoof, default_allow_IP = default_allow_ip, 
                                                          default_allow_non_IP = default_allow_non_ip, priority = priority)        
        entries = policy.find('entries')
        for entry in entries:
            description = unicode(entry.find('description').text)
            location = unicode(entry.find('location').text)
            network_type = unicode(entry.find('networkType').text)
            protocol = unicode(entry.find('protocol').text)
            action = unicode(entry.find('action').text)
            etherType = unicode(entry.find('etherType').text)
            DSCP = unicode(entry.find('DSCP').text)
            priority = unicode(entry.find('priority').text)
            source_port = unicode(entry.find('sourcePort').text)
            destination_port = unicode(entry.find('destinationPort').text)
            stateful = unicode(entry.find('stateful'))
            stats_logging = unicode(entry.find('statsLoggingEnabled'))
            flow_logging = unicode(entry.find('flowLoggingEnabled'))
                
            if stateful[0].upper() == 'T':
                stateful = True
            else:
                stateful = False

            if stats_logging[0].upper() == 'T':
                stats_logging = True
            else:
                stats_logging = False            

            if flow_logging[0].upper() == 'T':
                flow_logging = True
            else:
                flow_logging = False  
            
            #create_ingress_policy_template_entry(ingress_template = in_policy, description = description, location=location, network_type = network_type, protocol = protocol,
            #                          action = action, etherType = etherType, DSCP = DSCP, priority = priority, stateful = stateful,
            #                          stats_logging = stats_logging, flow_logging = flow_logging)
            create.create_ingress_policy_entry(ingress_template = in_policy, description = description, location=location, network_type = network_type, protocol = protocol,
                                               action = action, etherType = etherType, DSCP = DSCP, priority = priority, stateful = stateful,
                                               stats_logging = stats_logging, flow_logging = flow_logging)
        
    #Create Egress policies (Not used in standard BI)
    policy = fetch_bi_stateful_egress()
    
    name = unicode(policy.find('name').text)
    active = unicode(policy.find('active').text)
    default_allow_ip = unicode(policy.find('defaultAllowIP').text)
    default_allow_non_ip = unicode(policy.find('defaultAllowNonIP').text)
    priority = unicode(policy.find('priority').text)
    default_install_implicit_rules = unicode(policy.find('defaultInstallACLImplicitRules').text)
    
    if active[0].upper() == 'T':
        active = True
    else:
        active = False
        
    if default_install_implicit_rules[0].upper() == 'T':
        default_install_implicit_rules = True
    else:
        default_install_implicit_rules = False
    
    if default_allow_ip[0].upper() == 'T':
        default_allow_ip = True
    else:
        default_allow_ip = False
    
    if default_allow_non_ip[0].upper() == 'T':
        default_allow_non_ip = True
    else:
        default_allow_non_ip = False
    
    egress_policy_predicate = 'name beginswith "%s"' % name
    #policies = list_egress_policy(policy_prefix = name, domain = domain, session = session)
    policies = vspk_list.list_egress_policies(predicate = egress_policy_predicate, domain = domain)
    egress_template = None
    if len(policies) == 1:
        logger.info('Specified egress policy found')
        egress_template = policies[0]
    else:    
        logger.info('Specified egress policy not found - Creating policy and ACL entries')
        
        #egress_template = create_egress_policy_template(session = session, domain_template = domain, name = name, active = active, 
        #                                              default_allow_IP = default_allow_ip, default_allow_non_IP = default_allow_non_ip, 
        #                                              priority = priority, default_install_implicit_rules = default_install_implicit_rules)
        
        egress_template = create.create_egess_policy_template(domain_template = domain, name = name, 
                                                              active = active, default_allow_IP = default_allow_ip, 
                                                              default_allow_non_IP = default_allow_non_ip, priority = priority, 
                                                              default_install_implicit_rules = default_install_implicit_rules)        
        
        entries = policy.find('entries')
        for entry in entries:
            description = unicode(entry.find('description').text)
            location = unicode(entry.find('location').text)
            network_type = unicode(entry.find('networkType').text)
            protocol = unicode(entry.find('protocol').text)
            action = unicode(entry.find('action').text)
            etherType = unicode(entry.find('etherType').text)
            DSCP = unicode(entry.find('DSCP').text)
            priority = unicode(entry.find('priority').text)
            source_port = unicode(entry.find('sourcePort').text)
            destination_port = unicode(entry.find('destinationPort').text)
            
            #create_egress_policy_template_entry(session = session, egress_template = egress_template, description = description, 
            #                                    location = location, network_type = network_type, protocol = protocol, action = action, 
            #                                    etherType = etherType, DSCP = DSCP, priority = priority)
            create.create_egress_policy_entry(egress_template = egress_template, description = description, location = location, 
                                              network_type = network_type, protocol = protocol, action = action, 
                                              etherType = etherType, DSCP = DSCP, priority = priority)

def create_l3_policies(enterprise, domain, zone):
    #No L3 policies to create
    logger = logging.getLogger('create_service')
    logger.info('Creating L3 policies - No ACL policies for L3 (create_l3_policies)')

#BI+L# policies are a combination of BI and L# policies
def create_l3_bi_policies(enterprise, domain, zone):
    #create_bi_policies(enterprise, domain, zone)
    logger = logging.getLogger('create_service')
    logger.info('Creating L3+BI policies (create_l3_bi_policies)')
    create_l3_policies(enterprise, domain, zone)

def create_l3_bi_acl_policies(enterprise,domain, zone):
    logger = logging.getLogger('create_service')
    logger.info('Creating L3+BI_ACL policies (create_l3_bi_acl_policies)')    
    
    policy = fetch_l3_stateful_ingress()
    
    name = unicode(policy.find('name').text)
    active = unicode(policy.find('active').text)
    allow_L2_spoof = unicode(policy.find('allowL2Spoof').text)
    default_allow_ip = unicode(policy.find('defaultAllowIP').text)
    default_allow_non_ip = unicode(policy.find('defaultAllowNonIP').text)
    priority = unicode(policy.find('priority').text)
    
    if active[0].upper() == 'T':
        active = True
    else:
        active = False
        
    if allow_L2_spoof[0].upper() == 'T':
        allow_L2_spoof = True
    else:
        allow_L2_spoof = False
    
    if default_allow_ip[0].upper() == 'T':
        default_allow_ip = True
    else:
        default_allow_ip = False
    
    if default_allow_non_ip[0].upper() == 'T':
        default_allow_non_ip = True
    else:
        default_allow_non_ip = False            
        
    #policies = list_ingress_policy(policy_prefix = name, domain = domain, session = session)
    policy_predicate = 'name beginswith "%s"' % name
    policies = vspk_list.list_ingress_policies(predicate = policy_predicate, domain = domain)
    in_policy = None
    if len(policies) == 1:
        logger.info('Specified policy found')
        in_policy = policies[0]
    else:
        logger.info('Specified policy not found - creating')
        #in_policy = create_ingress_policy_template(session = session, domain_template = domain, 
        #                                        name = name, active=active, allow_l2_spoof = allow_L2_spoof,
        #                                        default_allow_IP = default_allow_ip, 
        #                                        default_allow_non_IP = default_allow_non_ip, priority = priority)
        in_policy = create.create_ingress_policy_template(domain_template = domain, name = name, active = active, 
                                                          allow_l2_spoof = allow_L2_spoof, default_allow_IP = default_allow_ip, 
                                                          default_allow_non_IP = default_allow_non_ip, priority = priority)        
        
        
        entries = policy.find('entries')
        for entry in entries:
            description = unicode(entry.find('description').text)
            location = unicode(entry.find('location').text)
            network_type = unicode(entry.find('networkType').text)
            protocol = unicode(entry.find('protocol').text)
            action = unicode(entry.find('action').text)
            etherType = unicode(entry.find('etherType').text)
            DSCP = unicode(entry.find('DSCP').text)
            priority = unicode(entry.find('priority').text)
            source_port = unicode(entry.find('sourcePort').text)
            destination_port = unicode(entry.find('destinationPort').text)
            stateful = unicode(entry.find('stateful'))
            stats_logging = unicode(entry.find('statsLoggingEnabled'))
            flow_logging = unicode(entry.find('flowLoggingEnabled'))
                
            if stateful[0].upper() == 'T':
                stateful = True
            else:
                stateful = False

            if stats_logging[0].upper() == 'T':
                stats_logging = True
            else:
                stats_logging = False            

            if flow_logging[0].upper() == 'T':
                flow_logging = True
            else:
                flow_logging = False  
            
            #create_ingress_policy_template_entry(ingress_template = in_policy, description = description, location=location, network_type = network_type, protocol = protocol,
            #                          action = action, etherType = etherType, DSCP = DSCP, priority = priority, stateful = stateful,
            #                          stats_logging = stats_logging, flow_logging = flow_logging)
    
            create.create_ingress_policy_entry(ingress_template = in_policy, description = description, location=location, network_type = network_type, protocol = protocol,
                                               action = action, etherType = etherType, DSCP = DSCP, priority = priority, stateful = stateful,
                                               stats_logging = stats_logging, flow_logging = flow_logging)
    
    #Create Egress policies (Not used in standard BI)
    policy = fetch_l3_stateful_egress()
    
    name = unicode(policy.find('name').text)
    active = unicode(policy.find('active').text)
    default_allow_ip = unicode(policy.find('defaultAllowIP').text)
    default_allow_non_ip = unicode(policy.find('defaultAllowNonIP').text)
    priority = unicode(policy.find('priority').text)
    default_install_implicit_rules = unicode(policy.find('defaultInstallACLImplicitRules').text)
    
    if active[0].upper() == 'T':
        active = True
    else:
        active = False
        
    if default_install_implicit_rules[0].upper() == 'T':
        default_install_implicit_rules = True
    else:
        default_install_implicit_rules = False
    
    if default_allow_ip[0].upper() == 'T':
        default_allow_ip = True
    else:
        default_allow_ip = False
    
    if default_allow_non_ip[0].upper() == 'T':
        default_allow_non_ip = True
    else:
        default_allow_non_ip = False
    
    #policies = list_egress_policy(policy_prefix = name, domain = domain, session = session)
    egress_policy_predicate = 'name beginswith "%s"' % name
    policies = vspk_list.list_egress_policies(predicate = egress_policy_predicate, domain = domain)    
    egress_template = None
    if len(policies) == 1:
        logger.info('Specified egress policy found')
        egress_template = policies[0]
    else:
        logger.info('Specified egress policy not found - creating')
        #egress_template = create_egress_policy_template(session = session, domain_template = domain, name = name, active = active, 
        #                                              default_allow_IP = default_allow_ip, default_allow_non_IP = default_allow_non_ip, 
        #                                              priority = priority, default_install_implicit_rules = default_install_implicit_rules)
        
        egress_template = create.create_egess_policy_template(domain_template = domain, name = name, 
                                                              active = active, default_allow_IP = default_allow_ip, 
                                                              default_allow_non_IP = default_allow_non_ip, priority = priority, 
                                                              default_install_implicit_rules = default_install_implicit_rules)         
        
        entries = policy.find('entries')
        for entry in entries:
            description = unicode(entry.find('description').text)
            location = unicode(entry.find('location').text)
            network_type = unicode(entry.find('networkType').text)
            protocol = unicode(entry.find('protocol').text)
            action = unicode(entry.find('action').text)
            etherType = unicode(entry.find('etherType').text)
            DSCP = unicode(entry.find('DSCP').text)
            priority = unicode(entry.find('priority').text)
            source_port = unicode(entry.find('sourcePort').text)
            destination_port = unicode(entry.find('destinationPort').text)
            
            '''
            if location == 'ENDPOINT_DOMAIN':
                location_id = domain.id
            else:
                location_id = None
            '''    
            
            #create_egress_policy_template_entry(session = session, egress_template = egress_template, description = description, 
            #                                    location = location, network_type = network_type, protocol = protocol, action = action, 
            #                                    etherType = etherType, DSCP = DSCP, priority = priority)
            
            create.create_egress_policy_entry(egress_template = egress_template, description = description, location = location, 
                                  network_type = network_type, protocol = protocol, action = action, 
                                  etherType = etherType, DSCP = DSCP, priority = priority)
            
def create_spoke_policies(enterprise,domain, zone):
    logger = logging.getLogger('create_service')
    logger.info('Creating Spoke policies (create_l3_bi_acl_policies)') 
        
    policy = fetch_spoke_ingress()
    
    name = unicode(policy.find('name').text)
    active = unicode(policy.find('active').text)
    allow_L2_spoof = unicode(policy.find('allowL2Spoof').text)
    default_allow_ip = unicode(policy.find('defaultAllowIP').text)
    default_allow_non_ip = unicode(policy.find('defaultAllowNonIP').text)
    priority = unicode(policy.find('priority').text)
    
    if active[0].upper() == 'T':
        active = True
    else:
        active = False
        
    if allow_L2_spoof[0].upper() == 'T':
        allow_L2_spoof = True
    else:
        allow_L2_spoof = False
    
    if default_allow_ip[0].upper() == 'T':
        default_allow_ip = True
    else:
        default_allow_ip = False
    
    if default_allow_non_ip[0].upper() == 'T':
        default_allow_non_ip = True
    else:
        default_allow_non_ip = False            
    
    policy_predicate = 'name beginswith "%s"' % name
    policies = vspk_list.list_ingress_policies(predicate = policy_predicate, domain = domain)        
    #policies = list_ingress_policy(policy_prefix = name, domain = domain, session = session)
    in_policy = None
    if len(policies) == 1:
        logger.info('Specified spoke policy found')
        in_policy = policies[0]
    else:
        logger.info('Specified spoke policy not found - creating')
        #in_policy = create_ingress_policy_template(session = session, domain_template = domain, 
        #                                        name = name, active=active, allow_l2_spoof = allow_L2_spoof,
        #                                        default_allow_IP = default_allow_ip, 
        #                                        default_allow_non_IP = default_allow_non_ip, priority = priority)
        
        in_policy = create.create_ingress_policy_template(domain_template = domain, name = name, active = active, 
                                                          allow_l2_spoof = allow_L2_spoof, default_allow_IP = default_allow_ip, 
                                                          default_allow_non_IP = default_allow_non_ip, priority = priority)        
        
        entries = policy.find('entries')
        for entry in entries:
            description = unicode(entry.find('description').text)
            location = unicode(entry.find('location').text)
            network_type = unicode(entry.find('networkType').text)
            protocol = unicode(entry.find('protocol').text)
            action = unicode(entry.find('action').text)
            etherType = unicode(entry.find('etherType').text)
            DSCP = unicode(entry.find('DSCP').text)
            priority = unicode(entry.find('priority').text)
            source_port = unicode(entry.find('sourcePort').text)
            destination_port = unicode(entry.find('destinationPort').text)
            stateful = unicode(entry.find('stateful'))
            stats_logging = unicode(entry.find('statsLoggingEnabled'))
            flow_logging = unicode(entry.find('flowLoggingEnabled'))
            location_id = zone.id
                
            if stateful[0].upper() == 'T':
                stateful = True
            else:
                stateful = False

            if stats_logging[0].upper() == 'T':
                stats_logging = True
            else:
                stats_logging = False            

            if flow_logging[0].upper() == 'T':
                flow_logging = True
            else:
                flow_logging = False  
            
            #create_ingress_policy_template_entry(ingress_template = in_policy, description = description, location=location, network_type = network_type, protocol = protocol,
            #                          action = action, etherType = etherType, DSCP = DSCP, priority = priority, stateful = stateful,
            #                          stats_logging = stats_logging, flow_logging = flow_logging, location_id = location_id)  
            create.create_ingress_policy_entry(ingress_template = in_policy, description = description, location=location, network_type = network_type, protocol = protocol,
                                               action = action, etherType = etherType, DSCP = DSCP, priority = priority, stateful = stateful,
                                               stats_logging = stats_logging, flow_logging = flow_logging, location_id = location_id)                  

def fetch_or_create_domain_qos_policy(domain, name, description, trust, forwarding_class, active):
    logger = logging.getLogger('create_service')
    logger.info('Creating domain QoS policy') 
        
    predicate = 'name beginswith "%s"' % name
    
    policies = vspk_list.list_domain_qos_policies(predicate=predicate, domain = domain)
       
    if len(policies) == 0:
        logger.info('QoD entry not found; creating now domain QoS entry')
        #zfb = create_enterprise_auto_assignments(zfb_name_prefix = name, match_attribute = ZFB_MATCH_ATTRIBUTE,
        #                       match_values = values, enterprise = enterprise, session = session)
        #zfb = create.create_enterprise_auto_assignment(name = name, match_attribute = ZFB_MATCH_ATTRIBUTE, 
        #                                               match_values = values, enterprise = enterprise)
        policy = create.create_domain_qos(domain, name, description, trust, forwarding_class, active)
        
        
    else:
        logger.info('QoS entry found')
        policy = policies[0]
    
    return policy
    
    
if __name__ == '__main__':
    
    
    try:
        #Initialize script
        main()
        logger = logging.getLogger('create_service')

        #Parse XML
        organizations = parse_organizations(default_params['root'])
        
        for org in organizations:
            name = unicode(org.find('name').text)
            profile_name = unicode(org.find('profile').text)
            local_as = unicode(org.find('localAS').text)
            
            logger.info('Fetching or creating enterprise object')
            enterprise = fetch_or_create_enterprise(name, profile_name, local_as)
            
            zfbs = {}
            
            #Parse XML for nsgs
            nsgs = parse_nsgs(org)
            for nsg in nsgs:
                nsg_name = nsg.find('name').text 
                template = nsg.find('nsg_template').text
                location = nsg.find('location').text
                mac_address = nsg.find('mac_address').text
                zfb_name = nsg.find('zfb_name').text
                
                if zfb_name in zfbs:
                    zfbs[zfb_name].append(mac_address)
                else:
                    vlist = [mac_address]
                    zfbs[zfb_name] = vlist
                
                logger.info('Fetching or creating nsg object')
                current_nsg = fetch_or_create_nsg(enterprise, nsg_name, template, location, mac_address)
                
                logger.info('Updating NSG uplink properties')
                uplink_properties = nsg.find('uplinkProperties')
                for port in uplink_properties:
                                        
                    #nsport settings
                    physical_name = port.find('physicalName').text
                    mtu = int(port.find('mtu').text)
                    #mtu = int(mtu)
                    speed = port.find('speed').text
                    nat_traversal = port.find('NATTraversal').text
                    
                    #Uplink connection settings
                    role = port.find('role').text
                    pppoe_config = port.find('pppoeConfig').text
                    username = port.find('username').text
                    password = port.find('password').text
                    mode = port.find('mode').text
                    netmask = port.find('netmask').text
                    address = port.find('address').text
                    gateway = port.find('gateway').text
                    dns_address = port.find('DnsAddress').text
                    
                    create.create_uplink_properties(nsg = current_nsg, physical_name = physical_name ,mtu = mtu, speed = speed, 
                                             nat_traversal = nat_traversal, role = role, pppoeConfig = pppoe_config, 
                                             username = username, password = password, mode = mode, netmask = netmask, 
                                             address = address, gateway = gateway, dns_address = dns_address)
                    '''
                    create_uplink_properties(nsg = current_nsg, physical_name = physical_name ,mtu = mtu, speed = speed, 
                                             nat_traversal = nat_traversal, role = role, pppoeConfig = pppoe_config, 
                                             username = username, password = password, mode = mode, netmask = netmask, 
                                             address = address, gateway = gateway, dns_address = dns_address)
                    '''
                    
            #Build ZFB entries
            keys = zfbs.keys()
            for key in keys:
                fetch_or_create_zfb(enterprise, key, zfbs[key])
                             
            #Parse services
            services = parse_services(org)
            for service in services:
                service_type = service.find('type').text
                service_name = service.find('name').text
                service_template = service.find('template').text
                
                template = fetch_or_create_service_template(enterprise, service_template)
                
                att_string = "create_" + (service_type.replace("+","_")).lower()
                
                #Call correct function based on dispatch pattern        
                domain = locals()[att_string](enterprise, template, service_name)
                
                #Create domain QoS policy
                qos_policies = parse_qos(service)
                for qos_policy in qos_policies:
                    qos_policy_name = qos_policy.find('name').text
                    qos_policy_description = qos_policy.find('description').text
                    qos_policy_trust = qos_policy.find('trust_forwarding_class').text
                    qos_policy_class = qos_policy.find('forwarding_class').text
                    qos_policy_active = qos_policy.find('active').text
                    
                    if qos_policy_trust[0].upper() == 'T':
                        qos_policy_trust = True
                    else:
                        qos_policy_trust = False
                    
                    if qos_policy_active[0].upper() == 'T':
                        qos_policy_active = True
                    else:
                        qos_policy_active = False
                    
                    fetch_or_create_domain_qos_policy(domain = domain, name = qos_policy_name, 
                                                      description = qos_policy_description, trust = qos_policy_trust, 
                                                      forwarding_class = qos_policy_class, active = qos_policy_active)
                
                zones = parse_zones(service)
                for zone in zones:
                    zone_name = "Zone " + zone.find('name').text
                    zone_description = zone.find('description')
                    
                    if zone_description is None:
                        zone_description = zone_name
                    else:
                        zone_description = zone_description.text
                        
                    zone_encryption = DEFAULT_ZONE_ENCRYPTION
                    zone_multicast = DEFAULT_ZONE_MULTICAST
                    zone_public = DEFAULT_ZONE_PUBLIC
                    
                    current_zone = fetch_or_create_zone(enterprise, domain, zone_name, zone_description, zone_encryption,
                                                        zone_multicast, zone_public)
                    
                    att_string = "create_" + (service_type.replace("+","_")).lower() + '_policies'
                    
                    #Call correct function based on dispatch pattern        
                    locals()[att_string](enterprise, domain, current_zone)
                    
                    if zone_description == DEFAULT_SPOKE_DESCRIPTION:
                        create_spoke_policies(enterprise, domain, current_zone)
                    
                    #Fetch subnets in zone
                    subnets = parse_subnets(zone)
                    for subnet in subnets:
                        subnet_name = subnet.find('name').text
                        subnet_network = subnet.find('network').text
                        subnet_mask = subnet.find('subnet_mask').text
                        subnet_nsg_name = subnet.find('nsg_name').text                                                                                                                                                                                                   
                        
                        #DNS
                        dns = subnet.find('dns')
                        subnet_dns_values = ''
                        for de in dns:
                            if de.text is not None:
                                dns_add = IPAddress(de.text)
                                subnet_dns_values = subnet_dns_values + format(int(dns_add),'02x').zfill(8)
                            else:
                                subnet_dns_values = fetch_default_dns()
                                break
                        
                        #print subnet_name
                        #print subnet_network
                        #print subnet_mask
                        #print subnet_nsg_name
                        #print ''
                        enc = locals()[(service_type.replace("+","_")).upper() + "_SUBNET_ENCRYPTION"]
                        pat = locals()[(service_type.replace("+","_")).upper() + "_SUBNET_PAT"]
                        underlay = locals()[(service_type.replace("+","_")).upper() + "_SUBNET_UNDERLAY"]
                        
                        #print 'Encryption' + enc
                        #print 'PAT' + pat
                        #print 'Underlay' + underlay
                                                
                        current_subnet = fetch_or_create_subnet(current_zone, subnet_name, subnet_network, 
                                                                subnet_mask, enc, pat, 
                                                                underlay, subnet_dns_values)
                        
                        
                        vports = parse_vports(subnet)
                        for vport in vports:
                            vport_name = vport.find('name').text
                            vport_nsg_port = vport.find('nsg_port').text
                            vport_vlan = vport.find('vlan').text
                            
                            subnet_nsg = fetch_nsg(enterprise, nsg_prefix = subnet_nsg_name)
                            
                            bridge_interfaces = parse_bridge_interfaces(vport)
                            
                            current_vport = fetch_or_create_vports(subnet_nsg, current_subnet, 
                                                                   vport_nsg_port, vport_vlan, vport_name, enterprise)
                            
                            for bridge_interface in bridge_interfaces:
                                bridge_interface_name = bridge_interface.find('name').text
                                
                                current_bridge_interface = fetch_create_bridge_interface(current_vport, bridge_interface_name)
                            
                            
    except requests.exceptions.MissingSchema:
        print "Encountered error. Check API url:"
        exc_type, exc_value, exc_traceback = sys.exc_info()
        #print exc_type
        logger = logging.getLogger('create_service')
        logger.info(exc_value)
        print exc_value
        #print exc_traceback
    except bambou.exceptions.BambouHTTPError as ex:
        #print "Unauthorized user. Check username and password"
        #exc_type, exc_value, exc_traceback = sys.exc_info()
        #print exc_type
        #print exc_value[0]
        logger = logging.getLogger('create_service')
        status_code = ex.connection.response.status_code
        
        if status_code == 400:
            logger.info('HTTP Error 400')
            print 'HTTP Error 400 - Bad request'
            print 'Malformed request'
        elif status_code == 401:
            logger.info('HTTP Error 401')
            print 'HTTP Error 401 - Unauthorized user.'
            print 'Check username and password'
        elif status_code == 403:
            logger.info('HTTP Error 403')
            print 'HTTP Error 403 - Not Authorized.'
            print 'Insufficient user rights'
        elif status_code == 404:
            logger.info('HTTP Error 404')
            print 'HTTP Error 404 - Not Found.'
            print 'Request for something which does not exist'
        elif status_code == 409:
            logger.info('HTTP Error 409')
            print 'HTTP Error 409 - Not Authorized.'
            print 'Requested operation conflicts with current configuration'
        elif status_code == 412:
            logger.info('HTTP Error 412')
            print 'HTTP Error 412 - Precondition fail'
            print 'Additional information required'
        elif status_code == 500:
            logger.info('HTTP Error 500')
            print 'HTTP Error 500 - Internal server error' 
        
        #print exc_traceback
    except:
        print "Unknown Error"
        logger.info('Unknown error encountered')
        print sys.exc_info()            

        