from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy_garden.drag_n_drop import (
    DraggableController, DraggableLayoutBehavior, DraggableObjectBehavior,
)

drag_controller = DraggableController()


class DraggableGridLayout(DraggableLayoutBehavior, GridLayout):

    def compare_pos_to_widget(self, widget, pos):
        x, y = pos
        if y > widget.top:
            return 'before'
        elif y < widget.y:
            return 'after'
        elif x > widget.right:
            return 'after'
        elif x < widget.x:
            return 'before'
        else:
            spacer = self.spacer_widget
            if widget.parent is spacer.parent:
                children = widget.parent.children
                if children.index(spacer) > children.index(widget):
                    return 'after'
        return 'before'

    def handle_drag_release(self, index, drag_widget):
        self.add_widget(drag_widget, index)


class DragLabel(DraggableObjectBehavior, Label):

    def __init__(self, **kwargs):
        super(DragLabel, self).__init__(
            **kwargs, drag_controller=drag_controller)

    def initiate_drag(self):
        self.parent.remove_widget(self)


kv = '''
BoxLayout:
    DraggableGridLayout:
        cols: 3
        drag_classes: ['label']
        orientation: 'vertical'
        padding: '5dp'
        spacing: '5dp'
        canvas:
            Color:
                rgba: (1, 0, 1, .2) if \
app.drag_controller.dragging and app.drag_controller.widget_dragged and \
app.drag_controller.widget_dragged.drag_cls == 'label' else (0, 0, 0, 0)
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: 'A1'
        Label:
            text: 'A2'
        Label:
            text: 'A3'
        Label:
            text: 'A4'
        Label:
            text: 'A5'
        Label:
            text: 'A6'
        DraggableGridLayout:
            padding: '20dp', 0
            spacing: '5dp'
            drag_classes: ['label2']
            cols: 2
            canvas:
                Color:
                    rgba: (1, 1, 0, .2) if \
app.drag_controller.dragging and app.drag_controller.widget_dragged and \
app.drag_controller.widget_dragged.drag_cls == 'label2' else (0, 0, 0, 0)
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: 'B1'
            Label:
                text: 'B2'
            Label:
                text: 'B3'
    DraggableGridLayout:
        cols: 3
        drag_classes: ['label', 'label2']
        orientation: 'vertical'
        padding: '5dp'
        spacing: '5dp'
        canvas:
            Color:
                rgba: (0, 1, 1, .2) if app.drag_controller.dragging else (0, 0, 0, 0)
            Rectangle:
                pos: self.pos
                size: self.size
        DragLabel:
            text: 'A1*'
            drag_cls: 'label'
        DragLabel:
            text: 'B1*'
            drag_cls: 'label2'
        DragLabel:
            text: 'A2*'
            drag_cls: 'label'
        DragLabel:
            text: 'B2*'
            drag_cls: 'label2'
        DragLabel:
            text: 'A3*'
            drag_cls: 'label'
        DragLabel:
            text: 'B3*'
            drag_cls: 'label2'
        DragLabel:
            text: 'A4*'
            drag_cls: 'label'
'''


class MyApp(App):

    drag_controller = drag_controller

    def build(self):
        return Builder.load_string(kv)

MyApp().run()
