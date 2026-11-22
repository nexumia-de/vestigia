"""Changes to a visit on the server, each with its undo. Declining
cannot be undone through the API (a declined visit is gone, recorded in
docs/dawarich-api.md), so it is sent only once its Undo toast has
closed."""
from phosh_toolkit import tasks

from vestigia.account.errors import describe


class VisitActions:
    def __init__(self, window, day_page):
        self.window = window
        self.page = day_page

    def _client(self):
        return self.window.account.client()

    def _changed(self):
        """The day's visits changed: fetch it again."""
        from vestigia.day import cache
        cache.forget(self.window.account.server_url, self.page.day)
        self.page.load()

    def update(self, visit, toast, undo_fields, **fields):
        """PATCH `fields`; the toast's Undo sends `undo_fields`."""
        def done(_answer, error):
            if error is not None:
                self.window.toast(describe(error))
                return
            self._changed()
            self.window.toast_with_undo(toast, lambda: self.update(
                visit, "Undone", None, **undo_fields) if undo_fields else None)
        tasks.run(lambda: self._client().update_visit(visit.visit_id, **fields), done)

    def confirm(self, visit):
        self.update(visit, "Visit confirmed", {"status": visit.status or "suggested"},
                    status="confirmed")

    def rename(self, visit, name):
        # Dawarich confirms a suggested visit on any edit unless a status
        # is sent: keep the status it had.
        self.update(visit, "Visit renamed", {"name": visit.name,
                                             "status": visit.status},
                    name=name, status=visit.status)

    def choose_place(self, visit, place_id):
        undo = {"place_id": visit.place_id, "status": visit.status} \
            if visit.place_id else None
        self.update(visit, "Place chosen", undo, place_id=place_id,
                    status=visit.status)

    def decline(self, visit):
        """Hide the visit at once; tell the server only when the toast
        closes without Undo."""
        self.page.hide_visit(visit)
        state = {"undone": False}

        def undo():
            state["undone"] = True
            self.page.show_day(self.page.current)

        def send():
            if state["undone"]:
                return
            tasks.run(lambda: self._client().update_visit(visit.visit_id,
                                                          status="declined"),
                      lambda _a, error: self.window.toast(describe(error))
                      if error is not None else self._changed())

        self.window.toast_with_undo("Visit declined", undo, on_dismissed=send)

    def places(self, visit, done):
        tasks.run(lambda: self._client().possible_places(visit.visit_id), done)
