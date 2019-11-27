import pytest


def test_creation():
    from kivy_garden.drag_n_drop import DraggableLayoutBehavior, \
        DraggableController, DraggableObjectBehavior
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

    layout = DraggableBoxLayout(drag_classes=['box'])
    label = DragLabel(drag_cls='box')
    label2 = DragLabel(drag_cls='box')

    layout.add_widget(label)
    layout.add_widget(label2)
