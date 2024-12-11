
# Top level application window of the OptiPass GUI

import logging
import panel as pn

from op import OP, DevOP
from gui.tgmap import TGMap
from gui.regionbox import RegionBox
from gui.budgets import BudgetBox
from gui.targetbox import TargetBox
from gui.infobox import InfoBox
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

        self.map = TGMap.init()
        self.map_pane = pn.Column(
            pn.panel(self.map.graphic())
        )

        self.budget_box = BudgetBox()
        self.region_boxes = RegionBox(self.map, self.budget_box)
        self.target_boxes = TargetBox()

        self.optimize_button = pn.widgets.Button(name='Run Optimizer', stylesheets=[button_style_sheet])
 
        self.info = InfoBox(self, self.run_optimizer)
        self.modal.append(self.info)

        welcome_tab = pn.Column(
            self.section_head('Welcome'),
            pn.panel("welcome message")
        )

        help_tab = pn.Column(
            self.section_head('Instructions'),
            pn.panel("instructions")
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
        budget_max, budget_delta = self.budget_box.values()
        targets = self.target_boxes.selection()

        if len(regions) == 0 or budget_max == 0 or len(targets) == 0:
            self.info.show_missing(regions, budget_max, targets)
            return
        
        if weights := self.target_boxes.weights():
            if not all([w.isdigit() and (1 <= int(w) <= 5) for w in weights]):
                self.info.show_invalid_weights(weights)
                return
            
        mapping = self.target_boxes.mapping()

        self.info.show_params(regions, budget_max, budget_delta, targets, weights, mapping)

    def run_optimizer(self, _):
        """
        Callback function invoked when the user clicks the Continue button after verifying
        the parameter options.

        Use the settings in the budget widgets to create the URL to pass to the server.
        """
        OP.run_optimizer(
            self.region_boxes.selection(),
            self.budget_box.values(),
            self.target_boxes.selection(),
            self.target_boxes.weights(),
            self.target_boxes.mapping(),
        )
