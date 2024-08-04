#
# Abstract interface to the OptiPass server
#

from io import StringIO
import json
import pandas as pd
import requests

class MetaOP(type):
    """
    This metaclass creates the API for the OP class.  It defines read-only
    attributes that can be accessed but not written from outside the OP module.
    The values of the attributes can only be set when the setup method is
    called.
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
        if project not in resp.json():
            raise ValueError(f'unknown project: {project}')
        cls._server_url = server
        cls._project_name = project

        req = f'{server}/mapinfo/{project}'
        resp = requests.get(req)
        cls._mapinfo = json.loads(resp.json()['mapinfo'])

        req = f'{server}/barriers/{project}'
        resp = requests.get(req)
        buf = StringIO(resp.json()['barriers'])
        cls._barrier_frame = pd.read_csv(buf)

        total_cost = cls._barrier_frame[['region','cost']].groupby('region').sum()
        cls._region_names = sorted(list(total_cost.index))
        cls._total_cost = { r[0]: r[1].cost for r in total_cost.iterrows() }

        cls._initial_tab = tab

class OP(metaclass=MetaOP):
    """
    Interface to an OptiPass server.  The module consists of a set of
    static methods that manage a single connection (i.e. it's basically
    a singleton object).  One set of methods fetch project data such as
    barrier information needed to draw the map or target names to fill
    to fill out the target widget.  Others provide an API for running
    OptiPass and collecting results.
    """

    @staticmethod
    def projects():
        req = 'http://localhost:8000/projects'
        resp = requests.get(req)
        return resp.json()

