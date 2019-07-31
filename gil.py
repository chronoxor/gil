#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gil (git links) tool allows to describe and manage complex git repositories
dependency with cycles and cross references
"""

import collections
import os
import re
import subprocess
import sys

__author__ = "Ivan Shynkarenka"
__email__ = "chronoxor@gmail.com"
__license__ = "MIT License"
__url__ = "https://github.com/chronoxor/gil"
__version__ = "1.10.0.0"


class GilRecord(object):
    def __init__(self, name, path, repo, branch, links):
        self.name = name
        self.path = path
        self.repo = repo
        self.branch = branch
        self.links = links
        self.active = False

    def __eq__(self, other):
        if not isinstance(self, other.__class__):
            return NotImplemented
        if not self.name == other.name:
            return False
        if not self.repo == other.repo:
            return False
        if not self.branch == other.branch:
            return False
        return True

    def __lt__(self, other):
        if not isinstance(self, other.__class__):
            return NotImplemented
        if not self.name < other.name:
            return True
        return False

    @property
    def __key__(self):
        return self.name, self.repo, self.branch

    def __hash__(self):
        return hash(self.__key__)

    def __str__(self):
        return "%s %s %s %s" % (self.name, self.path, self.repo, self.branch)


class GilContext(object):
    def __init__(self, path):
        self.records = collections.OrderedDict()
        self.path = os.path.abspath(path)
        print("Working path: %s" % self.path)

    def show(self):
        print("Gil context:")
        for value in self.records.values():
            print(value)

    def discover(self, path):
        current = os.path.abspath(path)

        # Recursive discover the root path
        root = current
        parent = current
        while True:
            top = os.path.abspath(os.path.join(parent, os.pardir))
            if top == parent:
                break
            parent = top
            # Try to find .gitlinks file
            filename = os.path.join(parent, ".gitlinks")
            if os.path.exists(filename):
                root = parent
        self.discover_recursive(root)

        # Mark active records
        for record in self.records:
            if record.path.startswith(current):
                record.active = True

    def discover_recursive(self, path):
        current = os.path.abspath(path)

        # Discover the current directory
        records = self.discover_path(current)

        # Insert discovered record into the records dictionary
        for record in records:
            if record not in self.records:
                self.records[record] = record

        # Discover all child directories
        for record in records:
            self.discover_recursive(record.path)

    def discover_path(self, path):
        # Try to find .gitlinks file
        filename = os.path.join(path, ".gitlinks")
        if not os.path.exists(filename):
            return []

        print("Discover git links: %s" % filename)

        # Process .gitlinks file
        return self.process_links(path, filename)

    def process_links(self, path, filename):
        result = []
        with open(filename, 'r') as file:
            index = 0
            for line in file:
                # Skip empty lines and comments
                line = line.strip()
                if line == '' or line.startswith('#'):
                    continue
                # Split line into tokens
                tokens = self.split(line)
                if (len(tokens) < 4) or ((len(tokens) % 2) != 0):
                    raise Exception("%s:%d: Invalid git link format! Must be in the form of 'name path repo branch [base_path target_path]'" % (filename, index))
                # Create a new git link record
                gil_name = tokens[0]
                gil_path = os.path.abspath(os.path.join(path, tokens[1]))
                gil_repo = tokens[2]
                gil_branch = tokens[3]
                gil_links = dict()
                for i in range(4, len(tokens), 2):
                    gil_links[tokens[i]] = tokens[i + 1]
                record = GilRecord(gil_name, gil_path, gil_repo, gil_branch, gil_links)
                # Try to find git link record in the records dictionary
                if record not in self.records:
                    result.append(record)
                index += 1
        return result

    def clone(self, args=None):
        args = [] if args is None else args
        stack = list(self.records.keys())
        while len(stack) > 0:
            value = stack.pop(0)
            path = value.path
            if not os.path.exists(path) or not os.listdir(path):
                # Perform git clone operation
                self.git_clone(value.path, value.repo, value.branch, args)
                # Discover new repository and append new records to the stack
                if os.path.exists(path) and os.listdir(path):
                    inner = collections.OrderedDict.fromkeys(self.discover_path(path))
                    for key in inner:
                        if key not in self.records:
                            self.records[key] = key
                            stack.append(key)

    def link(self, path=None):
        current = os.path.abspath(self.path if path is None else path)

        # Recursive discover the root path
        root = current
        parent = current
        while True:
            top = os.path.abspath(os.path.join(parent, os.pardir))
            if top == parent:
                break
            parent = top
            # Try to find .gitlinks file
            filename = os.path.join(parent, ".gitlinks")
            if os.path.exists(filename):
                root = parent
        self.link_recursive(root)

    def link_recursive(self, path):
        current = os.path.abspath(path)

        # Link the current directory
        dirs = self.link_path(current)

        # Link all child directories
        for d in dirs:
            self.link_path(d)

        # Link all records directories
        for record in self.records:
            self.link_path(record.path)

    def link_path(self, path):
        # Try to find .gitlinks file
        filename = os.path.join(path, ".gitlinks")
        if not os.path.exists(filename):
            return []

        # Process .gitlinks file
        return self.update_links(path, filename)

    def update_links(self, path, filename):
        result = []
        with open(filename, 'r') as file:
            index = 0
            for line in file:
                # Skip empty lines and comments
                line = line.strip()
                if line == '' or line.startswith('#'):
                    continue
                # Split line into tokens
                tokens = self.split(line)
                if (len(tokens) < 4) or ((len(tokens) % 2) != 0):
                    raise Exception("%s:%d: Invalid git link format! Must be in the form of 'name path repo branch [base_path target_path]'" % (filename, index))
                # Create a new git link record
                gil_name = tokens[0]
                gil_path = os.path.abspath(os.path.join(path, tokens[1]))
                gil_repo = tokens[2]
                gil_branch = tokens[3]
                gil_links = dict()
                for i in range(4, len(tokens), 2):
                    gil_links[tokens[i]] = tokens[i + 1]
                record = GilRecord(gil_name, gil_path, gil_repo, gil_branch, gil_links)
                # Try to find git link record in the records dictionary
                found = os.path.exists(gil_path) and os.listdir(gil_path)
                if record in self.records:
                    found = True
                    record = self.records[record]
                    # Try to check or create link to the existing git link record
                    src_path = record.path
                    dst_path = gil_path
                    # Add destination path to the result list
                    result.append(dst_path)
                    # Update root link
                    self.update_link(src_path, dst_path)
                    # Update record links if some exists
                    for src, dst in record.links.items():
                        src_link_path = os.path.abspath(os.path.join(src_path, src))
                        dst_link_path = os.path.abspath(os.path.join(path, dst))
                        self.update_link(src_link_path, dst_link_path)
                # Validate git link path
                if not found or not os.path.exists(gil_path) or not os.listdir(gil_path):
                    raise Exception("%s:%d: Invalid git link path! Please check %s git repository in %s" % (filename, index, gil_name, gil_path))
                index += 1
        return result

    def command(self, name, args=None):
        args = [] if args is None else args

        # Call the command for the current directory
        current = os.path.abspath(self.path)
        self.git_command(current, name, args)

        # Call the command for all active records
        for record in self.records:
            if record.active:
                # Checkout to the required branch
                self.git_checkout(record.path, record.branch)
                # Call the command callback
                self.git_command(record.path, name, args)

    # Filesystem methods

    @staticmethod
    def create_link(src_path, dst_path):
        # Create all directories at link path
        parent = os.path.abspath(os.path.join(dst_path, os.pardir))
        os.makedirs(parent, exist_ok=True)
        # Remove existing file, link or folder
        if os.path.exists(dst_path):
            if os.path.isdir(dst_path):
                os.rmdir(dst_path)
            else:
                os.remove(dst_path)
        # Create the link
        os.symlink(src_path, dst_path, target_is_directory=True)
        print("Update git link: %s -> %s" % (src_path, dst_path))

    @staticmethod
    def update_link(src_path, dst_path):
        if src_path == dst_path:
            # Do nothing here...
            pass
        elif os.path.exists(dst_path) and os.listdir(dst_path):
            # Check the link
            if os.path.islink(dst_path):
                real_path = os.readlink(dst_path)
                if real_path != src_path:
                    # Re-create the link
                    GilContext.create_link(src_path, dst_path)
        else:
            GilContext.create_link(src_path, dst_path)

    # Git methods

    @staticmethod
    def git_clone(path, repo, branch, args):
        # Call git clone command
        print("Running git clone %s branch \"%s\" into %s" % (repo, branch, path))
        params = ["git", "clone", *args, "-b", branch, repo, path]
        process = subprocess.run(params)
        if process.returncode != 0:
            raise Exception("Failed to run git clone %s branch \"%s\" into %s" % (repo, branch, path))

    @staticmethod
    def git_checkout(path, branch):
        # Save the current working directory
        working = os.getcwd()
        # Change working directory into the current git repository
        os.chdir(path)
        # Call git checkout command
        print("Running: git checkout branch \"%s\" in %s" % (branch, path))
        params = ["git", "checkout", branch]
        process = subprocess.run(params)
        if process.returncode != 0:
            raise Exception("Failed to run git checkout branch \"%s\" in %s" % (branch, path))
        # Restore the current working directory
        os.chdir(working)

    @staticmethod
    def git_command(path, command, args):
        # Save the current working directory
        working = os.getcwd()
        # Change working directory into the current git repository
        os.chdir(path)
        # Call git command
        print("Running: git %s in %s" % (command, path))
        params = ["git", command, *args]
        process = subprocess.run(params)
        if process.returncode is None:
            raise Exception("Failed to run git %s in %s" % (command, path))
        # Restore the current working directory
        os.chdir(working)

    # Utility methods

    # Split a string by spaces preserving quoted substrings
    # Author: Ton van den Heuvel
    # https://stackoverflow.com/a/51560564
    @staticmethod
    def split(line):
        def strip_quotes(s):
            if s and (s[0] == '"' or s[0] == "'") and s[0] == s[-1]:
                return s[1:-1]
            return s
        return [strip_quotes(p).replace('\\"', '"').replace("\\'", "'") for p in re.findall(r'"(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\'|[^\s]+', line)]


def show_help():
    print("usage: gil command arguments")
    print("Supported commands:")
    print("\thelp - show this help")
    print("\tversion - show version")
    print("\tcontext - show git links context")
    print("\tclone [args] - clone git repositories")
    print("\tlink - link git repositories")
    print("\tupdate - update git repositories (clone & link)")
    print("\tpull [args] - pull git repositories")
    print("\tpush [args] - push git repositories")
    print("\tcommit [args] - commit git repositories")
    print("\tstatus [args] - show status of git repositories")
    sys.exit(1)


def show_version():
    print(__version__)
    sys.exit(1)


def main():
    # Show help message
    if len(sys.argv) <= 1:
        show_help()

    if sys.argv[1] == "help":
        show_help()
    elif sys.argv[1] == "version":
        show_version()

    # Get the current working directory
    path = os.getcwd()

    # Create git links context
    context = GilContext(path)

    # Discover working path
    context.discover(path)

    if sys.argv[1] == "context":
        context.show()
    elif sys.argv[1] == "clone":
        context.clone(sys.argv[2:])
    elif sys.argv[1] == "link":
        context.link()
    elif sys.argv[1] == "update":
        context.clone()
        context.link()
    elif (sys.argv[1] == "pull") or (sys.argv[1] == "push") or (sys.argv[1] == "commit") or (sys.argv[1] == "status"):
        context.command(sys.argv[1], sys.argv[2:])
    else:
        print("Unknown command: %s" % sys.argv[1])
        return -1
    return 0


if __name__ == "__main__":
    sys.exit(main())
