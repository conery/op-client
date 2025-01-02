# GUI

The Python syntax for defining a new class that is derived from an existing class uses a `class` statement.
This is the statement that defines the RegionBox class:
```
class RegionBox(pn.Column):
    ...
```
`pn.Column` is an existing widget class, defined in the Panel library.
That means our new RegionBox objects will be special types of columns that can be inserted into the GUI at some place.

The code that is called to create a new object is a function named `__init__` defined inside the class.
The first argument to `__init__` is always `self`, which is a reference to the object being built.

Here is a simplified version of the `__init__` function for the RegionBox class (the actual definition is shown below, in the documentation for RegionBox):

```
class RegionBox(pn.Column):
    
    def __init__(self, project):
        self.boxes = { }
        for name in OP.region_names:
            box = pn.widgets.Checkbox(name=name, styles=box_styles, stylesheets=[box_style_sheet])
            box.param.watch(self.cb, ['value'])
            self.boxes[name] = box
```

When this function is called, it initializes a variable named `boxes` to be an empty dictionary.  The `for` loop iterates over all the region names.  It makes a Checkbox widget for each region and adds the box to the dictionary.

The line in the middle of the loop that calls `box.param.watch` is where all the "magic" happens.  This function call tells the GUI that whenever a checkbox is clicked it should call a function named `cb` that is also defined inside the RegionBox class.  Here is a simplified version:
```
def cb(self, event):
    r = event.obj.name
    if event.new:
        self.selected.add(r)
    else:
        self.selected.remove(r)
```
The name `cb` is short for "callback", a common name for this type of function.  The parameter named `event` has information about what the user just did.  In this case, we want to get the name of the button (which will be one of the region names) and then update the set of selected regions.  If the button was turned on we add the region name to the set, otherwise we remove it.

## TideGatesApp

::: src.gui.app.TideGatesApp
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 3
      filters: ""
      members_order: source

## BudgetBox

::: src.gui.budgets.BudgetBox
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 3
      filters: ""
      members_order: source

### BasicBudgetBox

::: src.gui.budgets.BasicBudgetBox
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 4
      filters: ""
      members_order: source

### FixedBudgetBox

::: src.gui.budgets.FixedBudgetBox
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 4
      filters: ""
      members_order: source

### AdvancedBudgetBox

::: src.gui.budgets.AdvancedBudgetBox
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 4
      filters: ""
      members_order: source

## DownloadPane

::: src.gui.output.DownloadPane
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 3
      filters: ""
      members_order: source

## InfoBox

::: src.gui.infobox.InfoBox
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 3
      filters: ""
      members_order: source

## OutputPane

::: src.gui.output.OutputPane
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 3
      filters: ""
      members_order: source

## RegionBox

::: src.gui.regionbox.RegionBox
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 3
      filters: ""
      members_order: source

## TargetBox

::: src.gui.targetbox.TargetBox
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 3
      filters: ""
      members_order: source

### BasicTargetBox

::: src.gui.targetbox.BasicTargetBox
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 4
      filters: ""
      members_order: source

### WeightedTargetBox

::: src.gui.targetbox.WeightedTargetBox
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 4
      filters: ""
      members_order: source

## TGMap

::: src.gui.tgmap.TGMap
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 3
      filters: ""
      members_order: source

### StaticMap

::: src.gui.tgmap.StaticMap
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 4
      filters: ""
      members_order: source

### TiledMap

::: src.gui.tgmap.TiledMap
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 4
      filters: ""
      members_order: source
