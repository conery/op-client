
# Top level application window of the OptiPass GUI

import panel as pn

from op import OP
from gui.tgmap import TGMap
from gui.regionbox import RegionBox
from gui.budgets import BudgetBox
from gui.targetbox import TargetBox
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
        # self.target_boxes = TargetBox()
        self.target_boxes = pn.panel('Targets')
        self.climate_group = pn.panel("Climate")
 
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
            sizing_mode = 'fixed',
            width=800,
            # height=700,
        )
        self.tabs.active = OP.initial_tab

        self.sidebar.append(pn.Row(self.map_pane))
        self.main.append(self.tabs)
      

    def section_head(self, s, b = None):
        """
        Create an HTML header for one of the sections in the Start tab.
        """
        header = pn.pane.HTML(f'<h3>{s}</h3>', styles=header_styles)
        return header if b is None else pn.Row(header, b)
