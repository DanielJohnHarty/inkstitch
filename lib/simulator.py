import sys
import wx
from wx.lib.intctrl import IntCtrl
import time
from itertools import izip

from .svg import color_block_to_point_lists, PIXELS_PER_MM
from .i18n import _

# L10N command label at bottom of simulator window
COMMAND_NAMES = [_("STITCH"), _("JUMP"), _("TRIM"), _("STOP"), _("COLOR CHANGE")]

STITCH = 0
JUMP = 1
TRIM = 2
STOP = 3
COLOR_CHANGE = 4


class ControlPanel(wx.Panel):
    """"""
    def __init__(self, parent, *args, **kwargs):
        """"""
        self.parent = parent
        self.stitch_plan = kwargs.pop('stitch_plan')
        self.target_stitches_per_second = kwargs.pop('stitches_per_second')
        self.target_duration = kwargs.pop('target_duration')
        kwargs['style'] = wx.BORDER_SUNKEN
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.drawing_panel = None
        self.num_stitches = 1
        self.current_stitch = 1
        self.speed = 1
        self.direction = 1

        # Widgets
        self.btnMinus = wx.Button(self, -1, label='-')
        self.btnMinus.Bind(wx.EVT_BUTTON, self.animation_slow_down)
        self.btnPlus = wx.Button(self, -1, label='+')
        self.btnPlus.Bind(wx.EVT_BUTTON, self.animation_speed_up)
        self.btnBackwardStitch = wx.Button(self, -1, label='<|')
        self.btnBackwardStitch.Bind(wx.EVT_BUTTON, self.animation_one_stitch_backward)
        self.btnForwardStitch = wx.Button(self, -1, label='|>')
        self.btnForwardStitch.Bind(wx.EVT_BUTTON, self.animation_one_stitch_forward)
        self.directionBtn = wx.Button(self, -1, label='<<')
        self.directionBtn.Bind(wx.EVT_BUTTON, self.on_direction_button)
        self.pauseBtn = wx.Button(self, -1, label=_('Pause'))
        self.pauseBtn.Bind(wx.EVT_BUTTON, self.on_pause_start_button)
        self.restartBtn = wx.Button(self, -1, label=_('Restart'))
        self.restartBtn.Bind(wx.EVT_BUTTON, self.animation_restart)
        self.quitBtn = wx.Button(self, -1, label=_('Quit'))
        self.quitBtn.Bind(wx.EVT_BUTTON, self.animation_quit)
        self.slider = wx.Slider(self, -1, value=1, minValue=1, maxValue=2,
                                style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.slider.Bind(wx.EVT_SLIDER, self.on_slider)
        self.stitchBox = IntCtrl(self, -1, value=1, min=1, max=2, limited=True, allow_none=False)
        self.stitchBox.Bind(wx.EVT_TEXT, self.on_stitch_box)
        self.speedST = wx.StaticText(self, -1, label='', style=wx.ALIGN_CENTER)
        self.commandST = wx.StaticText(self, -1, label='', style=wx.ALIGN_CENTER)

        # Layout
        self.vbSizer = vbSizer = wx.BoxSizer(wx.VERTICAL)
        self.hbSizer1 = hbSizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbSizer2 = hbSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hbSizer1.Add(self.slider, 1, wx.EXPAND | wx.ALL, 3)
        hbSizer1.Add(self.stitchBox, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        vbSizer.Add(hbSizer1, 1, wx.EXPAND | wx.ALL, 3)
        hbSizer2.Add(self.speedST, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
        hbSizer2.AddStretchSpacer(prop=1)
        hbSizer2.Add(self.commandST, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
        hbSizer2.AddStretchSpacer(prop=1)
        hbSizer2.Add(self.btnMinus, 0, wx.ALL, 2)
        hbSizer2.Add(self.btnPlus, 0, wx.ALL, 2)
        hbSizer2.Add(self.btnBackwardStitch, 0, wx.ALL, 2)
        hbSizer2.Add(self.btnForwardStitch, 0, wx.ALL, 2)
        hbSizer2.Add(self.directionBtn, 0, wx.EXPAND | wx.ALL, 2)
        hbSizer2.Add(self.pauseBtn, 0, wx.EXPAND | wx.ALL, 2)
        hbSizer2.Add(self.restartBtn, 0, wx.EXPAND | wx.ALL, 2)
        hbSizer2.Add(self.quitBtn, 0, wx.EXPAND | wx.ALL, 2)
        vbSizer.Add(hbSizer2, 0, wx.EXPAND | wx.ALL, 3)
        self.SetSizer(vbSizer)

        # Keyboard Shortcuts
        shortcut_keys = [
            (wx.ACCEL_NORMAL, wx.WXK_RIGHT, self.animation_forward),
            (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_RIGHT, self.animation_forward),
            (wx.ACCEL_NORMAL, wx.WXK_LEFT, self.animation_reverse),
            (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_LEFT, self.animation_reverse),
            (wx.ACCEL_NORMAL, wx.WXK_UP, self.animation_speed_up),
            (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_UP, self.animation_speed_up),
            (wx.ACCEL_NORMAL, wx.WXK_DOWN, self.animation_slow_down),
            (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_DOWN, self.animation_slow_down),
            (wx.ACCEL_NORMAL, ord('+'), self.animation_one_stitch_forward),
            (wx.ACCEL_NORMAL, ord('='), self.animation_one_stitch_forward),
            (wx.ACCEL_SHIFT, ord('='), self.animation_one_stitch_forward),
            (wx.ACCEL_NORMAL, wx.WXK_ADD, self.animation_one_stitch_forward),
            (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_ADD, self.animation_one_stitch_forward),
            (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_UP, self.animation_one_stitch_forward),
            (wx.ACCEL_NORMAL, ord('-'), self.animation_one_stitch_backward),
            (wx.ACCEL_NORMAL, ord('_'), self.animation_one_stitch_backward),
            (wx.ACCEL_NORMAL, wx.WXK_SUBTRACT, self.animation_one_stitch_backward),
            (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_SUBTRACT, self.animation_one_stitch_backward),
            (wx.ACCEL_NORMAL, ord('r'), self.animation_restart),
            (wx.ACCEL_NORMAL, ord('p'), self.on_pause_start_button),
            (wx.ACCEL_NORMAL, wx.WXK_SPACE, self.on_pause_start_button),
            (wx.ACCEL_NORMAL, ord('q'), self.animation_quit)]

        accel_entries = []

        for shortcut_key in shortcut_keys:
            eventId = wx.NewId()
            accel_entries.append((shortcut_key[0], shortcut_key[1], eventId))
            self.Bind(wx.EVT_MENU, shortcut_key[2], id=eventId)

        accel_table = wx.AcceleratorTable(accel_entries)
        self.SetAcceleratorTable(accel_table)
        self.SetFocus()

    def set_drawing_panel(self, drawing_panel):
        self.drawing_panel = drawing_panel
        self.drawing_panel.set_speed(self.speed)

    def set_num_stitches(self, num_stitches):
        if num_stitches < 2:
            # otherwise the slider and intctrl get mad
            num_stitches = 2
        self.num_stitches = num_stitches
        self.stitchBox.SetMax(num_stitches)
        self.slider.SetMax(num_stitches)
        self.choose_speed()

    def choose_speed(self):
        if self.target_duration:
            self.set_speed(int(self.num_stitches / float(self.target_duration)))
        else:
            self.set_speed(self.target_stitches_per_second)

    def animation_forward(self, event=None):
        self.directionBtn.SetLabel("<<")
        self.drawing_panel.forward()
        self.direction = 1
        self.update_speed_text()

    def animation_reverse(self, event=None):
        self.directionBtn.SetLabel(">>")
        self.drawing_panel.reverse()
        self.direction = -1
        self.update_speed_text()

    def on_direction_button(self, event):
        evtObj = event.GetEventObject()
        lbl = evtObj.GetLabel()
        if self.direction == 1:
            self.animation_forward()
        else:
            self.animation_reverse()

    def set_speed(self, speed):
        self.speed = int(max(speed, 1))
        self.update_speed_text()

        if self.drawing_panel:
            self.drawing_panel.set_speed(self.speed)

    def update_speed_text(self):
        self.speedST.SetLabel(_('Speed: %d stitches/sec') % (self.speed * self.direction))
        self.hbSizer2.Layout()


    def on_slider(self, event):
        stitch = event.GetEventObject().GetValue()
        self.stitchBox.SetValue(stitch)

        if self.drawing_panel:
            self.drawing_panel.set_current_stitch(stitch)

    def on_current_stitch(self, stitch, command):
        if self.current_stitch != stitch:
            self.current_stitch = stitch
            self.slider.SetValue(stitch)
            self.stitchBox.SetValue(stitch)
            self.commandST.SetLabel(COMMAND_NAMES[command])

    def on_stitch_box(self, event):
        stitch = self.stitchBox.GetValue()
        self.slider.SetValue(stitch)

        if self.drawing_panel:
            self.drawing_panel.set_current_stitch(stitch)

    def animation_slow_down(self, event):
        """"""
        self.set_speed(self.speed / 2.0)

    def animation_speed_up(self, event):
        """"""
        self.set_speed(self.speed * 2.0)

    def animation_pause(self, event=None):
        self.drawing_panel.stop()

    def animation_start(self, event=None):
        self.drawing_panel.go()

    def on_start(self):
        self.pauseBtn.SetLabel(_('Pause'))

    def on_stop(self):
        self.pauseBtn.SetLabel(_('Start'))

    def on_pause_start_button(self, event):
        """"""
        if self.pauseBtn.GetLabel() == _('Pause'):
            self.animation_pause()
        else:
            self.animation_start()

    def animation_one_stitch_forward(self, event):
        self.drawing_panel.one_stitch_forward()

    def animation_one_stitch_backward(self, event):
        self.drawing_panel.one_stitch_backward()

    def animation_quit(self, event):
        self.parent.quit()

    def animation_restart(self, event):
        self.drawing_panel.restart()

class DrawingPanel(wx.Panel):
    """"""

    # render no faster than this many frames per second
    TARGET_FPS = 30

    # It's not possible to specify a line thickness less than 1 pixel, even
    # though we're drawing anti-aliased lines.  To get around this we scale
    # the stitch positions up by this factor and then scale down by a
    # corresponding amount during rendering.
    PIXEL_DENSITY = 10

    # Line width in pixels.
    LINE_THICKNESS = 0.4

    def __init__(self, *args, **kwargs):
        """"""
        self.stitch_plan = kwargs.pop('stitch_plan')
        self.control_panel = kwargs.pop('control_panel')
        kwargs['style'] = wx.BORDER_SUNKEN
        wx.Panel.__init__(self, *args, **kwargs)

        self.SetBackgroundColour('#FFFFFF')
        self.SetDoubleBuffered(True)

        self.animating = False
        self.target_frame_period = 1.0 / self.TARGET_FPS
        self.last_frame_duration = 0
        self.direction = 1
        self.current_stitch = 0
        self.black_pen = wx.Pen((128, 128, 128))
        self.width = 0
        self.height = 0
        self.loaded = False

        # desired simulation speed in stitches per second
        self.speed = 16

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.choose_zoom_and_pan)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_mouse_button_down)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)

        # wait for layouts so that panel size is set
        wx.CallLater(50, self.load, self.stitch_plan)

    def clamp_current_stitch(self):
        if self.current_stitch < 1:
            self.current_stitch = 1
        elif self.current_stitch > self.num_stitches:
            self.current_stitch = self.num_stitches

    def stop_if_at_end(self):
        if self.direction == -1 and self.current_stitch == 1:
            self.stop()
        elif self.direction == 1 and self.current_stitch == self.num_stitches:
            self.stop()

    def start_if_not_at_end(self):
        if self.direction == -1 and self.current_stitch > 1:
            self.go()
        elif self.direction == 1 and self.current_stitch < self.num_stitches:
            self.go()

    def animate(self):
        if not self.animating:
            return

        frame_time = max(self.target_frame_period, self.last_frame_duration)

        # No sense in rendering more frames per second than our desired stitches
        # per second.
        frame_time = max(frame_time, 1.0 / self.speed)

        stitch_increment = int(self.speed * frame_time)

        #print >> sys.stderr, time.time(), "animate", self.current_stitch, stitch_increment, self.last_frame_duration, frame_time

        self.set_current_stitch(self.current_stitch + self.direction * stitch_increment)
        wx.CallLater(int(1000 * frame_time), self.animate)

    def OnPaint(self, e):
        if not self.loaded:
            return

        dc = wx.PaintDC(self)
        canvas = wx.GraphicsContext.Create(dc)

        transform = canvas.GetTransform()
        transform.Translate(*self.pan)
        transform.Scale(self.zoom / self.PIXEL_DENSITY, self.zoom / self.PIXEL_DENSITY)
        #transform.Translate(self.pan[0] * self.PIXEL_DENSITY, self.pan[1] * self.PIXEL_DENSITY)
        canvas.SetTransform(transform)

        stitch = 0
        last_stitch = None

        start = time.time()
        for pen, stitches in izip(self.pens, self.stitch_blocks):
            canvas.SetPen(pen)
            if stitch + len(stitches) < self.current_stitch:
                stitch += len(stitches)
                canvas.DrawLines(stitches)
                last_stitch = stitches[-1]
            else:
                stitches = stitches[:self.current_stitch - stitch]
                if len(stitches) > 1:
                    canvas.DrawLines(stitches)
                last_stitch = stitches[-1]
                break
        self.last_frame_duration = time.time() - start

        if last_stitch:
            x = last_stitch[0]
            y = last_stitch[1]
            x, y = transform.TransformPoint(float(x), float(y))
            canvas.SetTransform(canvas.CreateMatrix())
            crosshair_radius = 10
            canvas.SetPen(self.black_pen)
            canvas.DrawLines(((x - crosshair_radius, y), (x + crosshair_radius, y)))
            canvas.DrawLines(((x, y - crosshair_radius), (x, y + crosshair_radius)))

    def clear(self):
        dc = wx.ClientDC(self)
        dc.Clear()

    def load(self, stitch_plan):
        self.current_stitch = 1
        self.direction = 1
        self.last_frame_duration = 0
        self.num_stitches = stitch_plan.num_stitches
        self.control_panel.set_num_stitches(self.num_stitches)
        self.minx, self.miny, self.maxx, self.maxy = stitch_plan.bounding_box
        self.width = self.maxx - self.minx
        self.height = self.maxy - self.miny
        self.parse_stitch_plan(stitch_plan)
        self.choose_zoom_and_pan()
        self.set_current_stitch(0)
        self.loaded = True
        self.go()

    def choose_zoom_and_pan(self, event=None):
        # ignore if called before we load the stitch plan
        if not self.width or not self.height:
            return

        panel_width, panel_height = self.GetClientSize()

        # add some padding to make stitches at the edge more visible
        width_ratio = panel_width / float(self.width + 10)
        height_ratio = panel_height / float(self.height + 10)
        self.zoom = min(width_ratio, height_ratio)

        # center the design
        self.pan = ((panel_width - self.zoom * self.width) / 2.0,
                    (panel_height - self.zoom * self.height) / 2.0)

    def stop(self):
        self.animating = False
        self.control_panel.on_stop()

    def go(self):
        if not self.loaded:
            return

        if not self.animating:
            self.animating = True
            self.animate()
            self.control_panel.on_start()

    def color_to_pen(self, color):
        # We draw the thread with a thickness of 0.1mm.  Real thread has a
        # thickness of ~0.4mm, but if we did that, we wouldn't be able to
        # see the individual stitches.
        return wx.Pen(color.visible_on_white.rgb, width=int(0.1 * PIXELS_PER_MM * self.PIXEL_DENSITY))

    def parse_stitch_plan(self, stitch_plan):
        self.pens = []
        self.stitch_blocks = []

        # There is no 0th stitch, so add a place-holder.
        self.commands = [None]

        for color_block in stitch_plan:
            pen = self.color_to_pen(color_block.color)
            stitch_block = []

            for stitch in color_block:
                # trim any whitespace on the left and top and scale to the
                # pixel density
                stitch_block.append((self.PIXEL_DENSITY * (stitch.x - self.minx),
                                     self.PIXEL_DENSITY * (stitch.y - self.miny)))

                if stitch.trim:
                    self.commands.append(TRIM)
                elif stitch.jump:
                    self.commands.append(JUMP)
                elif stitch.stop:
                    self.commands.append(STOP)
                elif stitch.color_change:
                    self.commands.append(COLOR_CHANGE)
                else:
                    self.commands.append(STITCH)

                if stitch.trim or stitch.stop or stitch.color_change:
                    self.pens.append(pen)
                    self.stitch_blocks.append(stitch_block)
                    stitch_block = []

            if stitch_block:
                self.pens.append(pen)
                self.stitch_blocks.append(stitch_block)

    def set_speed(self, speed):
        self.speed = speed

    def forward(self):
        self.direction = 1
        self.start_if_not_at_end()

    def reverse(self):
        self.direction = -1
        self.start_if_not_at_end()

    def set_current_stitch(self, stitch):
        self.current_stitch = stitch
        self.clamp_current_stitch()
        self.control_panel.on_current_stitch(self.current_stitch, self.commands[self.current_stitch])
        self.stop_if_at_end()
        self.Refresh()

    def restart(self):
        if self.direction == 1:
            self.current_stitch = 1
        elif self.direction == -1:
            self.current_stitch = self.num_stitches

        self.go()

    def one_stitch_forward(self):
        self.set_current_stitch(self.current_stitch + 1)

    def one_stitch_backward(self):
        self.set_current_stitch(self.current_stitch - 1)

    def on_left_mouse_button_down(self, event):
        self.CaptureMouse()
        self.drag_start = event.GetPosition()
        self.drag_original_pan = self.pan
        self.Bind(wx.EVT_MOTION, self.on_drag)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.on_drag_end)
        self.Bind(wx.EVT_LEFT_UP, self.on_drag_end)

    def on_drag(self, event):
        if self.HasCapture() and event.Dragging():
            delta = event.GetPosition()
            offset = (delta[0] - self.drag_start[0], delta[1] - self.drag_start[1])
            self.pan = (self.drag_original_pan[0] + offset[0], self.drag_original_pan[1] + offset[1])
            self.Refresh()

    def on_drag_end(self, event):
        if self.HasCapture():
            self.ReleaseMouse()

        self.Unbind(wx.EVT_MOTION)
        self.Unbind(wx.EVT_MOUSE_CAPTURE_LOST)
        self.Unbind(wx.EVT_LEFT_UP)

    def on_mouse_wheel(self, event):
        if event.GetWheelRotation() > 0:
            zoom_delta = 1.03
        else:
            zoom_delta = 0.97

        # If we just change the zoom, the design will appear to move on the
        # screen.  We have to adjust the pan to compensate.  We want to keep
        # the part of the design under the mouse pointer in the same spot
        # after we zoom, so that we appar to be zooming centered on the
        # mouse pointer.

        # This will create a matrix that takes a point in the design and
        # converts it to screen coordinates:
        matrix = wx.AffineMatrix2D()
        matrix.Translate(*self.pan)
        matrix.Scale(self.zoom, self.zoom)

        # First, figure out where the mouse pointer is in the coordinate system
        # of the design:
        pos = event.GetPosition()
        inverse_matrix = wx.AffineMatrix2D()
        inverse_matrix.Set(*matrix.Get())
        inverse_matrix.Invert()
        pos = inverse_matrix.TransformPoint(*pos)

        # Next, see how that point changes position on screen before and after
        # we apply the zoom change:
        x_old, y_old = matrix.TransformPoint(*pos)
        matrix.Scale(zoom_delta, zoom_delta)
        x_new, y_new = matrix.TransformPoint(*pos)
        x_delta = x_new - x_old
        y_delta = y_new - y_old

        # Finally, compensate for that change in position:
        self.pan = (self.pan[0] - x_delta, self.pan[1] - y_delta)


        self.zoom *= zoom_delta


        self.Refresh()


class SimulatorPanel(wx.Panel):
    """"""
    def __init__(self, parent, *args, **kwargs):
        """"""
        self.parent = parent
        stitch_plan = kwargs.pop('stitch_plan')
        target_duration = kwargs.pop('target_duration')
        stitches_per_second = kwargs.pop('stitches_per_second')
        kwargs['style'] = wx.BORDER_SUNKEN
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.cp = ControlPanel(self,
                               stitch_plan=stitch_plan,
                               stitches_per_second=stitches_per_second,
                               target_duration=target_duration)
        self.dp = DrawingPanel(self, stitch_plan=stitch_plan, control_panel=self.cp)
        self.cp.set_drawing_panel(self.dp)

        vbSizer = wx.BoxSizer(wx.VERTICAL)
        vbSizer.Add(self.dp, 1, wx.EXPAND | wx.ALL, 2)
        vbSizer.Add(self.cp, 0, wx.EXPAND | wx.ALL, 2)
        self.SetSizer(vbSizer)

    def quit(self):
        self.parent.quit()

    def go(self):
        self.dp.go()

    def stop(self):
        self.dp.stop()

    def load(self, stitch_plan):
        self.dp.load(stitch_plan)

    def clear(self):
        self.dp.clear()


class EmbroiderySimulator(wx.Frame):
    def __init__(self, *args, **kwargs):
        self.on_close_hook = kwargs.pop('on_close', None)
        stitch_plan = kwargs.pop('stitch_plan', None)
        stitches_per_second = kwargs.pop('stitches_per_second', 16)
        target_duration = kwargs.pop('target_duration', None)
        wx.Frame.__init__(self, *args, **kwargs)

        self.simulator_panel = SimulatorPanel(self,
                                              stitch_plan=stitch_plan,
                                              target_duration=target_duration,
                                              stitches_per_second=stitches_per_second)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def quit(self):
        self.Close()

    def on_close(self, event):
        self.simulator_panel.stop()

        if self.on_close_hook:
            self.on_close_hook()

        self.Destroy()

    def go(self):
        self.simulator_panel.go()

    def stop(self):
        self.simulator_panel.stop()

    def load(self, stitch_plan):
        self.simulator_panel.load(stitch_plan)

    def clear(self):
        self.simulator_panel.clear()
