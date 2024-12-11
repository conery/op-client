#
# Abstract interface to the OptiPass server
#

from io import StringIO
import json
import logging
import os
import pandas as pd
import requests

class OPServerError(Exception):

    def __init__(self, resp):
        err = resp.json()['detail']
        super(OPServerError, self).__init__(err)

class MetaOP(type):
    """
    This metaclass creates the API for the OP class.  It defines read-only
    attributes that can be accessed but not written from outside the OP module.
    The values of the attributes can only be set when the setup method is
    called.  Note: one attribute (region_names) is writeable.
    """

    @property
    def server_url(cls):
        return cls._server_url
    
    @property
    def project_name(cls):
        return cls._project_name

    @property
    def region_names(cls):
        return cls._region_names
    
    @region_names.setter
    def region_names(cls, lst):
        cls._region_names = lst

    @property
    def target_frame(cls):
        return cls._target_frame

    @property
    def target_layout(cls):
        return cls._target_layout

    @property
    def mapping_name(cls):
        return cls._mapping_name

    @property
    def target_columns(cls):
        return cls._target_columns

    @property
    def total_cost(cls):
        return cls._total_cost

    @property
    def barrier_frame(cls):
        return cls._barrier_frame

    @property
    def mapinfo(cls):
        return cls._mapinfo

    @property
    def initial_tab(cls):
        return cls._initial_tab

    def setup(cls, server: str, project: str, tab: int):
        '''
        Initialize the connection to the OptiPass server.  Connect to the
        server, get the barrier file and other data for the project, save
        it in read-only class variables.

        Raises an exception if the server is not accessible or if the project
        name is not known to the server.

        Arguments:
          server: the URL of an OptiPass REST server
          project: the name of a data set on the server
          tab: the tab to show when starting the app
        '''
        req = f'{server}/projects'
        resp = requests.get(req)
        if resp.status_code != 200 or project not in resp.json():
            raise ValueError(f'unknown project: {project}')
        cls._server_url = server
        cls._project_name = project

        req = f'{server}/targets/{project}'
        resp = requests.get(req)
        if resp.status_code != 200:
            raise OPServerError(resp)
        dct = resp.json()
        buf = StringIO(dct['targets'])
        cls._target_frame = pd.read_csv(buf)
        cls._target_layout = dct['layout'].split('\n')

        req = f'{server}/colnames/{project}'
        resp = requests.get(req)
        if resp.status_code != 200:
            raise OPServerError(resp)
        dct = resp.json()
        cls._mapping_name = dct['name']
        cls._target_columns = dct['files']

        req = f'{server}/mapinfo/{project}'
        resp = requests.get(req)
        if resp.status_code != 200:
            raise OPServerError(resp)
        cls._mapinfo = json.loads(resp.json()['mapinfo'])

        req = f'{server}/barriers/{project}'
        resp = requests.get(req)
        if resp.status_code != 200:
            raise OPServerError(resp)
        buf = StringIO(resp.json()['barriers'])
        cls._barrier_frame = pd.read_csv(buf)

        total_cost = cls._barrier_frame[['region','cost']].groupby('region').sum()
        cls._region_names = sorted(list(total_cost.index))
        cls._total_cost = { r[0]: r[1].cost for r in total_cost.iterrows() }

        cls._initial_tab = tab

        logging.info('setup complete')

class OP(metaclass=MetaOP):
    """
    Interface to an OptiPass server.  The module consists of a set of
    static methods that manage a single connection (i.e. it's basically
    a singleton object). 
    """

    @staticmethod
    def url_for_figure(fn):
        return f'{OP.server_url}/static/images/'


    @staticmethod
    def format_budgets(cols):
        return { n: OP.format_budget_amount(n) for n in cols }
    
    dollar_format = {
        'thou':  (1000, 'K'),
        'mil':   (1000000, 'M'),
    }

    @staticmethod
    def format_budget_amount(n):
        divisor, suffix = OP.dollar_format['mil'] if n >= 1000000 else OP.dollar_format['thou']
        s = '${:}'.format(n/divisor)
        if s.endswith('.0'):
            s = s[:-2]
        return s+suffix

    @staticmethod
    def run_optimizer(
        regions: list[str],
        budgets: tuple[str,str],
        targets: list[str],
        weights: list[int],
        mapping: str | None,       
        ):
        '''
        Send a request to the op-server to run OptiPass using settings
        from the widgets.

        Args:
            regions: a list of geographic regions (river names) to use
            budgets: budget settings (max, increment)
            targets: a list of IDs of targets
            weights: a list of target weights
            mapping: the name of a column mapping file for targets
        '''
        # print(regions)
        # print(budgets)
        # print(targets)
        # print(weights)
        # print(mapping)
        req = f'{server}/optipass/{OP.project}'
        print(req)

class DevOP:
    '''
    A collection of utility functions for developers
    '''

    @staticmethod
    def default_list(varname):
        if lst := os.getenv(varname):
            return lst.split(':')
        return []
    
    @staticmethod
    def default_regions():
        return DevOP.default_list('OPREGIONS')

    @staticmethod
    def default_budget():
        return int(os.getenv('OPBUDGET','0'))

    @staticmethod
    def default_targets():
        return DevOP.default_list('OPTARGETS')
