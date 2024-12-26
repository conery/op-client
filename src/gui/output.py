from bokeh.models.widgets.tables import NumberFormatter
from bokeh.io import save as savehtml
from op import OP
import pandas as pd
import panel as pn
from pathlib import Path
from shutil import make_archive, rmtree

from .styles import *

class OutputPane(pn.Column):
    """
    After OptiPass has completed the last optimization run the GUI creates
    an instance of this class and saves it in the Output tab of the top 
    level display.
    """

    def __init__(self, op, tgmap):
        """
        Format the output from OptiPass.
        The first part of the panel has a set of ROI curves
        (displayed in a tab widget showing one figure at a time), the second
        part has tables showing data about barriers included in solutions.

        Arguments:
          op: an OPResult object with the optimization parameters and results
         """
        super(OutputPane, self).__init__()

        self.append(pn.pane.HTML('<h3>Optimization Results</h3>', styles=header_styles))
        self.append(self._make_title(op))

        if op.bcount > 1:
            self.append(pn.pane.HTML('<h3>ROI Curves</h3>'))
            self.append(self._make_figures_tab(op))

        self.append(pn.pane.HTML('<h3>Budget Summary</h3>'))
        self.gate_count = op.summary.gates.apply(len).sum()
        if self.gate_count == 0:
            self.append(pn.pane.HTML('<i>No barriers selected -- consider increasing the budget</i>'))
        else:
            self.append(self._make_budget_table(op, tgmap))
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
            stylesheets = [output_tab_style_sheet],
        )
        op.make_roi_curves()
        for p in op.display_figures:
            tabs.append(p)
        return tabs
    
    def _make_budget_table(self, op, tgmap):
        """
        Make the table of benefits for each budget.  Attach
        a callback function that is called when the user clicks on a row
        in the table (the callback updates the map to show gates used in a
        solution).
        """
        df = op.budget_table()
        formatters = { col: NumberFormatter(format='0.0', text_align='center') for col in df.columns }
        formatters['Budget'] = {'type': 'money', 'symbol': '$', 'precision': 0}
        formatters['# Barriers'] = NumberFormatter(format='0', text_align='center')
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
        self.budget_table = df
        self.make_dots(table, op, tgmap)
        table.on_click(self.budget_table_cb)

        return table

    def _make_gate_table(self, op):
        """
        Make a table showing details about gates used in solutions.
        """
        formatters = { }
        alignment = { }
        df = op.gate_table()

        df.columns = [OP.format_budget_amount(int(s)) if s.isdigit() else s for s in df.columns]

        for col in df.columns:
            if col.startswith('$') or col in ['Primary','Dominant']:
                formatters[col] = {'type': 'tickCross', 'crossElement': ''}
                alignment[col] = 'center'
            elif col == 'Cost':
                formatters[col] = {'type': 'money', 'symbol': '$', 'precision': 0}
                alignment[col] = 'right'

        table = pn.widgets.Tabulator(
            df, 
            show_index=True, 
            frozen_columns=['ID'],
            hidden_columns=['count'],
            formatters=formatters,
            text_align=alignment,
            configuration={'columnDefaults': {'headerSort': False}},
            header_align={c: 'center' for c in df.columns},
            selectable = False,
        )
        table.disabled = True
        self.gate_table = df
        return table
    
    def make_dots(self, plot, op, tgmap):
        """
        Called after the output panel is initialized, make a set of glyphs to display
        for each budget level.
        """
        self.selected_row = None
        self.dots = []
        for name, row in self.budget_table.iterrows():
            df = tgmap.map_coords().loc[row.gates]
            c = tgmap.map.circle_dot('x', 'y', size=12, line_color='blue', fill_color='white', source=df)
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

class DownloadPane(pn.Column):
    """
    After OptiPass has completed the last optimization run the GUI creates
    an instance of this class and saves it in the Download tab of the top 
    level display.
    """

    NB = 'Net benefit plot'
    IT = 'Individual target plots'
    BS = 'Budget summary table'
    BD = 'Barrier detail table'

    def __init__(self, op):
        """
        Display a set of checkboxes for the user to select what sort of data to
        include in a zip file.  If the gate table is not empty enable table downloads.
        Check the output panel to see which plots were created and to enable the
        net benefit plot if there is one.

        The pane also has a form to allow the user to enter the name of the download
        file, the format for the figures, and a button to click when they are ready
        to download the data.

        Arguments:
          op:  the OPResult object containing data tables and plots
        """
        super(DownloadPane, self).__init__()
        self.op = op
        self.folder_name = self._make_folder_name()

        self.grid = pn.GridBox(ncols=2)
        self.boxes = { }
        for x in [self.NB, self.BS, self.IT, self.BD]:
            b = pn.widgets.Checkbox(name=x, styles=box_styles, stylesheets=[box_style_sheet])
            if x in [self.NB, self.IT]:
                b.disabled = True
                b.value = False
            else:
                b.value = True
            self.boxes[x] = b
            self.grid.objects.append(b)

        self.filename_input = pn.widgets.TextInput(
            name = '', 
            value = self.folder_name,
        )

        self.image_type = pn.widgets.RadioBoxGroup(name='IFF', options=['HTML','PDF','PNG','JPEG'], inline=True)

        self.make_archive_button = pn.widgets.Button(name='Create Output Folder', stylesheets=[button_style_sheet])
        self.make_archive_button.on_click(self._archive_cb)

        self.append(pn.pane.HTML('<h3>Save Outputs</h3>', styles=header_styles))
        if len(self.op.matrix) > 0:
            self.append(pn.pane.HTML('<b>Items to Include in the Output Folder:</b>')),
            self.append(self.grid)
            self.append(pn.Row(
                pn.pane.HTML('<b>Image File Format:</b>'),
                self.image_type,
                margin=(20,0,0,0),
            ))
            self.append(pn.Row(
                pn.pane.HTML('<b>Output Folder Name:</b>'),
                self.filename_input,
                margin=(20,0,0,0),
            ))
            self.append(self.make_archive_button)
            self.append(pn.pane.HTML('<p>placeholder</p>', visible=False))

        # if there are figures at least one of them is an individual target, so enable
        # that option; if there is a net benefit figure it's the first figure, enable it
        # if it's there

        if len(self.op.display_figures) > 0:
            if self.op.display_figures[0][0] == 'Net':
                self.boxes[self.NB].value = True
                self.boxes[self.NB].disabled = False
            self.boxes[self.IT].value = True
            self.boxes[self.IT].disabled = False

    def _make_folder_name(self):
        """
        Use the region names, target names, and budget range to create the default name of the zip file.
        """
        parts = [s[:3] for s in self.op.regions]
        lst = self.op.targets
        if self.op.weights:
            lst = [f'{lst[i]}x{self.op.weights[i]}' for i in range(len(lst))]
        parts.extend(lst)
        parts.append(OP.format_budget_amount(self.op.binc*self.op.bcount)[1:])
        if self.op.mapping:
            parts.append(self.op.mapping)
        return '_'.join(parts)

    def _archive_cb(self, e):
        """
        Function called when the user clicks the Download button.  Create the output
        folder and compress it.  When the archive is ready, display a FileDownload
        widget with a button that starts the download.
        """
        if not any([x.value for x in self.boxes.values()]):
            return
        self.loading = True
        base = self._make_archive_dir()
        self._save_files(base)
        p = make_archive(base, 'zip', base)
        self.loading = False
        self[-1] = pn.widgets.FileDownload(file=p, filename=self.filename+'.zip', stylesheets=[button_style_sheet])

    def _make_archive_dir(self):
        """
        Create an empty directory for the download, using the name in the form.
        """
        self.filename = self.filename_input.value_input or self.filename_input.value
        archive_dir = Path.cwd() / 'tmp' / self.filename
        if Path.exists(archive_dir):
            rmtree(archive_dir)
        Path.mkdir(archive_dir)
        return archive_dir

    def _save_files(self, loc):
        """
        Write the tables and figures to the download directory.

        Arguments:
          loc:  the path to the directory.
        """
        figures = self.op.display_figures if self.image_type.value == 'HTML' else self.op.download_figures
        for name, fig in figures:
            if name == 'Net' and not self.boxes[self.NB].value:
                continue
            if name != 'Net' and not self.boxes[self.IT].value:
                continue
            if self.image_type.value == 'HTML':
                savehtml(fig, filename=loc/f'{name}.html')
            else:
                ext = self.image_type.value.lower()
                fn = loc/f'{name}.{ext}'
                fig.savefig(fn, bbox_inches='tight')
        if self.boxes[self.BS].value:
            df = self.op.summary.drop(['gates'], axis=1)
            df.to_csv(
                loc/'budget_summary.csv', 
                index=False,
                float_format=lambda n: round(n,2)
            )
        if self.boxes[self.BD].value:
            self.op.matrix.to_csv(
                loc/'barrier_details.csv',
                index=False,
                float_format=lambda n: round(n,2)
            )
