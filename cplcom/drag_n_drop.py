
from kivy.properties import OptionProperty, ObjectProperty, NumericProperty, \
    StringProperty, ListProperty, DictProperty, BooleanProperty
from kivy.factory import Factory
from kivy.event import EventDispatcher
from kivy.uix.widget import Widget
from kivy.graphics import Fbo, ClearBuffers, ClearColor, Scale, Translate
from kivy.graphics.texture import Texture
from kivy.lang.builder import Builder
from kivy.core.window import Window
from kivy.config import Config

from cplcom.utils import collide_parent_tree

_drag_distance = 0
if Config:
    _drag_distance = '{}sp'.format(Config.getint('widgets', 'scroll_distance'))


class DragableObjectBehavior(object):

    drag_controller = ObjectProperty(None)

    drag_widget = ObjectProperty(None)

    drag_cls = StringProperty('')

    _drag_touch = None

    def initiate_drag(self):
        pass

    def complete_drag(self):
        pass

    def _touch_uid(self):
        return '{}.{}'.format(self.__class__.__name__, self.uid)

    def on_touch_down(self, touch):
        uid = self._touch_uid()
        if uid in touch.ud:
            return touch.ud[uid]

        if super(DragableObjectBehavior, self).on_touch_down(touch):
            touch.ud[uid] = False
            return True

        x, y = touch.pos
        if not self.collide_point(x, y):
            touch.ud[uid] = False
            return False

        if self._drag_touch or ('button' in touch.profile and
                                touch.button.startswith('scroll')):
            touch.ud[uid] = False
            return False

        self._drag_touch = touch
        touch.grab(self)
        touch.ud[uid] = True
        return self.drag_controller.drag_down(self, touch)

    def on_touch_move(self, touch):
        uid = self._touch_uid()
        if uid not in touch.ud:
            touch.ud[uid] = False
            return super(DragableObjectBehavior, self).on_touch_move(touch)

        if not touch.ud[uid]:
            return super(DragableObjectBehavior, self).on_touch_move(touch)

        if touch.grab_current is not self:
            return False

        return self.drag_controller.drag_move(self, touch)

    def on_touch_up(self, touch):
        uid = self._touch_uid()
        if uid not in touch.ud:
            touch.ud[uid] = False
            return super(DragableObjectBehavior, self).on_touch_up(touch)

        if not touch.ud[uid]:
            return super(DragableObjectBehavior, self).on_touch_up(touch)

        if touch.grab_current is not self:
            return False

        touch.ungrab(self)
        self._drag_touch = None
        return self.drag_controller.drag_up(self, touch)


class PreviewWidget(Widget):

    preview_texture = ObjectProperty(None)


class SpacerWidget(Widget):
    pass

Builder.load_string('''
<PreviewWidget>:
    canvas:
        Color:
            rgba: .2, .2, .2, 1
        Rectangle:
            size: self.size
            pos: self.pos
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            size: self.size
            pos: self.pos
            texture: self.preview_texture

<SpacerWidget>:
    canvas:
        Color:
            rgba: .2, .2, .2, 1
        Rectangle:
            size: self.size
            pos: self.pos
''')


class DragableController(EventDispatcher):

    drag_distance = NumericProperty(_drag_distance)

    preview_widget = None

    preview_pixels = None

    widget_dragged = None

    touch_dx = 0

    touch_dy = 0

    dragging = False

    start_widget_pos = 0, 0

    def __init__(self, **kwargs):
        super(DragableController, self).__init__(**kwargs)
        self.preview_widget = PreviewWidget(size_hint=(None, None))

    def _reload_texture(self, texture):
        if self.preview_pixels:
            texture.blit_buffer(
                self.preview_pixels, colorfmt='rgba', bufferfmt='ubyte')
        else:
            texture.remove_reload_observer(self._reload_texture)

    def prepare_preview_widget(self, source_widget):
        size = source_widget.size
        widget = self.preview_widget

        # get the pixels from the source widget
        if source_widget.parent is not None:
            canvas_parent_index = source_widget.parent.canvas.indexof(
                source_widget.canvas)
            if canvas_parent_index > -1:
                source_widget.parent.canvas.remove(source_widget.canvas)

        fbo = Fbo(size=size, with_stencilbuffer=False)

        with fbo:
            ClearColor(0, 0, 0, 1)
            ClearBuffers()
            Scale(1, -1, 1)
            Translate(
                -source_widget.x, -source_widget.y - source_widget.height, 0)

        fbo.add(source_widget.canvas)
        fbo.draw()
        self.preview_pixels = fbo.texture.pixels
        fbo.remove(source_widget.canvas)

        if source_widget.parent is not None and canvas_parent_index > -1:
            source_widget.parent.canvas.insert(
                canvas_parent_index, source_widget.canvas)

        widget.size = size
        texture = widget.preview_texture = Texture.create(
            size=size, colorfmt='RGBA', bufferfmt='ubyte')
        texture.flip_vertical()
        texture.add_reload_observer(self._reload_texture)
        self._reload_texture(texture)

    def clean_dragging(self):
        if not self.preview_pixels:
            return

        self.preview_pixels = None
        widget = self.preview_widget
        if widget.parent:
            widget.parent.remove_widget(widget)

    def drag_down(self, source, touch):
        self.clean_dragging()
        self.widget_dragged = source
        self.prepare_preview_widget(source.drag_widget or source)
        self.touch_dx = self.touch_dy = 0
        self.dragging = False
        self.preview_widget.canvas.opacity = 0
        Window.add_widget(self.preview_widget)
        self.start_widget_pos = self.preview_widget.pos = \
            source.to_window(*source.pos)
        return False

    def drag_move(self, source, touch):
        if not self.dragging:
            self.touch_dx += abs(touch.dx)
            self.touch_dy += abs(touch.dy)
            if (self.touch_dx ** 2 + self.touch_dy ** 2) ** .5 \
                    > self.drag_distance:
                self.dragging = True
                self.preview_widget.canvas.opacity = .4
                touch.ud['drag_cls'] = source.drag_cls
                touch.ud['drag_widget'] = source
                source.initiate_drag()
            else:
                return False

        x, y = self.start_widget_pos
        x += touch.x - touch.ox
        y += touch.y - touch.oy
        self.preview_widget.pos = x, y
        return False

    def drag_up(self, source, touch):
        if not self.dragging:
            self.clean_dragging()
            return False
        self.clean_dragging()
        self.dragging = False
        source.complete_drag()
        self.widget_dragged = None
        return False


class DragableLayoutBehavior(object):

    spacer_props = DictProperty({})

    _spacer_widget = None

    drag_classes = ListProperty([])

    drag_append_end = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(DragableLayoutBehavior, self).__init__(**kwargs)
        self._spacer_widget = SpacerWidget()
        self.fbind('spacer_props', self._track_spacer_props)
        self._track_spacer_props()

    def _track_spacer_props(self, *largs):
        for key, value in self.spacer_props.items():
            setattr(self._spacer_widget, key, value)

    def _touch_uid(self):
        return '{}.{}'.format(self.__class__.__name__, self.uid)

    def compare_pos_to_widget(self, widget, pos):
        return 'before'

    def get_widget_under_drag(self, x, y):
        for widget in self.children:
            if widget.collide_point(x, y):
                return widget
        return None

    def handle_drag_release(self, index, drag_widget):
        pass

    def on_touch_move(self, touch):
        spacer = self._spacer_widget
        if touch.grab_current is not self:
            if not touch.ud.get(self._touch_uid()):
                # we haven't dealt with this before
                if self.collide_point(*touch.pos) and \
                        touch.ud.get('drag_cls') in self.drag_classes:
                    if super(DragableLayoutBehavior, self).on_touch_move(touch):
                        return True
                    touch.grab(self)
                    touch.ud[self._touch_uid()] = True
                    x, y = touch.pos
                else:
                    return super(DragableLayoutBehavior, self).on_touch_move(touch)
            else:
                # we have dealt with this touch before, do it when grab_current
                return True
        else:
            x, y = touch.pos
            if touch.ud.get('drag_cls') not in self.drag_classes or \
                    not collide_parent_tree(self, x, y):
                touch.ungrab(self)
                del touch.ud[self._touch_uid()]
                if spacer.parent:
                    self.remove_widget(spacer)
                return False
            if super(DragableLayoutBehavior, self).on_touch_move(touch):
                touch.ungrab(self)
                del touch.ud[self._touch_uid()]
                if spacer.parent:
                    self.remove_widget(spacer)
                return True

        if self.drag_append_end:
            if not spacer.parent:
                self.add_widget(spacer)
            return True

        widget = self.get_widget_under_drag(x, y)
        if widget == spacer:
            return True

        if widget is None:
            if spacer.parent:
                self.remove_widget(spacer)
            self.add_widget(spacer)
            return True

        i = self.children.index(widget)
        j = None
        if self.compare_pos_to_widget(widget, (x, y)) == 'before':
            if i == len(self.children) - 1 or self.children[i + 1] != spacer:
                j = i + 1
        else:
            if not i or self.children[i - 1] != spacer:
                j = i

        if j is not None:
            if spacer.parent:
                i = self.children.index(spacer)
                self.remove_widget(spacer)
                if i < j:
                    j -= 1
            self.add_widget(spacer, index=j)
        return True

    def on_touch_up(self, touch):
        spacer = self._spacer_widget
        if touch.grab_current is not self:
            if not touch.ud.get(self._touch_uid()):
                # we haven't dealt with this before
                if self.collide_point(*touch.pos) and \
                        touch.ud.get('drag_cls') in self.drag_classes:
                    if super(DragableLayoutBehavior, self).on_touch_up(touch):
                        return True
                    x, y = touch.pos
                else:
                    return super(DragableLayoutBehavior, self).on_touch_up(touch)
            else:
                # we have dealt with this touch before, do it when grab_current
                return True
        else:
            touch.ungrab(self)
            del touch.ud[self._touch_uid()]
            x, y = touch.pos
            if touch.ud.get('drag_cls') not in self.drag_classes or \
                    not collide_parent_tree(self, x, y):
                if spacer.parent:
                    self.remove_widget(spacer)
                return False
            if super(DragableLayoutBehavior, self).on_touch_up(touch):
                if spacer.parent:
                    self.remove_widget(spacer)
                return True

        if self.drag_append_end:
            if spacer.parent:
                self.remove_widget(spacer)
            self.handle_drag_release(
                len(self.children), touch.ud['drag_widget'])
            return True

        widget = self.get_widget_under_drag(x, y)
        if widget == spacer:
            index = self.children.index(spacer)
        elif widget is None:
            index = len(self.children)
        else:
            if self.compare_pos_to_widget(widget, (x, y)) == 'before':
                index = self.children.index(widget) + 1
            else:
                index = self.children.index(widget)

        if spacer.parent:
            i = self.children.index(spacer)
            self.remove_widget(spacer)
            if i < index:
                index -= 1

        self.handle_drag_release(index, touch.ud['drag_widget'])
        return True

Factory.register('DragableObjectBehavior', DragableObjectBehavior)
Factory.register('DragableController', DragableController)
Factory.register('DragableLayoutBehavior', DragableLayoutBehavior)

if __name__ == '__main__':
    from kivy.app import runTouchApp
    from kivy.uix.label import Label
    from kivy.uix.boxlayout import BoxLayout
    controller = DragableController()

    class DragableBoxLayout(DragableLayoutBehavior, BoxLayout):

        def compare_pos_to_widget(self, widget, pos):
            if self.orientation == 'vertical':
                return 'before' if pos[1] >= widget.center_y else 'after'
            return 'before' if pos[0] < widget.center_x else 'after'

        def handle_drag_release(self, index, drag_widget):
            self.add_widget(drag_widget, index)

    class DragLabel(DragableObjectBehavior, Label):

        def __init__(self, **kwargs):
            super(DragLabel, self).__init__(**kwargs)
            self.drag_controller = controller
            self.drag_cls = 'label'

        def initiate_drag(self):
            self.parent.remove_widget(self)

    widget = Builder.load_string('''
BoxLayout:
    DragableBoxLayout:
        drag_classes: ['label']
        orientation: 'vertical'
        Label:
            text: '1'
        Label:
            text: '1'
        Label:
            text: '1'
        Label:
            text: '1'
        Label:
            text: '1'
        Label:
            text: '1'
        DragableBoxLayout:
            padding: '20dp', 0
            drag_classes: ['label']
            orientation: 'vertical'
            Label:
                text: '1'
            Label:
                text: '1'
    DragableBoxLayout:
        drag_classes: ['label']
        orientation: 'vertical'
        DragLabel:
            text: '2'
        DragLabel:
            text: '2'
        DragLabel:
            text: '2'
        DragLabel:
            text: '2'
        DragLabel:
            text: '2'
        DragLabel:
            text: '2'
    ''')

    runTouchApp(widget)
