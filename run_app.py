import os
import sys

# PyInstaller's --windowed build has no console, so sys.stdout/stderr are
# None. Anything that tries to print() or log a warning during startup
# (pywin32, reportlab, etc.) then crashes with an unhandled AttributeError
# before the window ever appears.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from job_checklist.app import main

if __name__ == "__main__":
    main()
