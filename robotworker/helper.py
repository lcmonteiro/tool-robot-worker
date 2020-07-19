#!/usr/bin/env python
###################################################################################################
###-                    {robotworker Helper}                                                       ##-#
###-                                                                                           ##-#
###-Authors: Luis Monteiro                                                                     ##-#
###################################################################################################
# function
from os.path import normpath, join, exists, dirname
from re      import match

# typenames
from collections import OrderedDict
from string      import Template

# #############################################################################
# -----------------------------------------------------------------------------
# load configuration file
# -----------------------------------------------------------------------------
def load_conf(file):
    from yaml          import SafeLoader, load 
    from yaml.resolver import BaseResolver
    from collections   import OrderedDict
    class OrderedLoader(SafeLoader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    if file:
        with open(file, 'r') as ss:
            return load(ss, OrderedLoader)
    return {}

# #############################################################################
# -----------------------------------------------------------------------------
# update path on document
# -----------------------------------------------------------------------------
def update_path(data, origin):
    from os.path import dirname
    # extract path
    origin = normpath(dirname(origin))
    def process(var):
        if isinstance(var, set):
            return set([process(v) for v in var])
        if isinstance(var, list):
            return [process(v) for v in var]
        if isinstance(var, dict):
            return {k:process(var[k]) for k in var}
        if isinstance(var, OrderedDict):
            return OrderedDict({k:process(var[k]) for k in var})
        if isinstance(var, str):
            if match('(\.\.?/.+)|(\.)', var):
                path = normpath(join(origin, var))
                if exists(path):
                    return path
        return var
    return process(data)

# #############################################################################
# -----------------------------------------------------------------------------
# formart data
# -----------------------------------------------------------------------------
# engine for format
class Formater(Template): 
    idpattern = r'(?a:[_a-z][\.\-_a-z0-9]*)'

# format a text string
def format_text(text, context):
    return Formater(text).substitute(context)

# fromat recurcively a document
def format_data(data, context):
    def process(var):
        if isinstance(var, set):
            return set([process(v) for v in var])
        if isinstance(var, list):
            return [process(v) for v in var]
        if isinstance(var, dict):
            return {k:process(var[k]) for k in var}
        if isinstance(var, OrderedDict):
            return OrderedDict({k:process(var[k]) for k in var})
        if isinstance(var, str):
            return Formater(var).substitute(context)
        return var
    return process(data)

# #############################################################################
# -----------------------------------------------------------------------------
# parse data given a pattern
# -----------------------------------------------------------------------------
def parse_text(data, pattern):
    # match pattern
    matched = match(pattern, data)
    # process results
    group = matched.groupdict()
    if group:
        return group if len(group) > 1 else group.popitem()[1]
    group = matched.groups()
    if group:
        return group if len(group) > 1 else group[0]
    return data

###################################################################################################
# -------------------------------------------------------------------------------------------------
# end
# -------------------------------------------------------------------------------------------------
###################################################################################################