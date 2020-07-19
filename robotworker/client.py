#!/usr/bin/env python
###################################################################################################
###-                    {robotworker Client}                                                       ##-#
###-                                                                                           ##-#
###-Authors: Luis Monteiro                                                                     ##-#
###################################################################################################

###################################################################################################
# -------------------------------------------------------------------------------------------------
# imports
# -------------------------------------------------------------------------------------------------
###################################################################################################
# external
import pickle        as pk
import xmlrpc.client as xc
import functools     as ft

###################################################################################################
# -------------------------------------------------------------------------------------------------
# Default
# -------------------------------------------------------------------------------------------------
###################################################################################################
URI = 'http://127.0.0.1:20000'

###################################################################################################
# -------------------------------------------------------------------------------------------------
# Client
# -------------------------------------------------------------------------------------------------
###################################################################################################
class Client(xc.ServerProxy):
    def run(self, name, *args, result=True, stdout=False, stderr=False):
        from sys import stderr
        # run keyword
        report = self.run_keyword(name, args)
        # check status
        if report.pop('status', 'FAIL')  == 'FAIL':
            stderr.write(report.get('output', ''))
            raise RuntimeError(report.get('error', 'unknown'))
        # return - filter
        if not result:
            report.pop('return', None)
        # output - filter
        if 'output' in report:
            out = report.pop('output', [])
            if stdout:
                report['output'] = out.splitlines()
        return report.popitem()[1] if len(report) == 1 else report

###################################################################################################
# -------------------------------------------------------------------------------------------------
# environment
# -------------------------------------------------------------------------------------------------
###################################################################################################
class Environment:
    # -------------------------------------------------------------------------
    # init environment
    # -------------------------------------------------------------------------
    def __init__(self, path):
        self.__path = path
        try:
            self.load(path)
        except Exception:
            self.reset(URI)

    # -------------------------------------------------------------------------
    # delete environment
    # -------------------------------------------------------------------------
    def __del__(self):
        self.save()

    # -------------------------------------------------------------------------
    # load environment
    # -------------------------------------------------------------------------
    def load(self, path):
        with open(path, 'rb') as f:
            self.__env = pk.load(f)

    # -------------------------------------------------------------------------
    # reset environment
    # -------------------------------------------------------------------------
    def reset(self, uri):
        from collections import OrderedDict
        self.__env = dict(
            stack = [('worker', dict(uri=uri))])

    # -------------------------------------------------------------------------
    # save environment
    # -------------------------------------------------------------------------
    def save(self):
        with open(self.__path, 'wb') as f:
            pk.dump(self.__env, f)

    # -------------------------------------------------------------------------
    # discard environment
    # -------------------------------------------------------------------------
    def discard(self):
        def ignore(): 
            pass
        setattr(self, 'save', ignore)
    
    # -------------------------------------------------------------------------
    # push selection
    # -------------------------------------------------------------------------
    def push_selection(self, name, uri):
        self.__env['stack'].append((name, dict(uri=uri)))

    # -------------------------------------------------------------------------
    # pop selection
    # -------------------------------------------------------------------------
    def pop_selection(self):
        if len(self.__env['stack']) > 1:
            self.__env['stack'].pop()
        else:
            raise RuntimeError('Invalid Service Path')

    # -------------------------------------------------------------------------
    # root selection
    # -------------------------------------------------------------------------
    def root_selection(self):
        while len(self.__env['stack']) > 1:
            self.__env['stack'].pop()

    # -------------------------------------------------------------------------
    # get selection
    # -------------------------------------------------------------------------
    def get_selection(self):
        for elem in reversed(self.__env['stack']):
            return elem

    # -------------------------------------------------------------------------
    # connect
    # -------------------------------------------------------------------------
    def connect(self):
        # get servive url
        _, ctxt = self.get_selection()
        # create a client
        return Client(ctxt['uri'])
    
    # -------------------------------------------------------------------------
    # check service
    # -------------------------------------------------------------------------
    def check(self, timeout=10):
        from time import time, sleep
        end = time() + timeout
        while time() <= end:
            try:
                # test server
                self.connect().get_keyword_names()
                # return server information
                return self.get_selection()
            except:
                # wait
                sleep(1)
        # test server
        self.connect().get_keyword_names()
        # return server information
        return self.get_selection()
        
    # -------------------------------------------------------------------------
    # select service
    # -------------------------------------------------------------------------
    def select(self, path):
        from posixpath import normpath 
        # process path elements
        for name in normpath(path).split('/'):
            if name == '':
                self.root_selection()
                continue
            if name == '..':
                self.pop_selection()
                continue
            if name == '.':
                continue
            # connet to server
            cnt = self.connect()
            # get address
            uri = cnt.run('get_services')[name]
            # get servive address
            self.push_selection(name, uri)
        return self

# #######################################################################################
# ---------------------------------------------------------------------------------------
# environment dry : changes are not saved
# ---------------------------------------------------------------------------------------
class DiscardedEnvironment(Environment):
    def __del__(self):
        pass

###################################################################################################
# -------------------------------------------------------------------------------------------------
# robot : execute a profile
# -------------------------------------------------------------------------------------------------
###################################################################################################
class Robot:
    # -------------------------------------------------------------------------
    # load
    # -------------------------------------------------------------------------
    def __init__(self, profile):
        # functions
        from .helper import load_conf
        from .helper import update_path
        # load profile
        self.__profile = update_path(load_conf(profile), profile)

    # -------------------------------------------------------------------------
    # execute 
    # -------------------------------------------------------------------------
    def __call__(self, select, servers):
        from robot.run import run_cli
        # merge data with profile
        data = self.merge(self.__profile, 
            select =select, 
            servers=servers)
        # serialize merged profile
        data = self.serialize(data)
        # run merged profile
        run_cli(data)

    # -------------------------------------------------------------------------
    # loader
    # -------------------------------------------------------------------------
    @staticmethod
    def loader(file):
        from yaml import safe_load
        if file:
            with open(file, 'r') as ss:
                return safe_load(ss)
        return {}

    # -------------------------------------------------------------------------
    # merge
    # -------------------------------------------------------------------------
    @staticmethod
    def merge(profile, **kargs):
        from .helper import parse_text
        # merge process
        for key, val in kargs.items():
            # select
            if key == 'select':
                profile[key] = val
                continue
            # servers
            if key == 'servers':
                # get variables 
                var = profile.get('variables', {})            
                # merge servers
                for k, v in val.items():
                    var[f'{k}_host'] = parse_text(v, 'http://(.+:.+)')
                # update profile
                profile['variables'] = var
                continue
        # profile updated
        return profile

    # -------------------------------------------------------------------------
    # serialize
    # -------------------------------------------------------------------------
    @staticmethod
    def serialize(profile):
        out = []
        # python path
        for path in profile.get('includes', []):
            out +=['--pythonpath', path]
        # options
        for opt, val in profile.get('options', {}).items():
            out +=['--'+ opt, val]
        # variables 
        for key, val in profile.get('variables', {}).items():
            out +=['--variable', key + ':' + val]
        # includes
        for tag in profile.get('select', []):
            out +=['--include', tag]    
        # entry point
        out.append(profile.get('start', '.'))
        return out

###################################################################################################
# -------------------------------------------------------------------------------------------------
# commands
# -------------------------------------------------------------------------------------------------
###################################################################################################
import click
# ---------------------------------------------------------------------------------------
# base command
# ---------------------------------------------------------------------------------------
@click.group()
@click.option('--env'   , default='.us.env', type=click.Path())
@click.option('--select', default= None    , type=click.STRING)
@click.pass_context
def cli(ctx, env, select):
    try:
        # create environment
        if select:
            # temporary
            ctx.obj = DiscardedEnvironment(env)
            ctx.obj.select(select)
            return
        # default
        ctx.obj = Environment(env)
    except Exception as ex:
        raise click.ClickException(str(ex))

# ---------------------------------------------------------------------------------------
# list keywords
# ---------------------------------------------------------------------------------------
@cli.command('+', help='list keywords')
@click.pass_obj
def list_keywords(env):
    try:
        # connet to server
        client = env.connect()
        # list keyworks
        click.echo(f'{"COMMAND":30} {"ARGUMENTS"}')
        for key in client.get_keyword_names():
            click.echo(f'{key:30} [{" ".join(client.get_keyword_arguments(key))}]')
    except ConnectionRefusedError as ex:
        raise click.ClickException(ex)

# ---------------------------------------------------------------------------------------
# execute keyword
# ---------------------------------------------------------------------------------------
SETTINGS=dict(ignore_unknown_options=True)
@cli.command('.', help='execute keyword', context_settings=SETTINGS)
@click.argument('name', nargs= 1, type=click.STRING)
@click.argument('args', nargs=-1, type=click.STRING)
@click.pass_obj
def execute_keyword(env, name, args):
    from yaml import dump
    # transform name & args
    def transform(name, args):
        path = name.split('.')
        path = [x for c in path[:-1] for x in ['proxy', c]] + path[-1:]
        return (path[0], path[1:] + list(args)) 
    try:
        # connet to server
        client    = env.connect()
        # create path
        cmd, args = transform(name, args)
        # execute command
        click.echo(dump(client.run(cmd, *args, stdout=True), sort_keys=False))
    except ConnectionRefusedError as ex:
        raise click.ClickException(ex)
    except RuntimeError as ex:
        raise click.ClickException(ex)
    except Exception as ex:
        raise click.ClickException(ex)

# ---------------------------------------------------------------------------------------
# list services
# ---------------------------------------------------------------------------------------
@cli.command('list', help='list services')
@click.pass_obj
def list_services(env):
    try:
        # connet to server
        client = env.connect()
        # list keyworks
        click.echo(f'{"SERVICES":30}{"ADDRESS"}')
        for name, uri in client.run('get_services').items():
            click.echo(f'{name:30}{uri}')
    except ConnectionRefusedError as ex:
        raise click.ClickException(ex)
    except Exception as ex:
        raise click.ClickException(str(ex))

# ---------------------------------------------------------------------------------------
# select service
# ---------------------------------------------------------------------------------------
@cli.command('select', help='select service')
@click.option('--timeout', default=10 , nargs= 1, type=click.INT)
@click.argument('path'   , default='.', nargs= 1, type=click.STRING)
@click.pass_obj
def select_service(env, timeout, path):
    from yaml import dump
    try:
        # get servive address
        click.echo(dump(dict([env.select(path).check(timeout)])))
    except Exception as ex:
        env.discard()
        raise click.ClickException(ex)
    except KeyboardInterrupt as ex:
        env.discard()
        raise click.Abort(ex)
# ---------------------------------------------------------------------------------------
# run robot
# ---------------------------------------------------------------------------------------
@cli.command('robot', help='run robot')
@click.argument('select', nargs= -1, type=click.STRING)
@click.argument('profile', nargs= 1,  type=click.STRING)
@click.pass_obj
def robot(env, select, profile):
    try:
        # create robot
        robot = Robot(profile)
        # get servers
        servers = env.connect().run('get_services')
        # run robot
        click.echo(robot(select, servers))
    except Exception as ex:
        env.discard()
        raise click.ClickException(ex)
    except KeyboardInterrupt as ex:
        env.discard()
        raise click.Abort(ex)

###################################################################################################
# -------------------------------------------------------------------------------------------------
# main
# -------------------------------------------------------------------------------------------------
###################################################################################################
def main(arguments=None):
    cli(args=arguments)

###################################################################################################
# -------------------------------------------------------------------------------------------------
# run
# -------------------------------------------------------------------------------------------------
###################################################################################################
if __name__ == '__main__':
    exit(main(None))

###################################################################################################
# -------------------------------------------------------------------------------------------------
# end
# -------------------------------------------------------------------------------------------------
###################################################################################################