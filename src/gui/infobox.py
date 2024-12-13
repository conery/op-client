#
#  Display messages in a modal window
#

import panel as pn
from op import OP

class InfoBox(pn.Column):
    """
    When the user clicks the Run Optimizer button in the Start panel
    the GUI displays a message by calling one of the methods in 
    this class.  Messages are displayed in the modal dialog area
    defined by the GUI template.
    """

    missing_params_text = '''### Missing Information

Please select

'''

    invalid_weights_text = '''### Invalid Weights

Target weights must be numbers between 1 and 5 (not {})
'''

    preview_message_text = '''### Review Optimizer Settings

Clicking Continue will run the optimizer with the following settings:

'''

    success_text = '''### Optimization Complete

Click on the **Output** tab to see the results.
'''

    fail_text = '''### Optimization Failed

Reason: {}
'''

    def __init__(self, template, run_cb):
        """
        Initialize the module.

        Arguments:
          template:  the application template (which contains the modal dialog area to use)
          run_cb:  a callback function to invoke after the user reviews settings and clicks "Continue"
        """
        super(InfoBox, self).__init__()
        self.template = template

        self.continue_button = pn.widgets.Button(name='Continue')
        self.continue_button.on_click(run_cb)

        self.cancel_button = pn.widgets.Button(name='Cancel')
        self.cancel_button.on_click(self._cancel_cb)

    def _cancel_cb(self, _):
        """
        Close the dialog when the user clicks the "Cancel" button.
        """
        self.template.close_modal()
 
    def show_missing(self, rlist, budget, tlist):
        """
        Method called by the OP class when it detects missing parameters (e.g.
        if the user did not select a region or a target).
        """
        text = self.missing_params_text
        if len(rlist) == 0:
            text += ' * one or more geographic regions\n'
        if not budget:
            text += ' * a maximum budget\n'
        if len(tlist) == 0:
            text += ' * one or more targets\n'
        self.clear()
        self.append(pn.pane.Alert(text, alert_type = 'warning'))
        self.template.open_modal()

    def show_invalid_weights(self, w: list[str]):
        """
        Method called when weighted targets are being used and one of the
        text boxes does not have a valid entry (must be a number between 1 and 5).

        Arguments:
          w: the list of strings read from the text entry widgets
        """
        text = self.invalid_weights_text.format(w)
        self.clear()
        self.append(pn.pane.Alert(text, alert_type = 'warning'))
        self.template.open_modal()
        
    def show_params(self, regions, budgets, targets, weights, mapping):
        """
        Method called to allow the user to review the optimization parameters read from the
        various widgets.  Displays each parameter and two buttons ("Cancel" and "Continue").

        Arguments:
          regions:  list of region names
          budgets:  a tuple with starting budget, increment, and count
          targets:  list of restoration target names
          weights:  list of target weights (optional)
          mapping:  column mappings (optional)
        """
        bstart, binc, bcount = budgets
        fbmax = OP.format_budget_amount(binc*bcount)
        fbstep = OP.format_budget_amount(binc)
        fbstart = OP.format_budget_amount(bstart)
        text = self.preview_message_text
        text += f'  * Regions: {", ".join(regions)}\n\n'
        if bcount > 1:
            text += f'  * {bcount} budget levels from {fbstep} up to {fbmax} in increments of {fbstep}\n\n'
        else:
            text += f'  * a single budget of {fbstart}\n\n'
        targets = [t.split(':')[-1] for t in targets]
        if weights:
            targets = [f'{targets[i]} ⨉ {weights[i]}' for i in range(len(targets))]
        text += f'  * Targets: {", ".join(targets)}\n' 
        text += f'  * Mapping: {mapping}\n\n'
        self.clear()
        self.append(pn.pane.Alert(text, alert_type = 'secondary'))
        self.append(pn.Row(self.cancel_button, self.continue_button))
        self.template.open_modal()

    def show_success(self):
        """
        Method called after OptiPass has finished running and the results have been
        parsed successfully.
        """
        self.clear()
        self.append(pn.pane.Alert(self.success_text, alert_type = 'success'))
        self.template.open_modal()

    def show_fail(self, reason):
        """
        Method called if OptiPass failed.

        Arguments:
          reason:  string containing the error message
        """
        self.clear()
        text = self.fail_text.format(reason)
        if str(reason) == 'No solution':
            text += '\n * try increasing the maximum budget'
        self.append(pn.pane.Alert(text, alert_type = 'danger'))
        self.template.open_modal()

