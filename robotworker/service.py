#!/usr/bin/env python
###################################################################################################
### -                            {robotworker Node}                                                ##-#
### -                                                                                          ##-#
### - Authors: Luis Monteiro                                                                   ##-#
###################################################################################################

###################################################################################################
# -------------------------------------------------------------------------------------------------
# imports
# -------------------------------------------------------------------------------------------------
###################################################################################################
from subprocess         import Popen                 as build_server
from xmlrpc.client      import ServerProxy           as build_proxy
from robotremoteserver  import stop_remote_server    as stop_server
from robotremoteserver  import test_remote_server    as test_server

###################################################################################################
# -------------------------------------------------------------------------------------------------
# Service
# -------------------------------------------------------------------------------------------------
###################################################################################################
class Service(object):
    
    # ###################################################################################
    # -----------------------------------------------------------------------------------
    #   constructor
    # -----------------------------------------------------------------------------------
    def __init__(self, cmd, host, port, args:dict):
        # build server command
        self.__cmd  = [cmd]
        self.__cmd += [f'--host={host}', f'--port={port}']
        self.__cmd += [f'--{k}={v}' for k, v in args.items()]
        # build proxy uri 
        self.__uri = f'http://{host}:{port}'

        # build server
        self.__server = build_server(self.__cmd, shell=True)
        # build proxy
        self.__proxy  = build_proxy (self.__uri) 
 
    # ###################################################################################
    # -----------------------------------------------------------------------------------
    #   destructor
    # -----------------------------------------------------------------------------------
    def __del__(self):
        # kill process
        self.__server.kill()
    
    # ###################################################################################
    # -----------------------------------------------------------------------------------
    # get address
    # -----------------------------------------------------------------------------------
    def address(self):     
        return self.__uri
   
    # ###################################################################################
    # -----------------------------------------------------------------------------------
    # execute keyword
    # -----------------------------------------------------------------------------------
    def execute(self, name, *args, **kwargs):     
        return self.__proxy.run_keyword(name, args, kwargs)

    # ###################################################################################
    # -----------------------------------------------------------------------------------
    # restart node
    # -----------------------------------------------------------------------------------
    def restart(self, timeout=5):
        from time import time, sleep
        end = time() + timeout
        # send a stop command
        stop_server(self.__uri)
        while time() < end:
            test_server(self.__uri)
            
###################################################################################################
# -------------------------------------------------------------------------------------------------
# End
# -------------------------------------------------------------------------------------------------
###################################################################################################
