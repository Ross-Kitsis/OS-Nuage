'''
Created on Dec 21, 2016

@author: t916355
'''

import keystoneclient.v2_0.client as ksclient
import time
from credentials import get_keystone_creds
from credentials import get_nova_creds
#from novaclient import client as novaclient
from novaclient.client import Client

if __name__ == '__main__':
    
    creds = get_keystone_creds()
    keystone = ksclient.Client(**creds)
    print keystone.auth_token
    
    #Service Catalog
    
    nova_endpoint = keystone.service_catalog.url_for(service_type='compute',endpoint_type='publicURL')
    print nova_endpoint
    
    
    '''
    creds = get_nova_creds()
    nova = novaclient.Client("2",**creds)
    print nova.auth_url
    
    #print nova.flavors.list()
    '''
    
    nova_creds = get_nova_creds()
    nt = Client(**nova_creds)
    #nt = novaclient.Client("2",**creds)
    #nt = novaclient.Client("2","ross","ross123","ross_proj","http://172.18.181.250:5000/v2.0",service_type="compute")
    #nt = novaclient.Client('2',auth_url = "http://172.18.181.250:5000/v2.0", token = keystone.auth_token)
    print '>>>> Servers <<<<'
    servers = nt.servers.list()
    for server in servers:
        print server.name, server.id
        print nt.servers.interface_list(server.id)[0].mac_addr
    
    print ''
    print '>>>> Images <<<<<'
    images = nt.images.list()
    for image in images:
        print image.name
    
    print ''
    print '>>>> Flavors <<<<'
    flavors = nt.flavors.list()
    for flavor in flavors:
        print flavor.name, flavor.id
        
    print ''
    print '>>>> Networks <<<<'
    networks = nt.networks.list()
    for network in networks:
        print network.label, network.id
    
    
    '''
    print ''
    print 'Creating instance'
    image = nt.images.find(name="nsgv image 40r3")
    flavor = nt.flavors.find(name="m1.small")
    net = nt.networks.find(label='VL_3009')
    print net
    nics = [{'net-id':net.id}]
    instance = nt.servers.create(name="Python_Type", image=image, flavor = flavor, nics=nics)
    
    print "Sleeping for 5s, then attempting to list new server"
    time.sleep(5)
    print "Listing VMs"
    print nt.servers.list()
    '''