#
# Abstract interface to the OptiPass server
#

from io import StringIO
import json
import logging
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
        # if project not in resp.json():
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

