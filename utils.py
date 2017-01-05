'''
Useful utilities not fitting into any particular module but used as support routines

@author: Ross Kitsis
'''

import logging
from netaddr import *
from vspk.v4_0 import *


#Update ZFB with new values
def update_zfb_values(zfb, new_values):
    """This function creates and modifies NSG uplink properties as required in 4.0R3
        
    :param zfb: The ZFB entry to modify
    :type zfb: NUZFBAutoassignment
    
    :param new_values: The new values to attempt to inset into the auto assignment entry
    :type new_values: list
        
    """
    
    current_values = zfb.zfb_match_attribute_values
    
    in_current = set(current_values)
    in_new = set(new_values)
    
    diff = in_new - in_current
    new_vals = current_values + list(diff)
    
    zfb.zfb_match_attribute_values = new_vals
    zfb.save()