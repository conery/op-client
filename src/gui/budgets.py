#
# Widgets to display budget options for the Tide Gate Optimization tool
#

import logging
import panel as pn
from bokeh.models.formatters import NumeralTickFormatter

from .styles import slider_style_sheet

class BudgetBox(pn.Column):
    """
    There are three ways users can specify the range of budget values
    when running OptiPass.  A BudgetBox widget has one tab for each option.
    The widgets displayed inside a tab are defined by their own classes
    (BasicBudgetBox, AdvancedBudgetBox, and FixedBudgetBox).
    """

    def __init__(self):
        super(BudgetBox, self).__init__()
        self.tabs = pn.Tabs(
            ('Basic', BasicBudgetBox()),
            ('Advanced', AdvancedBudgetBox()),
            ('Fixed', FixedBudgetBox()),
        )
        self.append(self.tabs)

    def set_budget_max(self, n: int):
        """
        When the user selects or deselects a region the budget widgets need
        to know the new total cost for all the selected regions.  This method
        passes that information to each of the budget widgets.

        Arguments:
          n: the new maximum budget amount
        """
        for t in self.tabs:
            t.set_budget_max(n)

    def values(self):
        """
        Return the budget settings for the currently selected budget type.  Get
        the widget values from the active budget type, convert them into a tuple
        of values that will be passed to the optimizer.

        Returns:
          bmin:  the starting budget
          binc:  the increment between budget values
          bcnt:  the number of budget values 
        """
        return self.tabs[self.tabs.active].values()
    
    def defined(self):
        """
        Return True if the user has defined a budget using the current tab
        """
        return self.tabs[self.tabs.active].defined()
    
    def set_value(self, n):
        """
        Initialize the GUI by setting an initial budget value
        """
        self.tabs[self.tabs.active].set_value(n)


class BasicBudgetBox(pn.WidgetBox):
    """
    The default budget widget displays a slider that ranges from 0
    up to a maximum value based on the total cost of all barriers in
    currently selected regions.
    """

    levels = [
        ('$0', 0),
        ('$500K', 500000),
        ('$1M', 1000000),
        ('$2.5M', 2500000),
        ('$5M', 5000000),
        ('$10M', 10000000),
        ('$25M', 25000000),
        ('$50M', 50000000),
        ('$100M', 100000000),
    ]

    MIN_LEVELS = 3

    def __init__(self):
        super(BasicBudgetBox, self).__init__(margin=(15,0,15,5))
        self.labels = [ x[0] for x in self.levels ]
        self.map = { x[0]: x[1] for x in self.levels }
        self.slider = pn.widgets.DiscreteSlider(
            options = self.labels[:self.MIN_LEVELS], 
            value = self.labels[0],
            name = 'Maximum Budget',
            margin=(20,20,20,20),
            stylesheets=[slider_style_sheet],
        )
        self.append(self.slider)

    def set_budget_max(self, n):
        """
        Choose a maximum budget by scanning a table of budget levels to
        find the first one less than the total cost.

        Arguments:
          n: the total cost of all barriers in the current selection.
        """
        for i in range(len(self.levels)-1, -1, -1):
            if n >= self.levels[i][1]:
                break
        i = max(i, self.MIN_LEVELS)
        self.slider.options = self.labels[:i+1]

    BUDGET_COUNT = 10

    def values(self):
        """
        The basic budget always has the same number of budgets and always
        starts with $0.  Determine the increment by dividing the max budget
        in the slider by the number of budgets.
        """
        x = self.map[self.slider.value]
        return 0, x // self.BUDGET_COUNT, self.BUDGET_COUNT
        
    def defined(self):
        """
        The basic budget is set if the slider is not in the first location.
        """
        return self.slider.value != '$0'

    def set_value(self, n):
        """
        Set the slider to n
        """
        self.slider.value = self.slider.options[n]
    
class FixedBudgetBox(pn.WidgetBox):
    """
    This option is for situations where a user knows exactly how much money they
    have to spend and want to know the optimal set of barriers to replace for that
    amount of money.  OptiPass is run twice -- once to determine the current 
    passabilities, and once to compute the benefit from the specified budget.
    The widget simply displays a box where the user enters the dollar amount for
    their budget.
    """

    def __init__(self):
        super(FixedBudgetBox, self).__init__(margin=(15,0,15,5))
        self.input = pn.widgets.TextInput(name='Budget Amount', value='$')
        self.append(self.input)

    def set_budget_max(self, n):
        pass

    def values(self):
        """
        A fixed budget has one value, returned as the starting budget.  The 
        the increment is 0 and count is 1.
        """
        s = self.input.value
        if s.startswith('$'):
            s = s[1:]
        n = self.parse_dollar_amount(self.input.value)
        return n, 0, 1
        
    def defined(self):
        """
        The fixed budget is set if the text box is not empty.
        """
        return self.parse_dollar_amount(self.input.value) > 0
    
    def set_value(self, n):
        """
        Initialize the budget to n
        """
        self.input.value = f'${n}'

    def parse_dollar_amount(self, s: str):
        """
        Make sure the string entered by the user has an acceptable format.
        It can be all digits (e.g. "1500000"), or digits separated by commas
        (e.g. "1,500,000"), or a number followed by a K or M (e.g. "1.5M").
        There can be a dollar sign at the front of the string.

        Arguments:
          s:  the string entered into the text box

        Returns:
          the value of the string converted into an integer
    
        """
        try:
            if s.startswith('$'):
                s = s[1:]
            if s.endswith(('K','M')):
                multiplier = 1000 if s.endswith('K') else 1000000
                res = int(float(s[:-1]) * multiplier)
            elif ',' in s:
                parts = s.split(',')
                assert len(parts[0]) <= 3 and (len(parts) == 1 or all(len(p) == 3 for p in parts[1:]))
                res = int(''.join(parts))
            else:
                res = 0 if s == '' else int(s)
            return res
        except Exception:
            return 0
            
class AdvancedBudgetBox(pn.WidgetBox):
    """
    The "advanced" option gives the user the most control over the budget values processed
    by OptiPass by letting them specify the number of budget levels (in the basic budget
    there are always 10 budget levels).  
    
    This box has three widgets:  a slider to specify the
    maximum amount, another slider to specify the increment between budgets, and
    an input box to specify the number of budgets.  Adjusting the value of any of these
    widgets automatically updates the other two.  For example, if the maximum is set to $1M
    and the number of budgets is 10, the increment is $100K.  If the user changes the number
    of budgets to 20, the increment drops to $50K.  Or if they change the maximum to $2M, the
    increment increases to $200K.
    """

    MAX_STEP = 10000
    INC_STEP = 1000
    COUNT_MIN = 2
    COUNT_MAX = 100
    MAX_SLIDER_WIDTH = 275
    INC_SLIDER_WIDTH = 125
    BOX_WIDTH = MAX_SLIDER_WIDTH + INC_SLIDER_WIDTH + 150

    def __init__(self):
        super(AdvancedBudgetBox, self).__init__(margin=(15,0,15,5), width=self.BOX_WIDTH)

        self.cap = 0

        self.max_slider = pn.widgets.FloatSlider(
            name='Maximum Budget', 
            start=0, 
            end=1, 
            step=self.MAX_STEP,
            value=0,
            width=self.MAX_SLIDER_WIDTH,
            format=NumeralTickFormatter(format='$0,0'),
            stylesheets=[slider_style_sheet],
        )

        self.inc_slider = pn.widgets.FloatSlider(
            name='Budget Interval', 
            start=0, 
            end=1, 
            step=self.INC_STEP,
            value=0,
            width=self.INC_SLIDER_WIDTH,
            format=NumeralTickFormatter(format='$0,0'),
            stylesheets=[slider_style_sheet],
        )

        self.count_input = pn.widgets.IntInput(
            value=10, 
            step=1, 
            start=self.COUNT_MIN,
            end=self.COUNT_MAX,
            width=75,
        )

        self.append(pn.GridBox(
            nrows=2,
            ncols=2,
            objects=[
                self.max_slider,
                self.inc_slider,
                pn.pane.HTML('<b>Limit: N/A<b>'),
                pn.Row(pn.pane.HTML('#Budgets:'),self.count_input, align=('start','center'))
            ]
        ))

        self.max_slider.param.watch(self.max_updated, ['value'])
        self.inc_slider.param.watch(self.inc_updated, ['value'])
        self.count_input.param.watch(self.count_updated, ['value'])

    def values(self):
        """
        In this widget the budget increment and budget count are determined
        by the values in the corresponding widgets.
        """
        return 0, self.inc_slider.value, self.count_input.value
        
    def defined(self):
        """
        The advance budget is set if the increment is not 0
        """
        return self.inc_slider.value > 0
    
    def set_value(self, n):
        """
        Set the budget to n
        """
        self.max_slider.value = n

    def set_budget_max(self, n):
        """
        Called when the user selects or deselects a region.  Save the new
        maximum, and update the value of the increment based on the new maximum.

        Arguments:
          n:  the total cost of all barriers in the selected regions.
        """
        self.max_slider.end = max(1, n)
        self.max_slider.start = self.MAX_STEP
        self.inc_slider.end = max(1, n // 2)
        self.inc_slider.start = max(self.INC_STEP, n / self.COUNT_MAX)
        lim = 'N/A' if n == 0 else f'${n/1000000:.2f}M'
        self.objects[0][2] = pn.pane.HTML(f'<b>Limit: {lim}</b>')

    def max_updated(self, e):
        """
        Callback function invoked when the user moves the maximum budget
        slider.  Computes a new budget increment.
        """
        try:
            self.inc_slider.value = self.max_slider.value // self.count_input.value
        except ArithmeticError:
            pass

    def inc_updated(self, e):
        """
        Callback function invoked when the user changes the budget increment.
        Computes a new number of budgets.
        """
        try:
            c = max(self.COUNT_MIN, self.max_slider.value // self.inc_slider.value)
            c = min(self.COUNT_MAX, c)
            self.count_input.value = c
        except ArithmeticError:
            pass

    def count_updated(self, e):
        """
        Callback function invoked when the user changes the number of budget
        levels.  Computes a new budget increment.
        """
        try:
            self.inc_slider.value = self.max_slider.value // self.count_input.value
        except ArithmeticError:
            pass

