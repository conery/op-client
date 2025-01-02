# Reference

The source code is in a folder named `src`.
Inside that are files for the top level application (`main.py`), a module that serves as the interface to the server (`op.py`), and a folder named `gui` that has definitions of the components in graphical user interface.

```
src
├── gui
│   ├── app.py
│   ├── budgets.py
│   ├── infobox.py
│   ├── output.py
│   ├── regionbox.py
│   ├── styles.py
│   ├── targetbox.py
│   └── tgmap.py
├── main.py
└── op.py
```
## `main.py`

This file has the main entry point called when the program is launched from the command line.
It uses `argparse` to get command line options, initializes the OptiPass interface, creates the Panel application, and starts the application.

### `make_app`

::: src.main.make_app
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 3
      filters: ""
      members_order: source

### `start_app`

::: src.main.start_app
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 3
      filters: ""
      members_order: source

## `op.py`

A class named OP provides an abstract interface to the data for the current project.
For example, the "widgets" in the GUI call OP methods to get the list of region names or descriptions of restoration targets.

The module is essentially a "singleton object".
It defines a collection of static methods.
When the top level application starts it calls a method named `setup`, which initializes all the data; after that the GUI objects call methods to get values of the data.

### MetaOP

The OP class is actually constructed at runtime by a "metaclass".
When the application is started, OP has a few methods but no data.
The `setup` method fetches the data from the server and adds it to the OP class.

Here's a concrete example of how this is done, using target data, which is stored in a Pandas dataframe.
The metaclass, which is named MetaOP, defines a method named `target_frame`:

```python
    @property
    def target_frame(cls):
        return cls._target_frame
```

That definition defines the name, but that name doesn't refer to any acutal table of values at this point.

The `setup` method includes these lines to fetch the target descriptions from the server, convert those descriptions into a Pandas dataframe, and save the frame:

```python
        req = f'{server}/targets/{project}'
        resp = requests.get(req)
        if resp.status_code != 200:
            raise OPServerError(resp)
        dct = resp.json()
        buf = StringIO(dct['targets'])
        cls._target_frame = pd.read_csv(buf).set_index('abbrev')
```

The first line creates the URL of the REST request to send to the remote server, the second line sends the request.
When the response comes back, the third line makes sure the request succeeded.
Lines 4 and 5 create the data frame, and the last line saves it in an internal variable named `_target_frame`.

From this point on, methods in the GUI can access the data by using the expression `OP.target_frame`.
That will call the `target_frame` method shown above, which accesses the value in the internal variable and returns it to the GUI.

::: src.op.MetaOP
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 4
      filters: ""
      members_order: source

### OP

::: src.op.OP
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 4
      filters: ""
      members_order: source

### OPResult

::: src.op.OPResult
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 4
      filters: ""
      members_order: source

### DevOP

::: src.op.DevOP
    options:
      show_root_toc_entry: false
      docstring_options:
        ignore_init_summary: true
      merge_init_into_class: true
      heading_level: 4
      filters: ""
      members_order: source
