"""Stable headless Qt setup for the automated test harness."""

import os


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
