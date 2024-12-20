
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
import logging
import panel as pn
import requests

from rich.logging import RichHandler

from gui.app import TideGatesApp
from op import OP, OPServerError

args = None

def init_cli():
    """
    Use argparse to create the command line API.  After parsing the
    arguments save them in a global variable named args.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('--log', metavar='X', choices=['quiet','info','debug'])
    parser.add_argument('--server', metavar='S', default='https://optimizationtool.oregontidegates.org/op', help='URL of the OptiPass server')
    parser.add_argument('--project', metavar='X', required=True, help='name of dataset to use')
    parser.add_argument('--port', metavar='N', type=int, default=5006, help='local port for the Panel server')
    parser.add_argument('--tab', metavar='N', type=int, default=0, help='initial tab to display in GUI')

    global args
    args = parser.parse_args()

def setup_logging():
    """
    Configure the logging modile.
    """
    match args.log:
        case 'info':
            level = logging.INFO
        case 'debug':
            level = logging.DEBUG
        case _:
            level = logging.WARNING
    logging.basicConfig(
        level=level,
        style='{',
        format='{relativeCreated:4.0f} msec: {message}',
        handlers = [RichHandler(markup=True, rich_tracebacks=True)],
    )

def make_app():
    """
    Instantiate the top level widget.

    Returns:
        a TideGatesApp object
    """
    return TideGatesApp(
        title='Tide Gate Optimization', 
        sidebar_width=450,
    )

def start_app(port):
    """
    Launch the Bokeh server.
    """
    pn.extension(design='native')
    pn.serve( 
        {'tidegates': make_app},
        port = port,
        verbose = True,
        autoreload = True,
        websocket_origin= '*',
    )

if __name__ == '__main__':
    init_cli()
    setup_logging()
    try:
        OP.setup(args.server, args.project, args.tab)
        start_app(args.port)
    except requests.exceptions.ConnectionError as err:
        logging.error(f'failed to connect to {args.server}')
    except OPServerError as err:
        logging.error(f'op-server error: {err}')
    except ValueError as err:
        logging.error(err)
    except Exception as err:
        logging.exception(err)
    finally:
        exit(1)

