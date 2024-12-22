
# Top level application window of the OptiPass GUI

import logging
import panel as pn

from op import OP, OPResult, DevOP, OPServerError

from gui.tgmap import TGMap
from gui.regionbox import RegionBox
from gui.budgets import BudgetBox
from gui.targetbox import TargetBox
from gui.infobox import InfoBox
from gui.output import OutputPane

from .styles import *

pn.extension('gridstack', 'tabulator', 'floatpanel')

class TideGatesApp(pn.template.BootstrapTemplate):
    """
    The web application is based on the Bootstrap template provided by Panel.
    It displays a map (an instance of the TGMap class) in the sidebar.  The main content
    area has a Tabs widget with five tabs: a welcome message, a help page, the main page
    (described below) and two tabs for displaying outputs.

    The application also displays several small help buttons next to the main widgets.
    Clicking one of these buttons brings up a floating window with information about
    the widget.

    The main tab (labeled "Start") displays the widgets that allow the user to specify
    optimization parameters:  region names, budget levels, and restoration targets.  It
    also has a Run button.  When the user clicks this button the callback function makes
    sure the necessary parameters have been defined and then uses the template's modal
    dialog area.  Clicking the "OK" button in that dialog invokes another callback, 
    defined here, that runs the optimizer.
    """

    def __init__(self, **params):
        """
        Initialize the application.

        Arguments:
          params:  runtime options passed to the parent class constructor
        """
        super(TideGatesApp, self).__init__(**params)

        # self.header.append(pn.pane.HTML('<p>Hello</p>'))
        self.header.append(pn.widgets.Select(options=['Demo','Oregon']))

        self.map = TGMap.init()
        self.map_pane = pn.Column(
            pn.panel(self.map.graphic())
        )

        self.budget_box = BudgetBox()
        self.region_boxes = RegionBox(self.map, self.budget_box)
        self.target_boxes = TargetBox()

        self.optimize_button = pn.widgets.Button(name='Run Optimizer', stylesheets=[button_style_sheet])
 
        self.info = InfoBox(self, self.run_cb)
        self.modal.append(self.info)

        welcome_tab = pn.Column(
            self.section_head('Welcome'),
            pn.pane.HTML(OP.fetch_html_file('welcome.html')),
        )

        help_tab = pn.Column(
            self.section_head('Instructions'),
            pn.pane.HTML(OP.fetch_html_file('help1.html')),
            pn.pane.PNG(OP.fetch_image('ROI.png'), width=400),
            pn.pane.HTML(OP.fetch_html_file('help2.html')),
        )

        start_tab = pn.Column(
            self.section_head('Geographic Regions'),
            self.region_boxes,
            
            self.section_head('Budgets'),
            self.budget_box,

            self.section_head('Targets'),
            self.target_boxes,

            self.optimize_button,
        )

        output_tab = pn.Column(
            self.section_head('Nothing to See Yet'),
            pn.pane.HTML('<p>After running the optimizer this tab will show the results.</p>')
        )

        download_tab = pn.Column(
            self.section_head('Nothing to Download Yet'),
            pn.pane.HTML('<p>After running the optimizer use this tab to save the results.</p>')        )

        self.tabs = pn.Tabs(
            ('Home', welcome_tab),
            ('Help', help_tab),
            ('Start', start_tab),
            ('Output', output_tab),
            ('Download', download_tab),
            stylesheets=[tab_style_sheet],
            # tabs_location='left',
            # sizing_mode = 'fixed',
            # width=800,
            # height=700,
        )

        self.sidebar.append(pn.Row(self.map_pane))
        self.main.append(self.tabs)

        self.optimize_button.on_click(self.validate_settings)

        for r in DevOP.default_regions():
            self.region_boxes.check(r)
        self.budget_box.set_value(DevOP.default_budget())
        self.target_boxes.set_selection(DevOP.default_targets())
        if DevOP.results_dir():
            self.run_optimizer()
        self.tabs.active = OP.initial_tab
    
    def section_head(self, s, b = None):
        """
        Create an HTML header for one of the sections in the Start tab.
        """
        header = pn.pane.HTML(f'<h3>{s}</h3>', styles=header_styles)
        return header if b is None else pn.Row(header, b)

    def validate_settings(self, _):
        """
        Callback function invoked when the user clicks the Run Optimizer button.
        """
        regions = self.region_boxes.selection()
        budget = self.budget_box.defined()
        targets = self.target_boxes.selection()

        if len(regions) == 0 or (not budget) or len(targets) == 0:
            self.info.show_missing(regions, budget, targets)
            return
        
        if weights := self.target_boxes.weights():
            if not all([w.isdigit() and (1 <= int(w) <= 5) for w in weights]):
                self.info.show_invalid_weights(weights)
                return
            
        mapping = self.target_boxes.mapping()

        self.info.show_params(regions, self.budget_box.values(), targets, weights, mapping)

    def run_cb(self, _):
        """
        Callback function invoked when the user clicks the Continue button after verifying
        the parameter options.

        Wrap the call to the function that runs the optimizer in code that shows the loading
        icon and opens a message when the function returns.
        """
        try:
            self.close_modal()
            self.main[0].loading = True
            self.run_optimizer()
            self.main[0].loading = False
            self.info.show_success()
        except OPServerError as err:
            self.main[0].loading = False
            self.info.show_fail(err)

    def run_optimizer(self):
        """
        Use the settings in the widgets to run OptiPass, save the results
        in the output tab.
        """
        params = [
            self.region_boxes.selection(),
            self.budget_box.values(),
            self.target_boxes.selection(),
            self.target_boxes.weights(),
            self.target_boxes.mapping(),
        ]

        resp = OP.run_optimizer(*params)

        params += resp
        res = OPResult(*params)
        output = OutputPane(res, self.map)

        self.region_boxes.add_external_callback(output.hide_dots)
        self.tabs[3] = ('Output', output)
        # self.tabs[4] = ('Download', DownloadPane(output))

