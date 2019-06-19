.. _examples:

********
Examples
********

To test, run the example code and try to drag the widgets around between
the various layouts.


Basic Example
-------------

Following is an example with :class:`kivy.uix.boxlayout.BoxLayout`:

.. code-block:: python

    from kivy.uix.label import Label
    from kivy.uix.boxlayout import BoxLayout

    class DraggableBoxLayout(DraggableLayoutBehavior, BoxLayout):

        def compare_pos_to_widget(self, widget, pos):
            if self.orientation == 'vertical':
                return 'before' if pos[1] >= widget.center_y else 'after'
            return 'before' if pos[0] < widget.center_x else 'after'

        def handle_drag_release(self, index, drag_widget):
            self.add_widget(drag_widget, index)

    class DragLabel(DraggableObjectBehavior, Label):

        def initiate_drag(self):
            # during a drag, we remove the widget from the original location
            self.parent.remove_widget(self)

And then in kv:

.. code-block:: yaml

    BoxLayout:
        DraggableBoxLayout:
            drag_classes: ['label']
            orientation: 'vertical'
            Label:
                text: 'A'
            Label:
                text: 'A'
            Label:
                text: 'A'
        DraggableBoxLayout:
            drag_classes: ['label']
            orientation: 'vertical'
            DragLabel:
                text: 'A*'
                drag_cls: 'label'
            DragLabel:
                text: 'A*'
                drag_cls: 'label'

Advanced Example
----------------

.. code-block:: python

    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.boxlayout import BoxLayout

    drag_controller = DraggableController()

    class DraggableBoxLayout(DraggableLayoutBehavior, BoxLayout):

        def compare_pos_to_widget(self, widget, pos):
            if self.orientation == 'vertical':
                return 'before' if pos[1] >= widget.center_y else 'after'
            return 'before' if pos[0] < widget.center_x else 'after'

        def handle_drag_release(self, index, drag_widget):
            self.add_widget(drag_widget, index)

    class DragLabel(DraggableObjectBehavior, Label):

        def __init__(self, **kwargs):
            super(DragLabel, self).__init__(
                **kwargs, drag_controller=drag_controller)

        def initiate_drag(self):
            # during a drag, we remove the widget from the original location
            self.parent.remove_widget(self)

    kv = '''
    BoxLayout:
        DraggableBoxLayout:
            drag_classes: ['label']
            orientation: 'vertical'
            canvas:
                Color:
                    rgba: (1, 1, 1, .2) if \
    app.drag_controller.dragging and app.drag_controller.widget_dragged and \
    app.drag_controller.widget_dragged.drag_cls == 'label' else (0, 0, 0, 0)
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: 'A'
            Label:
                text: 'A'
            Label:
                text: 'A'
            Label:
                text: 'A'
            Label:
                text: 'A'
            Label:
                text: 'A'
            DraggableBoxLayout:
                padding: '20dp', 0
                drag_classes: ['label2']
                orientation: 'vertical'
                canvas:
                    Color:
                        rgba: (1, 1, 1, .2) if \
    app.drag_controller.dragging and app.drag_controller.widget_dragged and \
    app.drag_controller.widget_dragged.drag_cls == 'label2' else (0, 0, 0, 0)
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Label:
                    text: 'B'
                Label:
                    text: 'B'
                Label:
                    text: 'B'
        DraggableBoxLayout:
            drag_classes: ['label', 'label2']
            orientation: 'vertical'
            canvas:
                Color:
                    rgba: (1, 1, 1, .2) if app.drag_controller.dragging else (0, 0, 0, 0)
                Rectangle:
                    pos: self.pos
                    size: self.size
            DragLabel:
                text: 'A*'
                drag_cls: 'label'
            DragLabel:
                text: 'B*'
                drag_cls: 'label2'
            DragLabel:
                text: 'A*'
                drag_cls: 'label'
            DragLabel:
                text: 'B*'
                drag_cls: 'label2'
            DragLabel:
                text: 'A*'
                drag_cls: 'label'
            DragLabel:
                text: 'B*'
                drag_cls: 'label2'
            DragLabel:
                text: 'A*'
                drag_cls: 'label'
    '''


    class MyApp(App):

        drag_controller = drag_controller

        def build(self):
            return Builder.load_string(kv)

    MyApp().run()
