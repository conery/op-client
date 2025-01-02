## Unit Tests

Unit testing is done with `pytest`.
To run all the tests, simply `cd` to the top level directory and type this shell command:

```bash
$ pytest
```

The tests are all in the `tests` directory:

* `test_optipass.py` has functions that test the interface to OptiPass

You can run one set of tests by including the file name in the shell command, _e.g._

```bash
$ pytest test/test_optipass.py
```

### Test the OP Class

The OP class is the abstract interface to the `op-server` REST server.

When the main application starts it calls the `setup` method.
That method sends HTTP requests to the server and it saves the returned values so they are accessible to static methods of the OP class.

To test `setup` we use a library named `responses`.
It allows us to "short-circuit" the HTTP request.
Whenever `setup` tries to send a URL, the `responses` module catches it and returns a response to use for the test.

Here's an example.  To get the list of project names from the server, the `setup` method has this code:

```
      req = f'{server}/projects'
      resp = requests.get(req)
```

In the test, we have this code:

```
    path_to_projects = f'{server}/projects'
    responses.get(path_to_projects, json = ["demo"])
```

What that means is "whenever there is an HTTP request to a URL of the form `f'{server}/projects'` reply with the JSON form of the list `["demo"]`.
In other words, trick the `setup` code into thinking it connected to a server that has the demo data.

The body of the `test_setup` method defines responses for all of the requests that `setup` will try to send.
It then calls `setup`, and when it returns the test code will check all of the attributes of the OP class to make sure they have the expected values.


::: test.test_optipass
    options:
      heading_level: 4
      members_order: source

### Widget Tests

TBD
