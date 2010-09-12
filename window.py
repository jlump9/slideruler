# -*- coding: utf-8 -*-
#Copyright (c) 2009,2010 Walter Bender

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

from gettext import gettext as _

import math

try:
    from sugar.graphics import style
    GRID_CELL_SIZE = style.GRID_CELL_SIZE
except:
    GRID_CELL_SIZE = 0

from constants import SHEIGHT, SWIDTH, SCALE, OFFSET, LEFT, RIGHT, TOP, \
    BOTTOM, SCREENOFFSET
from sprite_factory import Slide, Stator, Reticule, CustomSlide, CustomStator
from sprites import Sprites
from genslides import C_slide, D_stator, CI_slide, DI_stator, A_slide, \
    A_stator, K_slide, K_stator, S_slide, S_stator, T_slide, T_stator, \
    L_slide, L_stator, LL0_slide, LL0_stator, LLn_slide, LLn_stator, \
    Custom_slide, Custom_stator

import traceback
import logging
_logger = logging.getLogger('sliderule-activity')


def round(x, precision=2):
    if precision == 2:
        return(float(int(x * 100 + 0.5) / 100.))
    elif precision == 1:
        return(float(int(x * 10 + 0.5) / 10.))
    elif precision == 0:
        return(int(x + 0.5))
    else:
        y = math.pow(10, precision)
        return(float(int(x * y + 0.5) / y))


def _calc_log(dx):
    """ C and D scales """
    rescale = 1
    if dx < 0:
        rescale = 0.1
        dx += SWIDTH - (2.0 * OFFSET)
    return round(math.exp(dx / SCALE) * rescale)


def _calc_inverse_log(dx):
    """ CI and DI scales """
    rescale = 1
    if dx < 0:
        rescale = 0.1
        dx += SWIDTH - (2.0 * OFFSET)
    return round(10.0/ math.exp(dx / SCALE) * rescale)


def _calc_log_squared(dx):
    """ A and B scales """
    rescale = 1
    if dx < 0:
        dx += SWIDTH - (2.0 * OFFSET)
        rescale = 0.01
    A = math.exp(2 * dx / SCALE) * rescale
    if A > 50:
        return round(A, 1)
    else:
        return round(A)


def _calc_log_cubed(dx):
    """ K scale """
    rescale = 1
    if dx < 0:
        rescale = 0.001
        dx += SWIDTH - (2.0 * OFFSET)
    K = math.exp(3 * dx / SCALE) * rescale
    if K > 500:
        return round(K, 0)
    elif K > 50:
        return round(K, 1)
    else:
        return round(K)


def _calc_log_log(dx):
    """ LL0 scale """
    if dx < 0:
        dx += SWIDTH - (2.0 * OFFSET)
    LL0 = math.exp(math.exp(dx / SCALE) / 1000)
    if LL0 > 1.002:
        return round(LL0, 5)
    else:
        return round(LL0, 6)


def _calc_linear(dx):
    """ L scale """
    if dx < 0:
        dx += SWIDTH - (2.0 * OFFSET)
        return round(10 * ((dx / SCALE) / math.log(10) - 1.0))
    else:
        return round(10 * (dx / SCALE) / math.log(10))


def _calc_sine(dx):
    """ S scale """
    dx /= SCALE
    s = math.exp(dx)/10
    if s > 1.0:
        s = 1.0
    S = 180.0 * math.asin(s) / math.pi
    if S > 60:
        return round(S, 1)
    else:
        return round(S)


def _calc_tangent(dx):
    """ T scale """
    dx /= SCALE
    t = math.exp(dx)/10
    if t > 1.0:
        t = 1.0
    return round(180.0 * math.atan(t) / math.pi)


def _calc_ln(dx):
    return round(dx / SCALE)


class SlideRule():

    def __init__(self, canvas, path, parent=None):
        """ Handle launch from both within and without of Sugar environment. """
        SLIDES = {'C':[C_slide, self._calc_C], 'CI':[CI_slide, self._calc_CI],
                  'A':[A_slide, self._calc_A], 'K':[K_slide, self._calc_K],
                  'S':[S_slide, self._calc_S], 'T':[T_slide, self._calc_T],
                  'L':[L_slide, self._calc_L],
                  'LLn':[LLn_slide, self._calc_LLn],
                  'LL0':[LL0_slide, self._calc_LL0]}

        STATORS = {'D':[D_stator, self._calc_D, self._calc_D_result],
                   'DI':[DI_stator, self._calc_DI, self._calc_DI_result],
                   'B':[A_stator, self._calc_B, self._calc_B_result],
                   'K2':[K_stator, self._calc_K2, self._calc_K2_result],
                   'S2':[S_stator, self._calc_S2, self._calc_S2_result],
                   'T2':[T_stator, self._calc_T2, self._calc_T2_result],
                   'L2':[L_stator, self._calc_L2, self._calc_L2_result],
                   'LLn':[LLn_stator, self._calc_LLn2, self._calc_LLn2_result],
                   'LL0':[LL0_stator, self._calc_LL02, self._calc_LL02_result]}

        self.path = path
        self.activity = parent

        if parent is None:
            self.sugar = False
            self.canvas = canvas
            self.parent = None
        else:
            self.sugar = True
            self.canvas = canvas
            self.parent = parent
            parent.show_all()

        self.canvas.set_flags(gtk.CAN_FOCUS)
        self.canvas.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.canvas.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
        self.canvas.add_events(gtk.gdk.POINTER_MOTION_MASK)
        self.canvas.connect("expose-event", self._expose_cb)
        self.canvas.connect("button-press-event", self._button_press_cb)
        self.canvas.connect("button-release-event", self._button_release_cb)
        self.canvas.connect("motion-notify-event", self._mouse_move_cb)
        self.canvas.connect("key_press_event", self._keypress_cb)
        self.width = gtk.gdk.screen_width()
        self.height = gtk.gdk.screen_height()-GRID_CELL_SIZE
        self.sprites = Sprites(self.canvas)
        self.slides = []
        self.stators = []
        self.scale = 1

        _logger.debug("creating slides, stators, and reticule")
        self.results_label = Stator(self.sprites, self.path, 'label',
                                        int((self.width - 600) / 2),
                                        SCREENOFFSET + 4 * SHEIGHT,
                                        600, SHEIGHT)

        for slide in SLIDES:
            self.slides.append(self._make_slide(slide, SCREENOFFSET + SHEIGHT,
                SLIDES[slide][0], SLIDES[slide][1]))

        for stator in STATORS:
            self.stators.append(self._make_stator(stator,
                                                  SCREENOFFSET + 2 * SHEIGHT,
                STATORS[stator][0], STATORS[stator][1], STATORS[stator][2]))

        self.make_custom_slide('math.log(x, 10)', 'x', 'math.exp(x)', 1, 10, 1)

        self.reticule = Reticule(self.sprites, self.path, 'reticule',
                          150, SCREENOFFSET + SHEIGHT, 100, 2 * SHEIGHT)
        self.reticule.draw(2000)

        self.active_slide = self.name_to_slide('C')
        self.active_stator = self.name_to_stator('D')

        self.update_slide_labels()
        self.update_results_label()

        self.press = None
        self.last = None
        self.dragpos = 0

    def _expose_cb(self, win, event):
        # self.sprite_list.refresh(event)
        self.sprites.redraw_sprites()
        return True

    def _destroy_cb(self, win, event):
        gtk.main_quit()

    def _keypress_cb(self, area, event):
        """ Keypress: moving the slides with the arrow keys """
        k = gtk.gdk.keyval_name(event.keyval)
        if self.parent == None:
            return
        if k == 'a':
            self.parent.show_a()
        elif k == 'k':
            self.parent.show_k()
        elif k == 'c' or k == 'asterisk' or k == 'x':
            self.parent.show_c()
        elif k == 'i':
            self.parent.show_ci()
        elif k == 's':
            self.parent.show_s()
        elif k == 't':
            self.parent.show_t()
        elif k == 'l' or k == 'plus':
            self.parent.show_l()
        elif k == 'Left' or k == 'comma':
            self._move_slides(self.last, -1)
        elif k == 'Right' or k == 'period':
            self._move_slides(self.last, 1)
        elif k == 'Home' or k == 'Pause':
            self._move_slides(self.name_to_stator('D').spr,
                              -self.name_to_stator('D').spr.get_xy()[0])
        elif k == 'r':
            self.reticule.move(150, self.reticule.spr.get_xy()[1])
            self.update_slide_labels()
            self.update_results_label()
        elif k == 'Return' or k == 'BackSpace':
            self.parent.realign_cb()
            self.reticule.move(150, self.reticule.spr.get_xy()[1])
            self.update_slide_labels()
            self.update_results_label()
        return True

    def _make_slide(self, name, y, svg_engine, calculate=None):
        slide = Slide(self.sprites, self.path, name, 0, y, SWIDTH, SHEIGHT,
                      svg_engine, calculate)
        slide.spr.set_label('')
        slide.draw()
        return slide

    def _make_stator(self, name, y, svg_engine, calculate=None, result=None):
        stator = Stator(self.sprites, None, name, 0, y, SWIDTH, SHEIGHT,
                        svg_engine, calculate, result)
        stator.spr.set_label('')
        stator.draw()
        return stator

    def make_custom_slide(self, offset_text, label_text, calculate_text,
                          min_text, max_text, step_text):
        """ Create custom slide and stator from text entered on toolbar. """
        try:
            min = float(min_text)
        except ValueError:
            self.parent._min_entry.set_text('NaN')
            return
        try:
            max = float(max_text)
        except ValueError:
            self.parent._max_entry.set_text('NaN')
            return
        try:
            step = float(step_text)
        except ValueError:
            self.parent._step_entry.set_text('NaN')
            return

        # TODO: some sort of function error checking
        self.calculate_text = calculate_text

        def custom_offset_function(x):
            myf = "def f(x): return " + offset_text.replace('import','')
            userdefined = {}
            try:
                exec myf in globals(), userdefined
                return userdefined.values()[0](x)
            except:
                traceback.print_exc()
                return None

        def custom_label_function(x):
            myf = "def f(x): return " + label_text.replace('import','')
            userdefined = {}
            try:
                exec myf in globals(), userdefined
                return userdefined.values()[0](x)
            except:
                traceback.print_exc()
                return None

        custom_slide = CustomSlide(self.sprites, self.path, 'custom',
                                   0, SCREENOFFSET + SHEIGHT, Custom_slide,
                                   self._calc_custom,
                                   custom_offset_function,
                                   custom_label_function, min, max, step)
        custom_stator = CustomStator(self.sprites, 'custom2',
                                     0, SCREENOFFSET + SHEIGHT, Custom_stator,
                                     self._calc_custom2,
                                     self._calc_custom2_result,
                                     custom_offset_function,
                                     custom_label_function, min, max, step)
        
        if self.name_to_slide('custom').name == 'custom':
            i = self.slides.index(self.name_to_slide('custom'))
            active = False
            if self.active_slide == self.slides[i]:
                active = True
            self.slides[i].hide()
            self.slides[i] = custom_slide
            if active:
                self.active_slide = self.slides[i]
            self.parent.set_slide()
        else:
            self.slides.append(custom_slide)
        if self.name_to_stator('custom2').name == 'custom2':
            i = self.stators.index(self.name_to_stator('custom2'))
            active = False
            if self.active_stator == self.stators[i]:
                active = True
            self.stators[i].hide()
            self.stators[i] = custom_stator
            if active:
                self.active_stator = self.stators[i]
            self.parent.set_stator()
        else:
            self.stators.append(custom_stator)

    def name_to_slide(self, name):
        for slide in self.slides:
            if name == slide.name:
                return slide
        return self.slides[0]

    def name_to_stator(self, name):
        for stator in self.stators:
            if name == stator.name:
                return stator
        return self.stators[0]

    def sprite_in_stators(self, sprite):
        for stator in self.stators:
            if stator.match(sprite):
                return True
        return False

    def find_stator(self, sprite):
        for stator in self.stators:
            if stator.match(sprite):
                return stator
        return None

    def sprite_in_slides(self, sprite):
        for slide in self.slides:
            if slide.match(sprite):
                return True
        return False

    def find_slide(self, sprite):
        for slide in self.slides:
            if slide.match(sprite):
                return slide
        return None

    def _button_press_cb(self, win, event):
        win.grab_focus()
        x, y = map(int, event.get_coords())
        self.dragpos = x
        spr = self.sprites.find_sprite((x, y))
        self.press = spr
        return True

    def _mouse_move_cb(self, win, event):
        """ Drag a rule with the mouse. """
        if self.press is None:
            self.dragpos = 0
            return True
        win.grab_focus()
        x, y = map(int, event.get_coords())
        dx = x - self.dragpos
        self._move_slides(self.press, dx)
        self.dragpos = x

    def _move_slides(self, sprite, dx):
        if self.sprite_in_stators(sprite):
            for slide in self.slides:
                slide.move_relative(dx, 0)
            for stator in self.stators:
                stator.move_relative(dx, 0)
            self.reticule.move_relative(dx, 0)
        elif self.reticule.match(sprite):
            self.reticule.move_relative(dx, 0)
        elif self.sprite_in_slides(sprite):
            self.find_slide(sprite).move_relative(dx, 0)
        self.update_slide_labels()
        self.update_results_label()

    def _update_top(self, function):
        v_left = function()
        if self.active_stator.name == 'L2':
            v_right = 10 + v_left
        elif self.active_stator.name == 'D':
            v_right = v_left * 10.
        elif self.active_stator.name == 'B':
            v_right = v_left * 100.
        elif self.active_stator.name == 'K2':
            v_right = v_left * 1000.
        elif self.active_stator.name == 'DI':
            v_right = v_left / 10.
        elif self.active_stator.name == 'LLn2':
            v_right = round(math.log(10)) + v_left
        else:
            v_right = v_left
        for slide in self.slides:
            slide.tabs[LEFT].spr.set_label(str(v_left))
            slide.tabs[RIGHT].spr.set_label(str(v_right))

    def update_slide_labels(self):
        """ Based on the current alignment of the rules, calculate labels. """
        self._update_top(self.active_stator.calculate)
        self.reticule.tabs[BOTTOM].spr.set_label(
                str(self.active_stator.result()))
        self.reticule.tabs[TOP].spr.set_label(
            str(self.active_slide.calculate()))

    def _button_release_cb(self, win, event):
        if self.press == None:
            return True
        self.last = self.press
        self.press = None
        self.update_results_label()

    def update_results_label(self):
        """ Update toolbar label with results of calculation. """
        s = ''
        if self.active_stator.name == 'D':
            dx = self.name_to_stator('D').spr.get_xy()[0]
            S = self.active_slide.calculate()
            R = self._calc_D_result()
            if self.active_slide.name == 'A':
                if self.name_to_slide('A').spr.get_xy()[0] == dx:
                    s = " √ %0.2f = %0.2f\t\t%0.2f² = %0.2f" % (S, R, R, S)
            elif self.active_slide.name == 'K':
                if self.name_to_slide('K').spr.get_xy()[0] == dx:
                    s = " ∛ %0.2f = %0.2f\t\t%0.2f³ = %0.2f" % (S, R, R, S)
            elif self.active_slide.name == 'S':
                if self.name_to_slide('S').spr.get_xy()[0] == dx:
                    s = " sin(%0.2f) = %0.2f\t\tasin(%0.2f) = %0.2f" % \
                        (S, R/10, R/10, S)
            elif self.active_slide.name == 'T':
                if self.name_to_slide('T').spr.get_xy()[0] == dx:
                    s = " tan(%0.2f) = %0.2f\t\tatan(%0.2f) = %0.2f" % \
                        (S, R/10, R/10, S)
            elif self.active_slide.name == 'C':
                D = str(self._calc_D())
                s = "%s × %s = %s\t\t%s / %s = %s" % (D, S, R, R, S, D)
            elif self.active_slide.name == 'CI':
                D = str(self._calc_D())
                s = "%s / %s = %s\t\t%s × %s = %s" % (D, S, R/10, R/10, S, D)
        elif self.active_stator.name == 'L2':
            if self.active_slide.name == 'L':
                # use n dash to display a minus sign
                L2 = self._calc_L2()
                if L2 < 0:
                    L2str = "–" + str(-L2)
                else:
                    L2str = str(L2)

                L = self._calc_L()
                if L < 0:
                    operator1 = "–"
                    operator2 = "+"
                    Lstr = str(-L)
                else:
                    operator1 = "+"
                    operator2 = "–"
                    Lstr = str(L)

                LL = self._calc_L2_result()
                if LL < 0:
                    LLstr = "–" + str(-LL)
                else:
                    LLstr = str(LL)

                s = "%s %s %s = %s\t\t%s %s %s = %s" % (L2str, operator1, Lstr,
                                                        LLstr, LLstr,
                                                        operator2, Lstr, L2str)
        self.results_label.spr.set_label(s)

    def _top_slide_offset(self, x):
        """ Calcualate the offset between the top and bottom slides """
        x2, y2 = self.active_slide.spr.get_xy()
        return x2 - x

    # Calculate the value of individual slides and stators

    def _r_offset(self, slide):
        return self.reticule.spr.get_xy()[0] - slide.spr.get_xy()[0]

    def _calc_C(self):
        return _calc_log(self._r_offset(self.name_to_slide('C')))
        
    def _calc_D(self):
        return _calc_log(self._top_slide_offset(
                self.name_to_stator('D').spr.get_xy()[0]))

    def _calc_D_result(self):
        return _calc_log(self._r_offset(self.name_to_stator('D')))

    def _calc_CI(self):
        return _calc_inverse_log(self._r_offset(self.name_to_slide('CI')))

    def _calc_DI(self):
        return _calc_inverse_log(
            self._top_slide_offset(self.name_to_stator('DI').spr.get_xy()[0]))

    def _calc_DI_result(self):
        return _calc_inverse_log(self._r_offset(self.name_to_stator('DI')))

    def _calc_LLn(self):
        return _calc_ln(self._r_offset(self.name_to_slide('LLn')))

    def _calc_LLn2(self):
        return _calc_ln(self._top_slide_offset(
                self.name_to_stator('LLn2').spr.get_xy()[0]))

    def _calc_LLn2_result(self):
        return _calc_ln(self._r_offset(self.name_to_stator('D')))

    def _calc_LL0(self):
        return _calc_log_log(self._r_offset(self.name_to_slide('LL0')))

    def _calc_LL02(self):
        return _calc_log_log(self._top_slide_offset(
                self.name_to_stator('LL02').spr.get_xy()[0]))

    def _calc_LL02_result(self):
        return _calc_log_log(self._r_offset(self.name_to_stator('D')))

    def _calc_A(self):
        return _calc_log_squared(self._r_offset(self.name_to_slide('A')))

    def _calc_B(self):
         return _calc_log_squared(
             self._top_slide_offset(self.name_to_stator('B').spr.get_xy()[0]))

    def _calc_B_result(self):
         return _calc_log_squared(self._r_offset(self.name_to_stator('B')))

    def _calc_S(self):
        return _calc_sine(self._r_offset(self.name_to_slide('S')))

    def _calc_S2(self):
        return _calc_sine(self._top_slide_offset(
                self.name_to_stator('S2').spr.get_xy()[0]))

    def _calc_S2_result(self):
        return _calc_sine(self._r_offset(self.name_to_stator('S2')))

    def _calc_T(self):
        return _calc_tangent(self._r_offset(self.name_to_slide('T')))

    def _calc_T2(self):
        return _calc_tangent(self._top_slide_offset(
                self.name_to_stator('T2').spr.get_xy()[0]))

    def _calc_T2_result(self):
        return _calc_tangent(self._r_offset(self.name_to_stator('T2')))

    def _calc_K(self):
        return _calc_log_cubed(self._r_offset(self.name_to_slide('K')))

    def _calc_K2(self):
        return _calc_log_cubed(self._top_slide_offset(
                self.name_to_stator('K2').spr.get_xy()[0]))

    def _calc_K2_result(self):
        return _calc_log_cubed(self._r_offset(self.name_to_stator('K2')))

    def _calc_L(self):
        return _calc_linear(self._r_offset(self.name_to_slide('L')))

    def _calc_L2(self):
        return _calc_linear(self._top_slide_offset(
                self.name_to_stator('L2').spr.get_xy()[0]))

    def _calc_L2_result(self):
        return _calc_linear(self._r_offset(self.name_to_stator('L2')))

    def _calc_custom(self):
        return self.custom_calc(self._r_offset(self.name_to_slide('custom')))

    def _calc_custom2(self):
        return self.custom_calc(self._top_slide_offset(
                self.name_to_stator('custom2').spr.get_xy()[0]))

    def _calc_custom2_result(self):
        return self.custom_calc(self._r_offset(self.name_to_stator('custom2')))

    def custom_calc(self, dx):
        myf = "def f(x): return " + self.calculate_text.replace('import','')
        userdefined = {}
        try:
            exec myf in globals(), userdefined
            return round(userdefined.values()[0](dx / SCALE))
        except:
            traceback.print_exc()
            return None
