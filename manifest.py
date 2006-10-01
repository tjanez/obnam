#!/usr/bin/python

"""Create a manifest for a directory tree

The manifest contains a list of all directories, files, and other
filesystem objects in the tree, all their meta data (filename,
permissions, timestamps, etc), and checksums of file contents. The
manifest is sorted in a canonical order.

By taking manifests of two trees, or of one tree at different times,
it is possible to compare them for changes.

Manifest format: Each filesystem object is represented by a paragraph
of RFC822-like headers. Paragraphs are separated by empty lines. Sorting
is done in the C locale using the pathname as a result. Example:

    Pathname: foo/bar/foo%20bar
    Username: liw
    UID: 808

(This example is not complete.) Fields are (and the following is the
canonical order):

    Pathname        URL-encoded pathname
    Type            type of object: "file", "dir", "symlink", ...
    Mode            st_mode, in octal, with leading 0
    Inode           st_ino
    Device          st_dev, in hex, with leading 0x
    Nlink           st_nlink
    UID             st_uid
    Username        username, looked up based on st_uid
    GID             st_gid
    Group           group name, looked up based on st_gid
    Size            st_size
    Atime           st_atime
    Mtime           st_mtime
    Ctime           st_ctime
    MD5             MD5 checksum of file

"""


import grp
import md5
import optparse
import os
import pwd
import stat
import sys
import time
import urllib


printable_fields = [
    "Pathname", "Type", "Mode", "Inode", "Device", "Nlink", "UID",
    "Username", "GID", "Group", "Size", "Atime", "Mtime", "Ctime",
    "MD5",
]


class FilesystemObject:

    def __init__(self, pathname, key):
        self.pathname = pathname
        self.key = key
        self.st = os.lstat(pathname)
        if stat.S_ISREG(self.st.st_mode):
            self.checksum = md5.new()
            f = file(pathname, "r")
            while True:
                data = f.read(64 * 1024)
                if not data:
                    break
                self.checksum.update(data)
            f.close()
        else:
            self.checksum = None

    def typename(self):
        list = (
            (stat.S_ISDIR, "dir"),
            (stat.S_ISCHR, "char"),
            (stat.S_ISBLK, "block"),
            (stat.S_ISREG, "file"),
            (stat.S_ISFIFO, "fifo"),
            (stat.S_ISLNK, "symlink"),
            (stat.S_ISSOCK, "socket"),
        )
        for func, result in list:
            if func(self.st.st_mode):
                return result
        raise Exception("Unknown file type: 0%o" % self.st.st_mode)
        
    def time(self, timestamp):
        t = time.gmtime(timestamp)
        return time.strftime("%Y-%m-%dT%H:%M:%S UTC", t)

    def write_field(self, f, name, value):
        if name in printable_fields:
            f.write("%s: %s\n" % (name, value))
        
    def write(self, f):
        self.write_field(f, "Pathname", urllib.quote(self.key))
        self.write_field(f, "Type", self.typename())
        self.write_field(f, "Mode", "0%o" % self.st.st_mode)
        self.write_field(f, "Inode", "%d" % self.st.st_ino)
        self.write_field(f, "Device", "0x%x" % self.st.st_dev)
        self.write_field(f, "Nlink", "%d" % self.st.st_nlink)
        self.write_field(f, "UID", "%d" % self.st.st_uid)
        self.write_field(f, "Username", pwd.getpwuid(self.st.st_uid).pw_name)
        self.write_field(f, "GID", "%d" % self.st.st_gid)
        self.write_field(f, "Group", grp.getgrgid(self.st.st_gid).gr_name)
        self.write_field(f, "Size", "%d" % self.st.st_size)
        self.write_field(f, "Atime", "%s" % self.time(self.st.st_atime))
        self.write_field(f, "Mtime", "%s" % self.time(self.st.st_mtime))
        self.write_field(f, "Ctime", "%s" % self.time(self.st.st_ctime))
        if self.checksum:
            self.write_field(f, "MD5", self.checksum.hexdigest())


class Manifest:

    def __init__(self):
        self.fsys_objects = {}

    def add(self, root):
        if os.path.isdir(root):
            self.fsys_objects["."] = FilesystemObject(root, ".")
            for dirpath, dirnames, filenames in os.walk(root):
                for x in dirnames + filenames:
                    pathname = os.path.join(dirpath, x)
                    assert pathname.startswith(root + os.sep)
                    key = pathname[len(root + os.sep):]
                    self.fsys_objects[key] = FilesystemObject(pathname, key)
        else:
            self.fsys_objects[root] = FilesystemObject(root)

    def write(self, f):
        pathnames = self.fsys_objects.keys()
        pathnames.sort()
        for pathname in pathnames:
            self.fsys_objects[pathname].write(f)
            f.write("\n")


def parse_command_line():
    parser = optparse.OptionParser()
    
    parser.add_option("-i", "--ignore", action="append")
    
    (options, roots) = parser.parse_args()
    
    if options.ignore:
        for x in options.ignore:
            if x in printable_fields:
                printable_fields.remove(x)

    return roots


def main():
    roots = parse_command_line()
    os.stat_float_times(True)
    manifest = Manifest()
    for root in roots:
        manifest.add(root)
    manifest.write(sys.stdout)


if __name__ == "__main__":
    main()