
# An instance of the TGMap class is a map widget that will be
# displayed in the sidebar

import json
from op import OP
import panel as pn
import pandas as pd
from pathlib import Path

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
        print(url)
        xpixels = 473
        ypixels = 533
        p = bk.figure(
            title=OP.mapinfo['map_title'],
            x_range=(0,xpixels), 
            y_range=(0,ypixels),
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
        
class TiledMap(TGMap):
    '''
    A tiled map uses a tile server to fetch the map image.
    '''

    def __init__(self):
        print('make a tiled map')

    def _create_map(self, bf):
        """
        Hidden method, called by the constructor to create a Bokeh figure 
        based on the latitude and longitude of the barriers in
        a project.
        """
        self.tile_provider = get_provider(xyz.OpenStreetMap.Mapnik)
        p = bk.figure(
            title='Oregon Coast', 
            height=900,
            width=400,
            x_range=(bf.map_info.x.min()*0.997,bf.map_info.x.max()*1.003), 
            y_range=(bf.map_info.y.min()*0.997,bf.map_info.y.max()*1.003),
            x_axis_type='mercator',
            y_axis_type='mercator',
            toolbar_location='below',
            tools=['pan','wheel_zoom','hover','reset'],
            tooltips = [
                ("ID", "@id"),
                ("Region", "@region"),
                ("Type", "@type"),
            ]
        )
        p.add_tile(self.tile_provider)
        p.toolbar.autohide = True
        dots = { }
        for r in bf.regions:
            df = bf.map_info[bf.map_info.region == r]
            c = p.circle('x', 'y', size=5, color='darkslategray', source=df, tags=list(df.id))
            dots[r] = c
            c.visible = False

        self.outer_x = (bf.map_info.x.min()*0.997,bf.map_info.x.max()*1.003)
        self.outer_y = (bf.map_info.y.min()*0.997,bf.map_info.y.max()*1.003)

        return p, dots
    
    def _create_ranges(self, df):
        """
        Hidden method, called by the constructor to create a Pandas Dataframe 
        containing the range of latitudes and longitudes of the barriers in
        a project.
        """
        g = df.map_info.groupby('region')
        return pd.DataFrame({
            'x_min': g.min().x,
            'x_max': g.max().x,
            'y_min': g.min().y,
            'y_max': g.max().y,
        })

    def zoom(self, selection):
        """
        Update the map, setting the x and y range based on the currently selected
        regions.

        Arguments:
          selection:  a list of names of regions currently selected
        """
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

