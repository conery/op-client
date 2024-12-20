from bokeh.models.widgets.tables import NumberFormatter
import logging
from op import OP
import pandas as pd
import panel as pn
from .styles import *

class OutputPane(pn.Column):
    """
    After OptiPass has completed the last optimization run the GUI creates
    an instance of this class and saves it in the Output tab of the top 
    level display.
    """

    def __init__(self, op):
        """
        Format the output from OptiPass.
        The first part of the panel has a set of ROI curves
        (displayed in a tab widget showing one figure at a time), the second
        part has tables showing data about barriers included in solutions.

        Arguments:
          op: an OPResult object with the optimization parameters and results
         """
        super(OutputPane, self).__init__()

        self.append(pn.pane.HTML('<h3>Optimization Complete</h3>', styles=header_styles))
        self.append(self._make_title(op))

        if op.bcount > 1:
            self.append(pn.pane.HTML('<h3>ROI Curves</h3>'))
            self.append(self._make_figures_tab(op))

        self.append(pn.pane.HTML('<h3>Budget Summary</h3>'))
        self.gate_count = op.summary.gates.apply(len).sum()
        if self.gate_count == 0:
            self.append(pn.pane.HTML('<i>No barriers selected -- consider increasing the budget</i>'))
        else:
            self.append(self._make_budget_table(op))
            self.append(pn.Accordion(
                ('Barrier Details', self._make_gate_table(op)),
                stylesheets = [accordion_style_sheet],
            ))

    def _make_title(self, op):
        """
        The top section of the output pane is a title showing the optimization parameters.
        """
        tnames = [OP.target_frame.loc[t].short for t in op.targets]
        if op.weights:
            tnames = [f'{tnames[i]} ⨉ {op.weights[i]}' for i in range(len(tnames))]

        title = f"<p><b>Regions:</b> {', '.join(op.regions)};"
        title += f" <b>Targets:</b> {', '.join(tnames)};"
        if s := OP.mapping_name:
            title += f" <b>{s.capitalize()}:</b> {op.mapping};"
        if op.bcount > 1:
            bmax = op.binc * op.bcount
            smin = OP.format_budget_amount(op.binc)
            smax = OP.format_budget_amount(bmax)
            title += f" <b>Budgets:</b> {smin} to {smax}</p>"
        else:
            b = OP.format_budget_amount(op.bmin),
            title += " <b>Budget:</b> {b}</p>"
        return pn.pane.HTML(title)
            
    def _make_figures_tab(self, op):
        """
        Create a Tabs object with one tab for each ROI curve.
        """
        tabs = pn.Tabs(
            tabs_location='left',
            stylesheets = [tab_style_sheet],
        )
        op.make_roi_curves()
        for p in op.display_figures:
            tabs.append(p)
        return tabs
    
    def _make_budget_table(self, op):
        """
        Make the table of benefits for each budget.  Attach
        a callback function that is called when the user clicks on a row
        in the table (the callback updates the map to show gates used in a
        solution).
        """
        df = op.budget_table()
        formatters = { col: NumberFormatter(format='0.0', text_align='center') for col in df.columns }
        formatters['Budget'] = {'type': 'money', 'symbol': '$', 'precision': 0}
        alignment = { 
            'Budget': 'right',
            'Net Gain': 'center',
            '# Barriers': 'center'
        }

        table = pn.widgets.Tabulator(
            df,
            show_index = False,
            hidden_columns = ['gates'],
            editors = { c: None for c in df.columns },
            text_align = alignment,
            header_align = {c: 'center' for c in df.columns},
            formatters = formatters,
            selectable = True,
            configuration = {'columnDefaults': {'headerSort': False}},
        )
        table.on_click(self.budget_table_cb)
        self.budget_table = df
        return table

    def _make_gate_table(self, op):
        """
        Make a table showing details about gates used in solutions.
        """
        formatters = { }
        alignment = { }
        df = op.gate_table()
        print(df)

        hidden = ['Count']
        # for col in df.columns:
        #     if col.startswith('$') or col in ['Primary','Dominant']:
        #         formatters[col] = {'type': 'tickCross', 'crossElement': ''}
        #         alignment[col] = 'center'
        #     elif col.endswith('hab'):
        #         c = col.replace('_hab','')
        #         formatters[c] = NumberFormatter(format='0.0', text_align='center')
        #         # alignment[c] = 'center'
        #     elif col.endswith('tude'):
        #         formatters[col] = NumberFormatter(format='0.00', text_align='center')
        #         # alignment[col] = 'right'
        #     elif col.endswith('gain'):
        #         hidden.append(col)
        #     elif col == 'Cost':
        #         formatters[col] = {'type': 'money', 'symbol': '$', 'precision': 0}
        #         alignment[col] = 'right'
        # colnames = [c.replace('_hab','') for c in df.columns]
        # if self.op.weighted:
        #     for i, t in enumerate(self.op.targets):
        #         if t.short not in colnames:             # shouldn't happen, but just in case...
        #             continue
        #         j = colnames.index(t.short)
        #         colnames[j] += f'⨉{self.op.weights[i]}'
        #         formatters[colnames[j]] = NumberFormatter(format='0.0', text_align='center')
        # df.columns = colnames

        table = pn.widgets.Tabulator(
            df, 
            show_index=False, 
            frozen_columns=['ID'],
            hidden_columns=hidden,
            formatters=formatters,
            text_align=alignment,
            configuration={'columnDefaults': {'headerSort': False}},
            header_align={c: 'center' for c in df.columns},
            selectable = False,
        )
        table.disabled = True
        self.gate_table = df
        return table
    
    def make_dots(self, plot):
        """
        Called after the output panel is initialized, make a set of glyphs to display
        for each budget level.
        """
        if hasattr(self, 'budget_table'):
            self.selected_row = None
            self.dots = []
            for row in self.budget_table.itertuples():
                df = self.bf.map_info[self.bf.data.BARID.isin(row.gates)]
                c = plot.circle_dot('x', 'y', size=12, line_color='blue', fill_color='white', source=df)
                # c = plot.star_dot('x', 'y', size=20, line_color='blue', fill_color='white', source=df)
                # c = plot.star('x', 'y', size=12, color='blue', source=df)
                # c = plot.hex('x', 'y', size=12, color='green', source=df)
                c.visible = False
                self.dots.append(c)

    def budget_table_cb(self, e):
        """
        The callback function invoked when the user clicks a row in the budget table.
        Use the event to figure out which row was clicked.  Hide any dots that were displayed
        previously, then make the dots for the selected row visible.
        """
        if n := self.selected_row:
            self.dots[n].visible = False
        self.selected_row = e.row
        self.dots[self.selected_row].visible = True

    def hide_dots(self):
        """
        Callback function invoked when users click on a region name in the start panel to hide
        any dots that might be on the map.
        """
        if self.selected_row:
            self.dots[self.selected_row].visible = False
        self.selected_row = None
