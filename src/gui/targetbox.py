
import panel as pn
from pathlib import Path

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

        if OP.mapping_name:
            lst = [s.capitalize() for s in OP.target_columns]
            label = OP.mapping_name.capitalize()
            self.mapping_buttons = pn.widgets.RadioBoxGroup(name=label, options=lst)
            mapping_box = pn.Column(
                pn.pane.HTML(f'<b>{label}<b>', align='start'),
                self.mapping_buttons,
            )
        else:
            self.mapping_buttons = None

        self.tabs = pn.Tabs(
            ('Basic', BasicTargetBox()),
            ('Weighted', WeightedTargetBox()),
        )
        row = pn.Row()
        row.append(self.tabs)
        if self.mapping_buttons:
            row.append(mapping_box)
        self.append(row)

    @staticmethod
    def make_layout(obj):
        """
        Read the target layout (size of grid, location of each target in the grid)
        """
        obj.layout = [s.split() for s in OP.target_layout]
        obj.nrows = len(obj.layout)
        obj.ncols = max(len(r) for r in obj.layout)

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
    
    def mapping(self):
        """
        If the targets have alternative column name mappings return the selected
        mapping name
        """
        return self.mapping_buttons.value.lower() if OP.mapping_name else None


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
        df = OP.target_frame.set_index('abbrev')
        TargetBox.make_layout(self)
        self.grid = pn.GridBox(nrows = self.nrows, ncols = self.ncols)
        for row in self.layout:
            for t in row:
                s = df.loc[t].long
                b = pn.widgets.Checkbox(name=s, styles=box_styles, stylesheets=[box_style_sheet], tags=[t])
                self.grid.append(b)
        self.append(self.grid)

    def selection(self) -> list[str]:
        """
        Return a list of IDs of selected targets.
        """
        return [b.tags[0] for b in self.grid.objects if b.value]
    
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
        df = OP.target_frame.set_index('abbrev')
        TargetBox.make_layout(self)
        self.grid = pn.GridBox(nrows = self.nrows, ncols = self.ncols)
        for row in self.layout:
            for t in row:
                s = df.loc[t].long
                w = pn.Row()
                w.append(pn.widgets.TextInput(name='', placeholder='', width=25, align='center', stylesheets=[input_style_sheet], tags=[t]))
                w.append(pn.pane.HTML(s))
                self.grid.append(w)
        self.append(self.grid)

    def selection(self) -> list[str]:
        """
        Return a list of IDs of selected targets.
        """
        return [w[0].tags[0] for w in self.grid.objects if w[0].value]

    def weights(self) -> list[str]:
        """
        Return the text content of each non-empty text entry box.
        """
        return [w[0].value for w in self.grid.objects if w[0].value]
    
