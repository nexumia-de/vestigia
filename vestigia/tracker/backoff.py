"""Waiting times between failed uploads: doubling from 30 s to an hour.
No GTK."""


class Backoff:
    def __init__(self, first=30, longest=3600):
        self.first = first
        self.longest = longest
        self.failures = 0

    def next(self):
        """Seconds to wait after one more failure."""
        self.failures += 1
        return min(self.first * 2 ** (self.failures - 1), self.longest)

    def reset(self):
        self.failures = 0
