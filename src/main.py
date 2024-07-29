
#
# GUI client for the Tidegate Optimization Tool.
#
# John Conery
# University of Oregon
# (conery@uoregon.edu)
#
# This client uses Panel to display a GUI that has widgets for 
# optimization parameters (region names, budget levels, etc).
# It connects to an OptiPass server to fetch tide gate data and
# run OptiPass.

import argparse

import panel as pn

from gui.app import TideGatesApp

def init_cli():
    """
    Use argparse to create the command line API.

    Returns:
        a Namespace object with values of the command line arguments. 
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('--server', metavar='URL', help='web address of the OptiPass server')
    parser.add_argument('--project', metavar='X', help='name of dataset to use')
    parser.add_argument('--port', metavar='N', type=int, default=5006, help='local port for the Panel server')

    return parser.parse_args()

def make_app():
    """
    Instantiate the top level widget.

    Returns:
        a TideGatesApp object
    """
    return TideGatesApp(
        title='Tide Gate Optimization', 
        sidebar_width=450
    )

def start_app(port):
    """
    Launch the Bokeh server.
    """
    pn.extension(design='native')
    pn.serve( 
        {'tidegates': make_app},
        port = port,
        admin = True,
        verbose = True,
        autoreload = True,
        websocket_origin= '*',
    )

if __name__ == '__main__':
    args = init_cli()
    start_app(args.port)

