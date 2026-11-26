#!/usr/bin/env python3
"""Print a file's contents only if it is a regular file, never following a link.

The role reads config.yaml as root from a directory the container user (and so
the agent) can write to. Checking with stat and then reading leaves a window to
swap in a symlink, so the check and the read are one open():
  - O_NOFOLLOW fails on a symlink in the last path component (ELOOP);
  - O_NONBLOCK stops a planted FIFO from hanging the run;
  - fstat on the open descriptor rejects anything that isn't a regular file.
Hardlinks to files the user doesn't own are blocked by fs.protected_hardlinks.

Exit 0: contents on stdout. Exit 3: the file does not exist. Exit 1: refused.
"""
import os
import stat
import sys


def main(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return 3
    except OSError as err:
        sys.stderr.write("refusing to read %s: %s\n" % (path, err.strerror))
        return 1
    with os.fdopen(fd, encoding="utf-8") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            sys.stderr.write("refusing to read %s: not a regular file\n" % path)
            return 1
        sys.stdout.write(handle.read())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
