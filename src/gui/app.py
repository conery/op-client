
# Top level application window of the OptiPass GUI

import logging
import panel as pn

from op import OP, OPResult, DevOP, OPServerError

from gui.tgmap import TGMap
from gui.regionbox import RegionBox
from gui.budgets import BudgetBox
from gui.targetbox import TargetBox
from gui.infobox import InfoBox
from gui.output import OutputPane, DownloadPane

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

        # self.project_menu = pn.widgets.Select(options=['Demo','Oregon'], width=150)
        # self.header.append(pn.Row(
        #     pn.layout.HSpacer(),
        #     self.project_menu
        # ))

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

        self.map_help_button = pn.widgets.Button(name='ℹ️', stylesheets = [help_button_style_sheet])
        self.map_help_button.on_click(self.map_help_cb)

        self.region_help_button = pn.widgets.Button(name='ℹ️', stylesheets = [help_button_style_sheet])
        self.region_help_button.on_click(self.region_help_cb)

        self.budget_help_button = pn.widgets.Button(name='ℹ️', stylesheets = [help_button_style_sheet])
        self.budget_help_button.on_click(self.budget_help_cb)

        self.target_help_button = pn.widgets.Button(name='ℹ️', stylesheets = [help_button_style_sheet])
        self.target_help_button.on_click(self.target_help_cb)

        self.climate_help_button = pn.widgets.Button(name='ℹ️', stylesheets = [help_button_style_sheet])
        self.climate_help_button.on_click(self.climate_help_cb)

        self.tab_height = int(self.map.graphic().height * 1.05)

        welcome_tab = pn.Column(
            self.section_head('Welcome'),
            pn.pane.HTML(OP.fetch_html_file('welcome.html')),
            height = self.tab_height,
            scroll = True,
        )

        help_tab = pn.Column(
            self.section_head('Instructions'),
            pn.pane.HTML(OP.fetch_html_file('help.html')),
            height = self.tab_height,
            scroll = True,
         )

        start_tab = pn.Column(
            self.section_head('Geographic Regions', self.region_help_button),
            self.region_boxes,
            
            self.section_head('Budgets', self.budget_help_button),
            self.budget_box,

            self.section_head('Targets', self.target_help_button),
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

        self.sidebar.append(pn.Row(self.map_pane, self.map_help_button))
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
        self.tabs[3] = ('Output', pn.Column(output, height=self.tab_height, scroll=True))
        self.tabs[4] = ('Download', pn.Column(DownloadPane(res), height=self.tab_height, scroll=True))

    def map_help_cb(self, _):
        """
        Callback function for the help button next to the map in the sidebar.
        """
        msg = pn.pane.HTML('''
        <p>When you move your mouse over the map the cursor will change to a "crosshairs" symbol and a set of buttons will appear below the map.
        Navigating with the map is similar to using Google maps or other online maps:</p>
        <ul>
            <li>Left-click and drag to pan (move left and right or up and down).</li>
            <li>If you want to zoom in and out, first click the magnifying glass button below the map; then you can zoom in and out using the scroll wheel on your mouse.</li>   
            <li>Click the refresh button to restore the map to its original size and location.</li>
        </ul>
        ''')
        self.tabs[0].append(pn.layout.FloatPanel(msg, name='Map Controls', contained=False, position='center', width=400))
    
    def region_help_cb(self, _):
        """
        Callback function for the help button next to the region box widget in the start tab.
        """
        msg = pn.pane.HTML('''
        <p>Select a region by clicking in the box to the left of an estuary name.</p>
        <p>Each time you click in a box the map will be updated to show the positions of the barriers that are in our database for the estuary.</p>
        <p>You must select at least one region before you run the optimizer.</p>
        ''')
        self.tabs[2].append(pn.layout.FloatPanel(msg, name='Geographic Regions', contained=False, position='center', width=400))
    
    def budget_help_cb(self, _):
        """
        Callback function for the help button next to the budget box widget in the start tab.
        """
        msg = pn.pane.HTML('''
        <p>There are three ways to specify the budgets used by the optimizer.</p>
        <H4>Basic</H4>
        <p>The simplest method is to specify an upper limit by moving the slider back and forth.  When you use this method, the optimizer will run 10 times, ending at the value you select with the slider.  For example, if you set the slider at $10M (the abbreviation for $10 million), the optimizer will make ROI curves based on budgets of $1M, $2M, <i>etc</i>, up to the maximum of $10M.</p>
        <p>Note that the slider is disabled until you select one or more regions.  That's because the maximum value depends on the costs of the gates in each region.
        For example, the total cost of all gates in the Coquille region is $11.8M.  Once you choose that region, you can move the budget slider
        left and right to pick a maximum budget for the optimizer to consider.
        <H4>Advanced</H4>
        <p>If you click on the Advanced tab in this section you will see ways to specify the budget interval and the number of budgets.</p>
        <p>You can use this method if you want more control over the layout of the ROI curves, for example you can include more points by increasing the number of budgets.</p>
        <H4>Fixed</H4>
        <p>If you know exactly how much money you have to spend you can enter that amount by clicking on the Fixed tab and entering the budget amount.</p>
        <p>The optimizer will run just once, using that budget.  The output will have tables showing the gates identified by the optimizer, but there will be no ROI curve.</p>
        <p>When entering values, you can write the full amount, with or without commas (<i>e.g.</i>11,500,000 or 11500000) or use the abbreviated form (11.5M).</p>
        ''')
        self.tabs[2].append(pn.layout.FloatPanel(msg, name='Budget Levels', contained=False, position='center', width=400))
    
    def target_help_cb(self, _):
        """
        Callback function for the help button next to the target box widget in the start tab.
        """
        msg = pn.pane.HTML('''
        <p>Click boxes next to one or more target names to have the optimizer include those targets in its calculations.</p>
        <p>The optimizer will create an ROI curve for each target selected. </p>
        <p>If more than one target is selected the optimizer will also generate an overall "net benefit" curve based on considering all targets at the same time.</p>
        ''')
        self.tabs[2].append(pn.layout.FloatPanel(msg, name='Targets', contained=False, position='center', width=400))
    
    def climate_help_cb(self, _):
        """
        Callback function for the help button next to the climate scenario checkbox in the start tab.
        """
        msg = pn.pane.HTML('''
        <p>By default the optimizer uses current water levels when computing potential benefits.  Click the button next to <b>Future</b> to have it use water levels expected due to climate change.</p>
        <p>The future scenario uses two projected water levels, both for the period to 2100. For fish habitat targets, the future water level is based on projected sea level rise of 5.0 feet.  For agriculture and infrastructure targets, the future water level is projected to be 7.2 feet, which includes sea level rise and the probabilities of extreme water levels causing flooding events.</p>
        ''')
        self.tabs[2].append(pn.layout.FloatPanel(msg, name='Targets', contained=False, position='center', width=400))