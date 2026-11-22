"""The map widget: OSM raster tiles with attribution, libshumate's own
tile cache and Vestigia's User-Agent (OSM tile usage policy), layers for
tracks and markers, and the own location from phosh_toolkit.location."""
import os

import gi

gi.require_version("Shumate", "1.0")
from gi.repository import GLib, Gtk, Shumate  # noqa: E402
from phosh_toolkit.location import Location  # noqa: E402

from vestigia import USER_AGENT  # noqa: E402
from vestigia.map import fit  # noqa: E402

OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
# Tests and screenshots without network set VESTIGIA_TILES=off.
TILES_ENV = "VESTIGIA_TILES"
# The portal reports a move of this many metres; enough for a dot.
LOCATION_DISTANCE_M = 10


def osm_source():
    return Shumate.RasterRenderer.new_full_from_url(
        "osm-mapnik", "OpenStreetMap",
        "© OpenStreetMap contributors", "https://www.openstreetmap.org/copyright",
        0, 19, 256, Shumate.MapProjection.MERCATOR, OSM_URL)


def style_color(widget, css_class):
    """The colour a style class gives: track colours come from style.css
    variables, never from code."""
    probe = Gtk.Label(css_classes=[css_class])
    probe.set_parent(widget)
    color = probe.get_color()
    probe.unparent()
    return color


class MapView(Gtk.Overlay):
    def __init__(self, window):
        super().__init__(hexpand=True, vexpand=True)
        self.window = window
        if hasattr(Shumate, "set_user_agent"):
            Shumate.set_user_agent(USER_AGENT)
        self.simple = Shumate.SimpleMap(vexpand=True, hexpand=True)
        if os.environ.get(TILES_ENV) != "off":
            self.simple.set_map_source(osm_source())
        self.map = self.simple.get_map()
        self.viewport = self.simple.get_viewport()
        self.viewport.set_reference_map_source(osm_source())
        self.set_child(self.simple)
        # GtkOverlay is final, so its size_allocate cannot be overridden;
        # an empty drawing area over the map reports size changes.
        sizer = Gtk.DrawingArea(can_target=False, hexpand=True, vexpand=True)
        sizer.connect("resize", self._on_resize)
        self.add_overlay(sizer)
        self.tracks = []
        # The box last fitted, and (width, height, view) after the fit.
        self._shown = None
        self._fitted = None
        # The user dragged, zoomed or scrolled since the last fit.
        self._touched = False
        for controller in (Gtk.GestureClick(), Gtk.EventControllerScroll(
                flags=Gtk.EventControllerScrollFlags.BOTH_AXES)):
            controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
            signal = "pressed" if isinstance(controller, Gtk.GestureClick) else "scroll"
            controller.connect(signal, self._on_touch)
            self.simple.add_controller(controller)
        self.markers = Shumate.MarkerLayer.new(self.viewport)
        self.map.add_layer(self.markers)
        self.me_layer = Shumate.MarkerLayer.new(self.viewport)
        self.map.add_layer(self.me_layer)
        self.me = None
        self.location = Location(LOCATION_DISTANCE_M)
        self.location.connect("changed", self._on_location)
        self.location.connect("failed", self._on_location_failed)
        self._follow = False

        self.locate_button = Gtk.Button(
            icon_name="find-location-symbolic", tooltip_text="Show My Location",
            halign=Gtk.Align.END, valign=Gtk.Align.END,
            margin_end=12, margin_bottom=48)
        self.locate_button.add_css_class("osd")
        self.locate_button.add_css_class("circular")
        self.locate_button.update_property([Gtk.AccessibleProperty.LABEL],
                                           ["Show My Location"])
        self.locate_button.set_size_request(48, 48)
        self.locate_button.connect("clicked", self._on_locate)
        self.add_overlay(self.locate_button)

    # Tracks and markers

    def clear(self):
        self._shown = None
        for layer in self.tracks:
            self.map.remove_layer(layer)
        self.tracks = []
        self.markers.remove_all()

    def add_track(self, positions):
        """A line through (lat, lon) pairs: an outline in the accent's
        foreground colour under the accent itself, readable on the light
        OSM tiles in light and dark style."""
        for css, width in (("vestigia-track-casing", 7.0), ("vestigia-track", 4.0)):
            layer = Shumate.PathLayer.new(self.viewport)
            layer.set_stroke_color(style_color(self, css))
            layer.set_stroke_width(width)
            for lat, lon in positions:
                layer.add_node(Shumate.Coordinate.new_full(lat, lon))
            self.map.insert_layer_behind(layer, self.markers)
            self.tracks.append(layer)

    def add_marker(self, lat, lon, icon, label):
        image = Gtk.Image(icon_name=icon, pixel_size=24)
        image.add_css_class("vestigia-marker")
        image.update_property([Gtk.AccessibleProperty.LABEL], [label])
        marker = Shumate.Marker(child=image)
        marker.set_location(lat, lon)
        marker.set_tooltip_text(label)
        self.markers.add_marker(marker)
        return marker

    def show(self, positions):
        """Centre and zoom so that all (lat, lon) pairs are visible; again
        after a resize (a window maximized after it opened) as long as
        the user has not moved the map since."""
        box = fit.bounds(positions)
        if box is None:
            return
        self._shown = box
        self._fit_box()

    def _fit_box(self):
        width = self.get_width() or 360
        height = self.get_height() or 600
        lat, lon, zoom = fit.fit(self._shown, width, height)
        self.viewport.set_zoom_level(zoom)
        self.map.center_on(lat, lon)
        self._fitted = (width, height)
        self._touched = False

    def _on_touch(self, *_):
        self._touched = True

    def _on_resize(self, area, width, height):
        if self._shown is None or self._fitted is None:
            return
        if (width, height) != self._fitted and not self._touched:
            # Not during allocation: changing the viewport queues one.
            GLib.idle_add(self._refit)

    def _refit(self):
        if self._shown is not None:
            self._fit_box()
        return GLib.SOURCE_REMOVE

    def center(self, lat, lon, zoom=None):
        if zoom is not None:
            self.viewport.set_zoom_level(zoom)
        self.map.center_on(lat, lon)

    # Own location

    def _on_locate(self, *_):
        self._follow = True
        if self.location.fix:
            self._on_location(self.location, *self.location.fix)
        self.location.start(self.window)

    def _on_location(self, location, lat, lon, accuracy):
        if self.me is None:
            image = Gtk.Image(icon_name="mark-location-symbolic", pixel_size=24)
            image.add_css_class("vestigia-me")
            image.update_property([Gtk.AccessibleProperty.LABEL], ["My Location"])
            self.me = Shumate.Marker(child=image)
            self.me_layer.add_marker(self.me)
        self.me.set_location(lat, lon)
        if self._follow:
            self._follow = False
            self.center(lat, lon, max(self.viewport.get_zoom_level(), 15))

    def _on_location_failed(self, location, message):
        self._follow = False
        self.window.toast("Your location is not available")

    def stop(self):
        self.location.stop()
