#
# Abstract interface to the OptiPass server
#

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

        Connect to the server and get a list of project (data set) names.
        If `project` is not in the list raise an exception, otherwise save
        the URL and project name.

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

