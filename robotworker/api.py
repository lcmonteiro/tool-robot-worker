#!/usr/bin/env python3
###################################################################################################
###-           {API Robot Worker}                                                              ##-#
###-Base Robot Tool                                                                            ##-#
###-Authors:   Luis Monteiro                                                                   ##-#
###-Reviewers:                                                                                 ##-#
###################################################################################################

###################################################################################################
# -------------------------------------------------------------------------------------------------
# imports
# -------------------------------------------------------------------------------------------------
###################################################################################################
# ---------------------------------------------------------
# external
# ---------------------------------------------------------
# functions
from logging  import getLogger  as logger
# objects
from string   import Template

# ---------------------------------------------------------
# internal
# ---------------------------------------------------------
# objects
from .service import Service

# #################################################################################################
# -------------------------------------------------------------------------------------------------
# helpers
# -------------------------------------------------------------------------------------------------
# #################################################################################################
class Pattern(Template): 
    idpattern = r'(?a:[_a-z][\.\-_a-z0-9]*)'

###################################################################################################
# -------------------------------------------------------------------------------------------------
# robotworker Api
# -------------------------------------------------------------------------------------------------
###################################################################################################
class Api(object):
    '''
        :description:   Api for robotworker 
        :params:	    None
        :return:	    Object robotworker Api 
    '''
    #####################################################################################
    # -----------------------------------------------------------------------------------
    #  Constructor
    #  @conf: configuration
    #  @ext : extensions 
    # -----------------------------------------------------------------------------------
    def __init__(self, conf={}, ext=[]):
        # initialize logger
        self._log        = logger()
        # load context
        self._context    = self._load_context(conf.get('context', {}))
        # load services
        self._services   = self._load_services(conf.get('services', {}))
        # load extensions
        self._extensions = self._load_extensions(conf.get('extensions', {}),  ext)
        # load sequences
        self._sequences  = self._load_sequences(conf.get('sequences', {}))

    #####################################################################################
    # -----------------------------------------------------------------------------------
    #  context manager
    # -----------------------------------------------------------------------------------
    def __enter__(self):
        pass
    def __exit__(self, err_type, err_value, err_trace):
        pass
                
    #####################################################################################
    # -----------------------------------------------------------------------------------
    #   proxy services
    # -----------------------------------------------------------------------------------
    def proxy(self, server, func, *args, **kwargs):
        report = self._services[server].execute(func, *args, **kwargs)
        # check status
        if report.pop('status', 'FAIL')  == 'FAIL':
            raise RuntimeError(report.get('error', 'unknown'))
        # print stdout
        if 'output' in report:
            print(report['output'])
        # return data
        return report.get('return', None)

    #####################################################################################
    # -----------------------------------------------------------------------------------
    #   get services
    # -----------------------------------------------------------------------------------
    def get_services(self):
        return {name:service.address() for name, service in self._services.items()}

    #####################################################################################
    # -----------------------------------------------------------------------------------
    #   get extensions
    # -----------------------------------------------------------------------------------
    def get_extensions(self):
        return self._extensions.copy()

    #####################################################################################
    # -----------------------------------------------------------------------------------
    #   get context
    # -----------------------------------------------------------------------------------
    def get_context(self):
        return self._context.copy()

    #####################################################################################
    # -----------------------------------------------------------------------------------
    #   add context
    # -----------------------------------------------------------------------------------
    def add_context(self, ctxt):
        return self._context.update(ctxt)

    #####################################################################################
    # -----------------------------------------------------------------------------------
    #   load context
    # -----------------------------------------------------------------------------------
    def _load_context(self, conf):
        from os import environ
        # use current environment 
        context = environ.copy()
        # update with command config
        context.update(conf)
        return context

    #####################################################################################
    # -----------------------------------------------------------------------------------
    #   load services
    # -----------------------------------------------------------------------------------
    def _load_services(self, conf):
        services = {}
        for name, params in conf.items():
            services[name] = Service(
                params['cmd'],
                params['host'],
                params['port'],
                params.get('settings', {}))
        return services
    
    #####################################################################################
    # -----------------------------------------------------------------------------------
    # load extension
    # -----------------------------------------------------------------------------------
    def _load_extensions(self, configuration, registration):
        extensions = {} 
        for register in registration if isinstance(registration, list) else []:
            # check name
            if 'name' not in register:
                self._log.warning('check extensions: name not found')
                continue
            name = register['name']
            # check configuration
            if name not in configuration:
                self._log.warning(f'check extensions: {name} is found')
                continue
            conf = configuration[name]
            # register
            extensions[name] = self._add_extension(register, conf)
        # return extension
        return extensions
        
    #####################################################################################
    # -----------------------------------------------------------------------------------
    # add extension
    # -----------------------------------------------------------------------------------
    def _add_extension(self, register, configuration):
        if 'init' in register:
            register['init'](self, configuration)
        for func in register['func']:
            setattr(Api, func.__name__, func)
        return[func.__name__ for func in register['func']]
    
    #####################################################################################
    # -----------------------------------------------------------------------------------
    # load sequencies
    # -----------------------------------------------------------------------------------
    def _load_sequences(self, config):
        from functools import partial
        sequences = {} 
        for name, params in config.items():
            sequence = partial(self._run_sequence, params)
            sequences[name] = sequence
            setattr(self, name, lambda *args, **kargs: sequence(args, kargs))
        return sequences

    #####################################################################################
    # -----------------------------------------------------------------------------------
    # run sequence
    # -----------------------------------------------------------------------------------
    def _run_sequence(self, config, args=[], kargs={}):
        # utilities
        template = lambda o, c   : Pattern(o).substitute(c).split()
        execute  = lambda p, a, k: getattr(self, p[0])(*(p[1:] + a), **k)
        build    = lambda p      : [x for c in p[:-1] for x in ['proxy', c]] + p[-1:]
        # get properties
        context  = config.get('context', {})
        sequency = config.get('sequence' , {})
        # build context
        context = self.get_context()
        context.update(context)
        context.update(zip(context, args))
        context.update(kargs)
        # run sequency
        report = {}
        for cmd, opt in sequency.items():
            # get arguments from options
            args, kargs = {
                str  : lambda o, c : (template(o, c), {}),
                list : lambda o, c : (o, {}),
                dict : lambda o, c : ([], o)
            }[type(opt)](opt, context)
            # execute command
            report[cmd] = execute(build(cmd.split('.')), args, kargs)
        return report

###################################################################################################
# -------------------------------------------------------------------------------------------------
# end
# -------------------------------------------------------------------------------------------------
###################################################################################################
