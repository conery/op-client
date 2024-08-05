
import panel as pn

from op import OP
from .styles import *

class TargetBox(pn.Column):
    """
    The restoration targets are shown in a matrix with a selection widget
    next to each target name.  The TargetBox widget has two tabs showing
    different types of selection widgets, either simple checkboxes (shown
    by a BasicTargetBox) or text entry widgets (shown by WeightedTargetBox).
    """

    def __init__(self):
        super(TargetBox, self).__init__(margin=(10,0,10,5))
        self.tabs = pn.Tabs(
            ('Basic', BasicTargetBox()),
            ('Weighted', WeightedTargetBox()),
        )
        self.append(self.tabs)

    def selection(self) -> list[str]:
        """
        Get a list of IDs of selected targets from the current target widget.
        """
        return self.tabs[self.tabs.active].selection()
    
    def weights(self):
        """
        Get target weights from the current target widget.
        """
        return self.tabs[self.tabs.active].weights()


class BasicTargetBox(pn.Column):
    """
    The BasicTargetBox widget displays a checkbox next to each target name.
    """

    def __init__(self):
        """
        Make the grid of checkboxes.  The IDs and descriptions of targets are
        fetched by calling the make_layout function in the Target class.
        """
        super(BasicTargetBox, self).__init__(margin=(10,0,10,5))
        self.grid = pn.GridBox(ncols=2)
        self.boxes = { }
        for row in make_layout():
            lst = [ ]
            for t in row:
                b = pn.widgets.Checkbox(name=t, styles=box_styles, stylesheets=[box_style_sheet])
                lst.append(b)
                self.boxes[t] = b
            self.grid.objects.extend(lst)
        self.append(self.grid)

    def selection(self) -> list[str]:
        """
        Return a list of IDs of selected targets.
        """
        return [t for t in self.boxes if self.boxes[t].value ]
    
    def weights(self):
        """
        There are no weights (all targets considered equally) so return an empty list.
        """
        return []
    
class WeightedTargetBox(pn.Column):
    """
    A WeightedTargetBox shows a text entry widget next to each target to allow
    users to enter a numeric weight for the target.
    """

    def __init__(self):
        """
        Make the grid of text entry widgets.  The IDs and descriptions of targets are
        fetched by calling the make_layout function in the Target class.
        """
        super(WeightedTargetBox, self).__init__(margin=(10,0,10,5))
        self.grid = pn.GridBox(ncols=2)
        for tnames in make_layout():
            for t in tnames:
                w = pn.Row()
                w.append(pn.widgets.TextInput(name='', placeholder='', width=25, stylesheets=[input_style_sheet]))
                w.append(t)
                self.grid.objects.append(w)
        self.append(self.grid)

    def selection(self) -> list[str]:
        """
        Return a list of IDs of selected targets.
        """
        return [w[1].object for w in self.grid.objects if w[0].value]

    def weights(self) -> list[str]:
        """
        Return the text content of each non-empty text entry box.
        """
        return [w[0].value for w in self.grid.objects if w[0].value]
    