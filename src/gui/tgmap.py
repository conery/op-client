
# An instance of the TGMap class is a map widget that will be
# displayed in the sidebar

import logging
import numpy as np
from op import OP
import pandas as pd

import bokeh.plotting as bk
from bokeh.tile_providers import get_provider
import xyzservices.providers as xyz


class TGMap:
    """
    A TGMap object manages the display of a map that shows the locations of the barriers
    in a project.  

    A static method named `init` is a factory that instantiates a new map.  It will read 
    the "mapinfo" file for the project and return a reference to a new
    map object belonging to the class specified in the mapinfo file.

    Attributes:
      map:  a Bokeh figure object, with x and y ranges defined by the locations of the barriers
      dots: a dictionary that maps region names to a list of circle glyphs for each barrier in a region
      ranges: a data frame that has the range of x and y coordinates for each region    
    """

    @staticmethod
    def init():
        mods = globals()
        if 'map_type' not in OP.mapinfo:
            raise ValueError(f'TGMap: Mapinfo missing a map_type')
        if cls := OP.mapinfo['map_type']:
            return mods[cls]()
        else:
            raise ValueError(f"TGMAp: unknown map type: {OP.mapinfo['map_type']}")
        
    def map_coords(self):
        '''
        Return a frame that has the coordinates and other info needed to display
        gates on a map
        '''
        return self._map_coords

    def graphic(self):
        '''
        Return a reference to the map (a Bokeh figure).
        '''
        return self.map

    def display_regions(self, selection):
        """
        Method called when the user clicks the checkbox next to the name
        of a region.  Set the visible attribute of each dot to True or False depending
        on whether the region it is in is selected.

        Arguments:
          selection:  a list of names of regions currently selected
        """
        for r, dots in self.dots.items():
            dots.visible = r in selection

class StaticMap(TGMap):
    '''
    A static map is simply a PNG file downloaded from the server. 
    '''

    def __init__(self):
        url = f"{OP.server_url}/map/{OP.project_name}/{OP.mapinfo['map_file']}"
        logging.info(f'Fetching map from {url}')
        xpixels = 473
        ypixels = 533
        p = bk.figure(
            title=OP.mapinfo['map_title'],
            x_range=(0,xpixels), 
            y_range=(0,ypixels),
            tools=OP.mapinfo['map_tools'],
            tooltips = [
                ("Barrier", "@ID"),
                ("Region", "@region"),
                ("Cost", "@cost")
            ]
        )
        p.image_url(url=[url], x = 0, y = ypixels, h = ypixels, w = xpixels)
        bf = OP.barrier_frame
        self.dots = { }
        for r in OP.region_names:
            df = bf[bf.region == r]
            c = p.circle('X','Y', size=10, color='darkslategray', source=df)
            self.dots[r] = c
            c.visible = False
        self.map = p

        df = bf[['region','X','Y']]
        df.columns = ['region','x','y']
        self._map_coords = df
        
class TiledMap(TGMap):
    '''
    A tiled map uses a tile server to fetch the map image.  Fetch the main barrier
    file to get the coordinates and other data for each barrier.
    '''

    def __init__(self):
        # bf = self._fetch_barriers()
        self._map_coords = self._make_info(OP.barrier_frame)
        self.regions = self._make_region_list()
        self.ranges = self._create_ranges()
        self.tile_provider = get_provider(xyz.OpenStreetMap.Mapnik)
        p = bk.figure(
            title='Oregon Coast', 
            height=900,
            width=400,
            x_range=(self._map_coords.x.min()*0.997,self._map_coords.x.max()*1.003), 
            y_range=(self._map_coords.y.min()*0.997,self._map_coords.y.max()*1.003),
            x_axis_type='mercator',
            y_axis_type='mercator',
            toolbar_location='below',
            tools=['pan','wheel_zoom','hover','reset'],
            tooltips = [
                ("ID", "@ID"),
                ("Region", "@region"),
                ("Type", "@type"),
            ]
        )
        p.add_tile(self.tile_provider)
        p.toolbar.autohide = True
        self.dots = { }
        for r in self.regions:
            df = self._map_coords[self._map_coords.region == r]
            c = p.circle('x', 'y', size=5, color='darkslategray', source=df, tags=list(df.index))
            self.dots[r] = c
            c.visible = False

        self.map = p

        self.outer_x = (self._map_coords.x.min()*0.997,self._map_coords.x.max()*1.003)
        self.outer_y = (self._map_coords.y.min()*0.997,self._map_coords.y.max()*1.003)
    
    # def _fetch_barriers(self):
    #     """
    #     Hidden method, fetch the barrier data from the server to get the
    #     map coordinates and other data we need.
    #     """
    #     url = f"{OP.server_url}/barriers/{OP.project_name}"
    #     resp = requests.get(url)
    #     if resp.status_code != 200:
    #         raise OPServerError(resp)
    #     buf = StringIO(resp.json()['barriers'])
    #     return pd.read_csv(buf)
    
    def _make_info(self, bf):
        """
        Hidden method, makes a dataframe with attributes needed to display gates on a map.
        Map latitude and longitude columns in the input frame to Mercator
        coordinates, and copy the ID, region and barrier types so they can
        be displayed as tooltips.
        """
        df = bf[['region','type']]
        R = 6378137.0
        map_coords = pd.concat([
            df, 
            np.radians(bf.X)*R, 
            np.log(np.tan(np.pi/4 + np.radians(bf.Y)/2)) * R
        ], axis=1)
        map_coords.columns = ['region', 'type', 'x', 'y']
        return map_coords

    def _make_region_list(self):
        '''
        Hidden method, make a list of unique region names, sorted by latitude, so regions
        are displayed in order from north to south.  Updates the list of names in the
        OP object.
        '''
        df = self._map_coords[['region','y']]
        mf = df.groupby('region').mean(numeric_only=True).sort_values(by='y',ascending=False)
        names = list(mf.index)
        OP.region_names = names
        return names

    def _create_ranges(self):
        """
        Hidden method, called by the constructor to create a Pandas Dataframe 
        containing the range of latitudes and longitudes of the barriers in
        a project.
        """
        g = self._map_coords.groupby('region')
        return pd.DataFrame({
            'x_min': g.min().x,
            'x_max': g.max().x,
            'y_min': g.min().y,
            'y_max': g.max().y,
        })

    def display_regions(self, selection):
        """
        Update the map, setting the x and y range based on the currently selected
        regions.

        Arguments:
          selection:  a list of names of regions currently selected
        """
        super().display_regions(selection)
        if len(selection) > 0:
            xmin = min([self.ranges['x_min'][r] for r in selection])
            xmax = max([self.ranges['x_max'][r] for r in selection])
            ymin = min([self.ranges['y_min'][r] for r in selection])
            ymax = max([self.ranges['y_max'][r] for r in selection])

            mx = (xmax+xmin)/2
            my = (ymax+ymin)/2
            dx = max(5000, xmax - xmin)
            dy = max(5000, ymax - ymin)
            ar = self.map.height / self.map.width

            if dy / dx > ar:
                dx = dy / ar
            else:
                dy = dx * ar

            self.map.x_range.update(start=mx-dx/2-5000, end=mx+dx/2+5000)
            self.map.y_range.update(start=my-dy/2, end=my+dy/2)
        else:
            self.map.x_range.update(start=self.outer_x[0], end=self.outer_x[1])
            self.map.y_range.update(start=self.outer_y[0], end=self.outer_y[1])
        self.map.add_tile(self.tile_provider)

