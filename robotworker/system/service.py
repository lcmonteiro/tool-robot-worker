#!/usr/bin/env python
###################################################################################################
###-                            {Robotworker Remote Server}                                        ##-#
###-                                                                                           ##-#
###-Authors: Luis Monteiro                                                                     ##-#
###################################################################################################

###################################################################################################
# -------------------------------------------------------------------------------------------------
# imports
# -------------------------------------------------------------------------------------------------
###################################################################################################
import win32serviceutil  as wu
import win32service      as ws
import win32event        as we
import subprocess        as sp
import psutil            as pu

###################################################################################################
# -------------------------------------------------------------------------------------------------
# WinService - uservice
# -------------------------------------------------------------------------------------------------
###################################################################################################
class WinService(wu.ServiceFramework):
    _svc_name_         = 'robotworker'
    _svc_display_name_ = 'Robot Worker'

    # -------------------------------------------------------------------------
    # Propreties
    # -------------------------------------------------------------------------
    @staticmethod
    def name():
        return WinService._svc_name_
    @staticmethod
    def display_name():
        return WinService._svc_display_name_

    # -------------------------------------------------------------------------
    # WinService Initialization
    # -------------------------------------------------------------------------
    def __init__(self, *args):
        # service initialization
        super().__init__(*args)
        # extract properties 
        self.__extract_properties()
        # update environment
        self.__update_environment()
        
    # -------------------------------------------------------------------------
    # WinService Statup
    # -------------------------------------------------------------------------
    def SvcRun(self):
        self.ReportServiceStatus(ws.SERVICE_START_PENDING)
        try:
            # create process
            self.__process = sp.Popen(self._svc_cmd_,
                stdout=sp.DEVNULL, stderr=sp.DEVNULL, stdin=sp.DEVNULL)
            # publish status
            self.ReportServiceStatus(ws.SERVICE_RUNNING)
            # wait process
            self.__process.communicate()
        finally:
            self.ReportServiceStatus(ws.SERVICE_STOP_PENDING)

    # -------------------------------------------------------------------------
    # WinService Shutdown
    # -------------------------------------------------------------------------
    def SvcStop(self):
        from contextlib import suppress
        from signal     import CTRL_C_EVENT
        # stop process
        self.ReportServiceStatus(ws.SERVICE_STOP_PENDING)
        try:
            # get all processes
            parent    = pu.Process(self.__process.pid)
            processes = parent.children(recursive=True)
            processes.append(parent)
            # send ctrl-c 
            for process in processes:
                with suppress(Exception): process.send_signal(CTRL_C_EVENT)
            # wait processes end
            pu.wait_procs(processes, 5)
        except pu.TimeoutExpired:
            # kill all processes
            with suppress(Exception):
                for process in processes:
                    with suppress(Exception): process.kill()
        finally:
            self.ReportServiceStatus(ws.SERVICE_STOPPED)

    # -------------------------------------------------------------------------
    # WinService Tools
    # -------------------------------------------------------------------------
    def __extract_properties(self):
        # get working directory
        self._svc_cwd_ = wu.GetServiceCustomOption(self._svc_name_,'cwd')    
        # get virtual environment
        self._svc_env_ = wu.GetServiceCustomOption(self._svc_name_,'env')
        # get command line    
        self._svc_cmd_ = wu.GetServiceCustomOption(self._svc_name_,'cmd')

    def __update_environment(self):
        from os import chdir 
        from os import environ as env
        from os import pathsep as sep
        # set workspace 
        chdir(self._svc_cwd_)
        # update environment path
        env['PATH'] = f"{self._svc_env_}\Scripts{sep}{env['PATH']}"
        # remove pythonhome from environment 
        env.pop('PYTHONHOME', None) 


###################################################################################################
# -------------------------------------------------------------------------------------------------
# command line interface
# -------------------------------------------------------------------------------------------------
###################################################################################################
import click

# ---------------------------------------------------------------------------------------
# base group
# ---------------------------------------------------------------------------------------
@click.group()
def cli():
    pass

# ---------------------------------------------------------------------------------------
# service bind 
# ---------------------------------------------------------------------------------------
SETTINGS=dict(ignore_unknown_options =True, allow_interspersed_args=False)
@click.command('bind', context_settings=SETTINGS)
@click.argument('cmd', nargs= 1, type=click.STRING)
@click.argument('arg', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def bind_service(ctx, cmd, arg):
    from os     import environ as env
    from os     import getcwd  as pwd
    from sys    import prefix
    from shutil import which
    # get servive name
    name = WinService.name()
    try:
        # verify commad 
        if not which(cmd):
            raise RuntimeError(f'command ({cmd}) not found')
        # set working directory
        wu.SetServiceCustomOption(name,'cwd', pwd())    
        # get virtual environment
        wu.SetServiceCustomOption(name,'env', env.get('VIRTUAL_ENV', prefix))
        # set command line    
        wu.SetServiceCustomOption(name,'cmd', ' '.join([cmd] + list(arg)))
        # success
        click.echo(f'BINDED: {name}')
    except ws.error as ex:
        raise click.ClickException(ex.strerror)
    except Exception as ex:
        raise click.ClickException(ex.strerror)

# ---------------------------------------------------------------------------------------
# install a service
# ---------------------------------------------------------------------------------------
@click.command('install', context_settings=SETTINGS)
@click.option('--user', default=None, help='user name')
def insert_service(user, cmd, arg):
    from os     import environ as env
    from os     import getcwd  as pwd
    from shutil import which
    # get servive name
    name    = WinService.name()
    # get servise display name
    display = WinService.display_name()
    try:
        # install Servive
        wu.InstallService(
            wu.GetServiceClassString(WinService), 
            name, 
            display,
            userName=user)
        # success
        click.echo(f'INSTALLED: {name}')
    except ws.error as ex:
        raise click.ClickException(ex.strerror)
    except Exception as ex:
        raise click.ClickException(ex.strerror)

# ---------------------------------------------------------------------------------------
# debug a service
# ---------------------------------------------------------------------------------------
@click.command('debug')
def debug_service():
    # get servive name
    name = WinService.name()
    try:
        wu.DebugService(WinService, argv=[name])
        click.echo(f'DEBUGED: {name}')
    except ws.error as ex:
        raise click.ClickException(ex.strerror)

# ---------------------------------------------------------------------------------------
# start a service
# ---------------------------------------------------------------------------------------
@click.command('start')
def start_service():
    # get servive name
    name = WinService.name()
    try:
        wu.StartService(name, args=['robotworker'])
        click.echo(f'STARTED: {name}')
    except ws.error as ex:
        raise click.ClickException(ex.strerror)

# ---------------------------------------------------------------------------------------
# stop a service
# ---------------------------------------------------------------------------------------
@click.command('stop')
def stop_service():
    # get servive name
    name = WinService.name()
    try:
        wu.StopService(name)
        click.echo(f'STOPPED: {name}')
    except ws.error as ex:
        raise click.ClickException(ex.strerror)

# ---------------------------------------------------------------------------------------
# remove a service
# ---------------------------------------------------------------------------------------
@click.command('uninstall') 
def remove_service():
    # get servive name
    name = WinService.name()
    try:
        wu.RemoveService(name)
        click.echo(f'UNINSTALLED: {name}')
        return 0
    except ws.error as ex:
        raise click.ClickException(ex.strerror)
###################################################################################################
# -------------------------------------------------------------------------------------------------
# main
# -------------------------------------------------------------------------------------------------
###################################################################################################
def main(arguments=None):
    cli.add_command(bind_service)
    cli.add_command(insert_service)
    cli.add_command(start_service)
    cli.add_command(stop_service)
    cli.add_command(remove_service)
    cli.add_command(debug_service)
    cli(args=arguments)
    #wu.HandleCommandLine(WinService)

###################################################################################################
# -------------------------------------------------------------------------------------------------
# run
# -------------------------------------------------------------------------------------------------
###################################################################################################
if __name__ == '__main__':
    exit(main())

###################################################################################################
# -------------------------------------------------------------------------------------------------
# end
# -------------------------------------------------------------------------------------------------
###################################################################################################