#Copyright (c) 2009, Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os.path

from sprites import *

#
# class for defining individual slider parts
#
class Slider:
    """ Create a sprite for a slider """
    def __init__(self, sprites, path, name, x, y, w, h):
        # create sprite from svg file
        self.spr = Sprite(sprites, x, y,
                          self.load_image(path,name,w,h))

    def draw_slider(self, layer=1000):
        self.spr.set_layer(layer)
        self.spr.draw()

    def load_image(self, path, name, w, h):
        return gtk.gdk.pixbuf_new_from_file_at_size(
            os.path.join(path+name+'.svg'), int(w), int(h))

class Tab:
    def __init__(self, sprites, path, name, x, y, w, h):
        # create sprite from svg file
        self.spr = Sprite(sprites, x, y,
                          self.load_image(path,name,w,h))
        self.spr.label = "1.0"

    def draw_slider(self, layer=1000):
        self.spr.set_layer(layer)
        self.spr.draw()

    def load_image(self, path, name, w, h):
        return gtk.gdk.pixbuf_new_from_file_at_size(
            os.path.join(path+name+'.svg'), int(w), int(h))


def svg_str_to_pixbuf(svg_string):
    """ Load pixbuf from SVG string. """
    pl = gtk.gdk.PixbufLoader('svg')
    pl.write(svg_string)
    pl.close()
    pixbuf = pl.get_pixbuf()
    return pixbuf
