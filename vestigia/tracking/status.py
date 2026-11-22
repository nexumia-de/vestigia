"""The line that says what the tracker does. No GTK."""
from datetime import datetime


def text(tracker):
    if tracker.error:
        return f"Tracking stopped: {tracker.error}"
    parts = []
    if tracker.running:
        parts.append("Recording")
    target, _secret = tracker.target()
    if target is None:
        if tracker.running:
            parts.append("points stay on this phone")
        return " · ".join(parts)
    pending = tracker.pending()
    if pending:
        parts.append(f"{pending} waiting")
    last = tracker.last_upload()
    if last:
        parts.append("uploaded " + datetime.fromtimestamp(last).strftime("%H:%M"))
    scheduler = tracker.scheduler
    if scheduler.rejected:
        parts.append("the upload target rejected the credentials")
    elif scheduler.waiting_for_network and pending:
        parts.append("waiting for the network")
    elif scheduler.last_error:
        parts.append(f"upload failed: {scheduler.last_error}")
    return " · ".join(parts)
