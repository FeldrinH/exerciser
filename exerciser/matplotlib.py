from matplotlib.figure import Figure
from IPython.display import display
from IPython.core.getipython import get_ipython
import matplotlib.pyplot as plt

# This is a fairly dirty hack. In particular autoshow using IPython events is a very questionable approach.
# TODO: Maybe this should be removed in favor of only supporting one backend?
def show_interactive(figure: Figure):
    """
    Does whatever is necessary to redraw and show the figure without recreating it.

    This is meant to be used with `ipywidgets.interact` and other similar functions.
    """
    if plt.get_backend().casefold().endswith('backend_inline'):
        # Inline backend does not redraw automatically. Need to display the figure manually.
        # After displaying the figure we close it, so any calls to plt.show doesn't display it a second time.
        display(figure)
        plt.close(figure)
    else:
        # Other (common) backends redraw automatically in interactive mode, but might not show the figure unless plt.show is called.
        # We automatically call plt.show once cell execution has completed.
        # Note: When using the `widget` backend this assumes that the given figure is the only active figure.
        # plt.show only shows the last active figure with the `widget` backend.
        # TODO: Explicitly display this specific figure to support multiple figures.
        autoshow()

_autoshow_queued = False

def autoshow():
    """
    Automatically calls plt.show once execution of this cell has ended.
    """
    global _autoshow_queued
    _autoshow_queued = True

def _autoshow_pre_run_cell():
    global _autoshow_queued
    _autoshow_queued = False

def _autoshow_post_run_cell():
    global _autoshow_queued
    if _autoshow_queued:
        _autoshow_queued = False
        plt.show()

ip = get_ipython()
if ip is not None:
    ip.events.register('pre_run_cell', _autoshow_pre_run_cell)
    ip.events.register('post_run_cell', _autoshow_post_run_cell)