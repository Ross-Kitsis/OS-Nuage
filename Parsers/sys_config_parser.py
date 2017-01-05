'''
Parses system configuration and provides inferface for other classes to get config information

@author: t916355
'''

class SysConfigParser(object):
    '''
    classdocs
    '''
    
    def get_max_page_size(self):
                
        return self.__config.page_max_size
    
    def get_page_size(self):
                
        return self.__config.page_size
    
    
    def __init__(self, session):
        csproot = session.user
        
        csproot.system_configs.fetch()
        
        self.__config = csproot.system_configs[0]
        
        