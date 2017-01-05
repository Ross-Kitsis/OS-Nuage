'''
Created on Jul 28, 2016

@author: Ross Kitsis
'''

import sys
import argparse
import os
import ConfigParser
from tabulate import tabulate
import requests
import bambou

sys.path.append("./")

from vspk.v4_0 import *
from vspk.utils import set_log_level

class ArgParser(object):
    '''
    This class parses command line arguments as well as the configuration file with default arguments
    
    Arguments not provided in the command line are loaded from the configuration file (where possible)
    
    Arguments in this parser are set based on default arguments required in almost all queries
    Each subsequent module wanted to parse more arguments most define a function to add its own arguments using the getParser function
    
    '''
    

    def getParser(self):
        return self.__parser

    def __init__(self):
        '''
        Setup the default parser with parameters common to multiple queries
        '''    
        
        config = ConfigParser.ConfigParser()
        config.read("./config.ini")
        
        #parse variables
        self.__parser = argparse.ArgumentParser(description="Set parameters - default parameters defined within config.ini", add_help=False)
    
        #parse api URL
        self.__parser.add_argument('--api',help='API URL and Port', default = config.get("NaasParam","VSD_API_URL"))
    
        #parse api username
        self.__parser.add_argument('--user',help='Nuage username', default = config.get("NaasParam","VSD_USERNAME"))
    
        #parse api password
        self.__parser.add_argument('--password',help='Nuage password', default = config.get("NaasParam","VSD_PASSWORD"))
    
        #parse api version
        self.__parser.add_argument('--version',help='API Version' , default = config.get("NaasParam","VSD_API_VERSION"))
        
        #parse organization
        self.__parser.add_argument('--organization',help='Nuage organization' , default = config.get("NaasParam","VSD_ORGANIZATION"))
        
        
        