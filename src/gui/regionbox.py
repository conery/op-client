
# Widget for displaying names of geographic regions

import panel as pn

from op import OP
from .styles import *

class RegionBox(pn.Column):
    """
    The region box displays the names of each geographic region in the data set,
    with a checkbox next to the name.  
    
    When the user clicks on one of the checkboxes
    several actions are triggered:  the set of selected regions is updated, the
    budget widget is notified so it can update the maximum budget (based on the total
    cost of all barriers in the current selection), and the map is updated by zooming
    in to a level that contains only the barriers in the selected regions.
    """
    
    def __init__(self, map, budget):
        """
        Create the grid of checkboxes and set up the callback function.

        Arguments:
          map:  the TGMap object that will be updated when regions are selected
          budget:  the BudgetBox object to update when regions are selected
        """
        super(RegionBox, self).__init__(margin=(10,0,10,5))
        self.map = map
        self.budget_box = budget
        boxes = []
        for name in OP.region_names:
            box = pn.widgets.Checkbox(name=name, styles=box_styles, stylesheets=[box_style_sheet])
            box.param.watch(self.cb, ['value'])
            boxes.append(box)
        self.grid = pn.GridBox(*boxes, ncols=3)
        self.selected = set()
        self.external_cb = None
        self.append(self.grid)

    def cb(self, *events):
        """
        Callback function invoked when one of the checkboxes is clicked.  If the new state
        of the checkbox is 'selected' the region is added to the set of selected regions,
        otherwise it is removed.  After updating the set notify the map widget and any
        other widgets that have been registered as external callbacks.
        """
        for e in events:
            if e.type == 'changed':
                r = e.obj.name
                if e.new:
                    self.selected.add(r)
                else:
                    self.selected.remove(r)
                amount = sum(OP.total_cost[x] for x in self.selected)
                self.budget_box.set_budget_max(amount)
        self.map.display_regions(self.selected)
        # self.map.zoom(self.selected)
        if self.external_cb:
            self.external_cb()

    def selection(self) -> list[str]:
        """
        Return a list of the names of currently selected regions.
        """
        return self.selected
    
    def add_external_callback(self, f):
        """
        Save a reference to an external function to call when a region box is clicked.

        Arguments:
          f: aditional function to call when a checkbox is clicked
        """
        self.external_cb = f

