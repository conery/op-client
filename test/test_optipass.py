#
# Unit tests for functions in the optipass module
#

# Contortions to go through in order to import a module from a
# folder that has a hyphen in its name

from importlib import import_module

op = import_module("src.op","ip-client")
OP = op.OP

# These tests use PyTest.  The client needs to fetch data from a
# REST server -- use the `responses` library to generate mock data

import pytest
import responses

import os
from pathlib import Path

@pytest.fixture
def mapinfo():
    return Path(os.path.dirname(__file__)) / 'fixtures' / 'mapinfo.json'

@pytest.fixture
def barriers():
    return Path(os.path.dirname(__file__)) / 'fixtures' / 'barriers.csv'


@responses.activate
def test_setup(barriers, mapinfo):
    '''
    Test the attributes saved by the setup method.
    '''
    server = 'http://localhost:8000'

    path_to_projects = f'{server}/projects'
    responses.get(path_to_projects, json = ["demo"])

    with open(barriers) as f:
        path_to_barriers = f'{server}/barriers/demo'
        responses.get(path_to_barriers, json = {"project":"demo", "barriers":f.read()})

    with open(mapinfo) as f:
        path_to_mapinfo = f'{server}/mapinfo/demo'
        responses.get(path_to_mapinfo, json = {"project":"demo", "mapinfo":f.read()})

    OP.setup(server, 'demo', 1)

    assert OP.server_url == 'http://localhost:8000'
    assert OP.project_name == 'demo'
    assert OP.initial_tab == 1

    assert OP.region_names == ['Red Fork','Trident']

    assert len(OP.barrier_frame) == 6
    assert len(OP.barrier_frame.columns) == 9
    assert round(OP.barrier_frame.cost.sum()) == 590000

    assert OP.mapinfo['map_type'] == 'StaticMap'
    assert OP.mapinfo['map_file'] == 'Riverlands.png'
    assert OP.mapinfo['map_title'] == 'The Riverlands'

    assert sorted(OP.total_cost.keys()) == OP.region_names
    assert round(sum(OP.total_cost.values())) ==  round(OP.barrier_frame.cost.sum())

    with pytest.raises(AttributeError) as err:
        OP.initial_tab = 2
    assert 'no setter' in str(err)
