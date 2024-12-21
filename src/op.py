#
# Abstract interface to the OptiPass server
#

from io import StringIO
import json
import logging
import os
import pandas as pd
import requests

from bokeh.plotting import figure
from bokeh.models import NumeralTickFormatter, HoverTool, Title

import matplotlib.pyplot as plt

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
        logging.info(f'Connecting to {server}')
        
        req = f'{server}/projects'
        logging.info(f'request: {req}')
        resp = requests.get(req)
        if resp.status_code == 502:
            raise requests.exceptions.ConnectionError()
        elif resp.status_code != 200:
            raise OPServerError(resp)
        elif project not in resp.json():
            raise ValueError(f'unknown project: {project}')
        cls._server_url = server
        cls._project_name = project

        req = f'{server}/targets/{project}'
        resp = requests.get(req)
        if resp.status_code != 200:
            raise OPServerError(resp)
        dct = resp.json()
        buf = StringIO(dct['targets'])
        cls._target_frame = pd.read_csv(buf).set_index('abbrev')
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
        cls._barrier_frame = pd.read_csv(buf).set_index('ID')

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
            budgets: a tuple with budget settings (start, increment, count)
            targets: a list of IDs of targets
            weights: a list of target weights
            mapping: the name of a column mapping file for targets

        Returns:
            summary: data frame with one row per budget level
            matrix:  data frame with one row per barrier
        '''
        req = f'{OP.server_url}/optipass/{OP.project_name}'
        args = {
            'regions': regions,
            'budgets': budgets,
            'targets': targets,
            'weights': weights or None,
            'mapping': [OP.mapping_name,mapping],
        }
        if token := DevOP.results_dir():
            args['tempdir'] = token

        resp = requests.get(req, args)
        if resp.status_code != 200:
            raise OPServerError(resp)
        
        dct = resp.json()
        buf = StringIO(dct['summary'])
        summary = pd.read_csv(buf)
        buf = StringIO(dct['matrix'])
        matrix = pd.read_csv(buf).set_index('ID')

        return summary, matrix
    
class OPResult:
    """
    Create an instance of this class each time the server returns a
    set of results from an optimization run.

    Pass the constructor the dictionaries returned by the server and
    the widget settings (region names, budget levels, target selection)
    so it can create plots and output tables.
    """

    def __init__(self, regions, budgets, targets, weights, mapping, summary, matrix):
        self.summary = pd.DataFrame(summary)
        self.matrix = pd.DataFrame(matrix)
        self.regions = regions
        self.bmin, self.binc, self.bcount = budgets
        self.targets = targets
        self.weights = weights
        self.mapping = mapping
        self.display_figures = []
        self.download_figures = []

        # The 'gates' column is a string, need to convert it to a list
        self.summary.gates = summary.gates.map(lambda s: json.loads(s.replace("'",'"')))

    def make_roi_curves(self):
        """
        Generate ROI plots based on computed benefits.
        """

        climate = None

        subtitle = 'Region: ' if len(self.regions) == 1 else 'Regions: '
        subtitle +=  ', '.join(self.regions)

        for i, t in enumerate(self.targets):
            target = OP.target_frame.loc[t]
            title = target.long
            if target.infra:
                title += f' ({self.mapping} {OP.mapping_name})'
            f = self.bokeh_figure(self.summary.budget, self.summary[target.name], title, subtitle, target.label)
            self.display_figures.append((target.short, f))
            f = self.pyplot_figure(self.summary.budget, self.summary[target.name], title, subtitle, target.label)
            self.download_figures.append((target.short, f))

        if len(self.targets) > 1:
            title = 'Combined Potential Benefit'
            if climate:
                title += f' ({OP.mapping} {OP.mapping_name})'
            if self.weights:
                subtitle += '\nTargets:'
                for i, t in enumerate(self.targets):
                    target = OP.target_frame.loc[t]
                    subtitle += f' {target.short} ⨉ {int(self.weights[i])}'
            f = self.bokeh_figure(self.summary.budget, self.summary.netgain, title, subtitle, 'Weighted Net Gain')
            self.display_figures.insert(0, ('Net', f))
            f = self.pyplot_figure(self.summary.budget, self.summary.netgain, title, subtitle, 'Weighted Net Gain')
            self.download_figures.insert(0, ('Net', f))

    def bokeh_figure(self, x, y, title, subtitle, axis_label):
        H = 400
        W = 400
        LW = 2
        D = 10

        f = figure(
            # title=title, 
            x_axis_label='Budget', 
            y_axis_label=axis_label,
            width=W,
            height=H,
            tools = [HoverTool(mode='vline')],
            tooltips = 'Budget @x{$0.0a}, Benefit @y{0.0}',
        )
        f.line(x, y, line_width=LW)
        f.circle(x, y, fill_color='white', size=D)
        f.add_layout(Title(text=subtitle, text_font_style='italic'), 'above')
        f.add_layout(Title(text=title), 'above')
        f.xaxis.formatter = NumeralTickFormatter(format='$0.0a')
        f.toolbar_location = None

        return f
    
    def pyplot_figure(self, x, y, title, subtitle, axis_label):

        def tick_fmt(n, x):
            return OP.format_budget_amount(n)

        LC = '#3c76af'
        H = 4
        W = 4
        LW = 1.25
        D = 7

        fig, ax = plt.subplots(figsize=(H,W))
        fig.suptitle(title, fontsize=11, fontweight='bold')

        ax.grid(linestyle='--', linewidth=0.5)
        ax.plot(x, y, color=LC, linewidth=LW)
        ax.plot(x, y, 'o', markerfacecolor='white', markeredgecolor=LC, markersize=D, markeredgewidth=0.75)
        ax.xaxis.set_major_formatter(tick_fmt)
        ax.set_title(subtitle, loc='left', fontstyle='oblique', fontsize= 10)
        ax.set_ylabel(axis_label, style='italic', fontsize=10)
        return fig
    
    def budget_table(self):
        """
        Make a table that has one column for each budget level, showing
        which barriers were included in the solution for that level. 
        """
        df = self.summary[['budget','netgain']]
        colnames = ['Budget', 'Net Gain']
        df = pd.concat([
            df,
            pd.Series(self.summary.gates.apply(len))
        ], axis=1)
        colnames.append('# Barriers')
        for i, t in enumerate(self.targets):
            target = OP.target_frame.loc[t]
            if target.name in self.summary.columns:
                df = pd.concat([df, self.summary[target.name]], axis=1)
                col = target.short
                # if self.weights:
                #     col += f'⨉{self.weights[i]}'
                colnames.append(col)
        df.columns = colnames
        return df
    
    def gate_table(self):
        """
        Make a table that has one row per gate with columns that are relevant
        to the output display
        """
        filtered = OP.barrier_frame[OP.barrier_frame.region.isin(self.regions)]

        col1 = [c for c in ['region','cost','DSID','type'] if c in filtered.columns]
        budget_cols = [c for c in self.matrix.columns if c.isnumeric() and c > '0']
        target_cols = [c for c in self.matrix.columns if len(c) == 2]
        col2 = [c for c in ['primary','dominant','X','Y'] if c in filtered.columns]

        df = pd.concat([
            filtered[col1],
            self.matrix[budget_cols],
            self.matrix['count'],
            self.matrix[target_cols],
            filtered[col2]
        ], axis=1)

        df = df[df['count'] > 0].sort_values(by='count', ascending=False).fillna('-')
        df.columns = [s.capitalize() if s in ['region','cost','type','primary','dominant'] else s for s in df.columns]

        return df


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

    @staticmethod
    def results_dir():
        return os.getenv('OPTMPDIR')
