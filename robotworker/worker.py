#!/usr/bin/env python
###################################################################################################
###-                            {robotworker Remote Worker}                                    ##-#
###-                                                                                           ##-#
###-Authors: Luis Monteiro                                                                     ##-#
###################################################################################################
# ---------------------------------------------------------------------------------------
# imports
# ---------------------------------------------------------------------------------------
# internal
from .api  import Api

# #######################################################################################
# ---------------------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------------------
# #######################################################################################
def command(name):
    from argparse import ArgumentParser
    def decorated(cls):
        init = getattr(cls, '__init__')
        if not hasattr(init, 'decoreted'):
            def _init_(self, **opts):
                self.stock.update(opts)
            # set identifiers  
            setattr(_init_, 'decoreted', True)
            # set function
            setattr(cls, '__init__', _init_)
        call = getattr(cls, '__call__')
        if not hasattr(call, 'decoreted'):
            def _call_(self, args):
                args = self.parser.parse_args(args)
                call(self, **vars(args))
            # set identifiers    
            setattr(_call_, 'decoreted', True)
            # set function
            setattr(cls, '__call__', _call_)
        # set objects
        setattr(cls, 'parser', ArgumentParser(name))
        setattr(cls, 'stock' , {})
        return cls
    return decorated
  
def option(name, default=None, help=None):
    def decorated(cls):
        cls.parser.add_argument(f'--{name}', type=type(default), help=help)
        if default:
            cls.stock[name]=default 
        return cls
    return decorated
      
def arguments(**opts):
    def wrapper(func):
        def decorated(self,**args):
            from collections   import OrderedDict
            # extract
            args = {
                k: f(args)
                for k, f in opts.items()}
            stock = {
                k: f(self.stock)
                for k, f in opts.items()}
            # combine 
            for k, v in args.items():
                if isinstance(v, (int, float, str)):
                    stock[k] = v
                    continue
                if isinstance(v, dict):
                    stock[k].update(v)
                    continue
            # execute  
            result = func(self, **stock)
            # load  
            if isinstance(result, (dict, OrderedDict)):  
                self.stock.update(result)
        return decorated 
    return wrapper

# #######################################################################################
# ---------------------------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------------------------
# #######################################################################################
def get(name):
    def wrapper(data):
        return data.get(name, None)
    return wrapper 
  
def getall():
    def wrapper(data):
        return {k:data.get(k) for k in data}
    return wrapper 
  
def pop(name):
    def wrapper(data):
        return data.pop(name, None)
    return wrapper 
  
def popall():
    def wrapper(data):
        return {k:data.pop(k) for k in data}
    return wrapper 

# #######################################################################################
# ---------------------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------------------
# #######################################################################################
@option('log' , default='robotworker.log'  , help='Worker Logger File')
@option('conf', default='configuration.yml', help='Worker Configuration')
@option('port', default= 20000             , help='Worker Port')
@option('host', default='127.0.0.1'        , help='Worker Host')
@command('robotworker')
class Worker(object):
    # -------------------------------------------------------------------------
    # properties
    # -------------------------------------------------------------------------
    EXTENSIONS = []

    # -------------------------------------------------------------------------
    # loader
    # -------------------------------------------------------------------------
    @arguments(file=pop('conf'))
    def loader(self, file):
        from .helper import load_conf
        from .helper import update_path
        return update_path(load_conf(file), file)

    # -------------------------------------------------------------------------
    # logger
    # -------------------------------------------------------------------------
    @arguments(conf=pop('log'))
    def logger(self, conf):
        from logging  import basicConfig  as config_logger
        from logging  import DEBUG        as LEVEL
        from logging  import getLogger    as logger
        config_logger(
            filemode= 'w',
            level   = LEVEL, 
            filename= conf, 
            format  = '[%(asctime)s] [%(levelname)-10s] [%(funcName)s] %(message)s')
    
    # -------------------------------------------------------------------------
    # extensions
    # -------------------------------------------------------------------------
    @arguments(ext=get('ext'))
    def extender(self, ext):
        return dict(ext=ext)

    # -------------------------------------------------------------------------
    # builder
    # -------------------------------------------------------------------------
    @arguments(
        api =pop('cls'), 
        ext =pop('ext'), 
        conf=getall())
    def builder(self, api, ext, conf):
        return dict(app = api(conf, ext))
 
    # -------------------------------------------------------------------------
    # runner
    # -------------------------------------------------------------------------
    @arguments(
        app =pop('app' ),
        host=pop('host'),
        port=pop('port'))
    def runner(self, app, host, port):
        from robotremoteserver import RobotRemoteServer
        # start robot worker with app context
        with app: RobotRemoteServer(app, host=str(host), port=int(port))

    # -------------------------------------------------------------------------
    # process
    # -------------------------------------------------------------------------
    def __call__(self, **args):
        self.loader  (**args)
        self.logger  (**args)
        self.extender(**args)
        self.builder (**args)
        self.runner  (**args)

#########################################################################################
# ---------------------------------------------------------------------------------------
# entry points
# ---------------------------------------------------------------------------------------
#########################################################################################
# -----------------------------------------------------------------------------
# main - function
# -----------------------------------------------------------------------------
def main(args=None, ext=[]):
    try :
        Worker(cls=Api, ext=ext)(args)
    except Exception as ex:
        print(str(ex))
    finally:
        exit(0)

# -----------------------------------------------------------------------------
# main - file
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()

###################################################################################################
# -------------------------------------------------------------------------------------------------
# end
# -------------------------------------------------------------------------------------------------
###################################################################################################