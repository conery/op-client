# Deploying a Client

## Local Installation Using Pip

To run the `op-client` application on your own system you need Python version 3.11.1 or later.

When you type the `pip` command that installs the code you will probably be downloading dozens of new libraries, including Panel (the GUI libarary), Bokeh (the server that manages the web application), Pandas (data science libarary that works with tabular data).
We strongly advise creating a new Python environment and installing the client there.

In the examples below, the shell prompt is preceded by `(tgo)`, which is the name of the Python environment used to make the examples.
This environment is based on `pyenv` but Conda would work equally well.
The second part of the prompt is the name of the directory where the command was entered.

#### 1. Download the Source Code

Open a terminal window and `cd` to a directory where you want to install the server.
If you have the GitHub command line tools, type this command to download the source code from GitHub:

```bash
(tgo) [myprojects] $ gh repo clone conery/op-server
```

> _If you don't have `gh` on your system you can download the project archive from [https://github.com/conery/op-client](https://github.com/conery/op-client) and unzip it in your project directory._ 

#### 2. Install the Python Libraries

At this point you should have a new folder named `op-sever` in your project directory.
`cd` into that folder:

```bash
(tgo) [myprojects] $ cd op-server
```

Type this command to have Pip install all the libraries required by the client:

```bash
(tgo) [op-server] $ pip install -r requirements.txt
```

#### 3. Start the Client

The shell command that starts the client has this general form:

```bash
(tgo) [op-server] $ python src/main.py --server X --project P
```

where `X` is the URL of an `op-server` that will run OptiPass and `P` is the name of one of the data sets managed by that server.

For example, if there is a server running at `tidegates-r-us.org` the command to connect to the server and work with the demo data would be

```bash
(tgo) [op-server] $ python src/main.py --server http://tidegates-r-us.org --project demo 
```

A couple of notes:

* Depending on how the server is set up you might need to use a secure connection, _i.e._ use `https` instead of `http` at the beginning of the URL.
* There may be additional "path" information at the end of the URL.  For example, the web server at `tidegates-r-us.org` may have several other web sites, in which case the web site administators there will have assigned a "path" that needs to be appended to the URL.  In that case, the URL would look something like this:

```
--server http://tidegates-r-us.org/op
```

> where `op` is the path defined by the web administrators.

#### 4. Connect to the Client

At this point you will have a Bokeh server running on your computer.
To use the client, start any web browser and have it connect to `http://localhost:5006`.

> _The `localhost` part of that URL means "this computer".  If your web browser doesn't recognize that name try using `http://127.0.0.1:5006`_

#### 5. Shutting Down the Client

When you're done:

* close the browser window
* go back to the terminal window where you typed the command to start the client and hit `⌃C` (hold down the control key while typing C)

> _You can also just close the terminal window if you won't be needing it any more_


## Local Container with Docker Desktop

Another way to run the `op-client` application on your own system is to run the code in a pre-configured "image" from DockerHub.
A Docker image is a small, self-contained Linux system that has Python, the client application, and all the libraries it needs already installed and ready to go.


#### 1. Pull the Image

The first time you use the client you need to download the image from DockerHub (Docker refers to this as "pulling" the image).

Open the Docker Desktop GUI.
Click on "Docker Hub" in the panel on the left side of the window.
In the search bar, type "conery", then look for `conery/op-client` and click on that.

You should now see a page that has a short description of the image, and a button labeled "Pull" on the right side of the window.
Click that button to download the image.

#### 2. Start the Container

Once you have the image you can start a "container" (the Docker term for a running image).

Open Docker Desktop and click on Images in the panel on the left.
You should see table with a row for the `op-client` image.
In the column labeled "Actions" there is a right-facing triangle (designed to look like the "play" button on a music app).

Click the play button and a window will pop up.
Click the arrow next to "Optional Settings".
Under "Ports" there is a box.
Click in the box, where it says "host port", and type 5006.

At the bottom of the window is a section labeled "Environment Variables".
This is where you specify the URL of the `op-server` you want to connect to and the name of the data set you want to use.

* Click in the box that says "Variable" and type `OP_SERVER` (using all upper case).  Next to it, click on "Value" and enter the URL of the server.  For example, if your server is at `tidegates-r-us.org` you would enter `http://tidegates-r-us.org` (see the note below).
* Click the plus sign to the right of the box where you just entered the URL.  A new pair of variable name and value boxes appear.  Enter `OP_PROJECT` in the variable box and the name of the data set (_e.g._ `demo`) in the value box.

Click the Run box to launch the client application running inside your new container.

Notes:

* Depending on how the server is set up you might need to use a secure connection, _i.e._ use `https` instead of `http` at the beginning of the URL for the `op-server`.
* There may be additional "path" information at the end of the URL.  For example, the web server at `tidegates-r-us.org` may have several other web sites, in which case the web site administators there will have assigned a "path" that needs to be appended to the URL.  In that case, the URL would look something like `http://tidegates-r-us.org/op`.

#### 3. Open a Browser Window

To connect to the software running in the container start a browser and tell it to open `http://localhost:5006` (if that doesn't work try `http://127.0.0.1:5006`).

#### 4. Managing the Container

When you're done you can close the browser window.

Open the Docker Desktop window and click on Containers in the panel on the left.
In the table row for your container, in the column named Actions, the "play" button has been turned into a "pause" button (a gray square).

* If you want to use the container again in the future click the pause button.
After a few seconds (while Docker is shutting down the container) the button will again look like a play button.
The next time you want to use it come back here to this window and click the play button.
The container will resume where you left off -- just open a browser window and connect to `http://localhost:5006` again.
You don't need to re-enter the container settings.
* If you are done with the container click the trash can icon at the end of the line.
This will delete the container, but not the image.
You can always come back in the future and create a new container using the steps in section 2 above.

## Container in the Cloud

Coming soon: instructions for setting up a server at AWS.
