#
# Abstract interface to the OptiPass server
#

from io import StringIO
import json
import pandas as pd
import requests

class OP:
    """
    Interface to an OptiPass server.  The module consists of a set of
    static methods that manage a single connection (i.e. it's basically
    a singleton object).  One set of methods fetch project data such as
    barrier information needed to draw the map or target names to fill
    to fill out the target widget.  Others provide an API for running
    OptiPass and collecting results.
    """

    server_url = None
    project_name = None

    @staticmethod
    def setup(server: str, project: str):
        '''
        Initialize the connection to the OptiPass server.  This method
        must be called first.

        Connect to the server and get a list of project (data set) names
        and a description of the map to display in the sidebar.

        If `project` is not in the list raise an exception, otherwise save
        the URL, project name, and map info.

        Arguments:
          server: the URL of an OptiPass REST server
          project: the name of a data set on the server
        '''
        req = f'{server}/projects'
        resp = requests.get(req)
        if project not in resp.json():
            raise ValueError(f'unknown project: {project}')
        OP.server_url = server
        OP.project_name = project

        req = f'{server}/mapinfo/{project}'
        resp = requests.get(req)
        OP.mapinfo = json.loads(resp.json()['mapinfo'])

    @staticmethod
    def fetch_barriers():
        req = f'{OP.server_url}/barriers/{OP.project_name}'
        resp = requests.get(req)
        buf = StringIO(resp.json()['barriers'])
        return pd.read_csv(buf)

    @staticmethod
    def url_for_figure(name):
        return f'{OP.server_url}/image/{name}'
    
    @staticmethod
    def region_names():
        req = f'{OP.server_url}/regions/{OP.project_name}'
        resp = requests.get(req)
        return resp.json()['regions']
