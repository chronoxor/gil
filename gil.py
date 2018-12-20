#!/usr/bin/python
# -*- coding: utf-8 -*-

# Git Links utility allows to create and manage git projects dependency
# https://github.com/chronoxor/GitLinks
# Author: Ivan Shynkarenka
# License: MIT License
# Version: 1.0.0.0

import optparse
import os
import re
import subprocess


class GilRecord(object):
    def __init__(self, name, path, repo, branch):
        self.name = name
        self.path = path
        self.repo = repo
        self.branch = branch

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

    @property
    def __key__(self):
        return self.name, self.repo, self.branch

    def __hash__(self):
        return hash(self.__key__)

    def __str__(self):
        return "%s %s %s %s" % (self.name, self.path, self.repo, self.branch)


class GilContext(object):
    def __init__(self, path, verbose):
        self.records = {}
        self.verbose = verbose
        self.path = os.path.abspath(path)
        if self.verbose:
            print("Working path: %s" % self.path)

    def show(self):
        print("Git Links context:")
        for value in self.records.values():
            print(value)

    def clone(self, args):
        stack = list(self.records.values())
        while len(stack) > 0:
            value = stack.pop()
            path = value.path
            if not os.path.exists(path) or not os.listdir(path):
                # Call git clone command
                params = ["git", "clone", *args, "-b", value.branch, value.repo, value.path]
                process = subprocess.run(params)
                if process.returncode != 0:
                    raise Exception("Failed to git clone %s branch %s into %s" % (value.repo, value.branch, value.path))

                # Discover new repository and append new records to the stack
                if os.path.exists(path) and os.listdir(path):
                    stack.extend(self.discover_dir(path))

    def discover(self, path):
        current = os.path.abspath(path)

        # Recursive discover the parent path
        parent = os.path.abspath(os.path.join(current, os.pardir))
        if parent != current:
            self.discover(parent)

        # Discover the current directory
        records = self.discover_dir(current)

        # Try to discover a new Git Links path
        for record in records:
            self.discover_dir(record.path)

    def discover_dir(self, path):
        # Try to find .gitlinks file
        filename = os.path.join(path, ".gitlinks")
        if not os.path.exists(filename):
            return []

        if self.verbose:
            print("Discover git links: %s" % filename)

        # Process .gitlinks file
        return self.process_links(path, filename)

    def process_links(self, path, filename):
        result = []
        file = open(filename, 'r')
        index = 0
        for line in file:
            # Skip empty lines and comments
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            # Split line into tokens
            tokens = self.split(line)
            if len(tokens) != 4:
                raise Exception("%s:%d: Invalid Git Links format! Must be in the form of 'name path repo branch'." % (filename, index))
            # Create a new Git Links record
            gil_name = tokens[0]
            gil_path = os.path.abspath(os.path.join(path, tokens[1]))
            gil_repo = tokens[2]
            gil_branch = tokens[3]
            record = GilRecord(gil_name, gil_path, gil_repo, gil_branch)
            # Try to insert Git Links record into the records dictionary
            if record not in self.records:
                result.append(record)
                self.records[record] = record
            index += 1
        file.close()
        return result

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


def main():
    parser = optparse.OptionParser(usage="usage: %prog [options] command arguments", version="%prog 1.0")
    parser.add_option("-p", "--path", action="store", dest="path", default=".", help="path to process")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="verbose output")
    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        return

    # Create Git Links context
    context = GilContext(options.path, options.verbose)

    # Discover working path
    context.discover(options.path)

    if args[0] == "help":
        print("Supported commands:")
        print("\thelp - show this help")
        print("\tcontext - show Git Links context")
        print("\tclone - clone and link git repositories")
    elif args[0] == "context":
        context.show()
    elif args[0] == "clone":
        context.clone(args[1:])
    else:
        print("Unknown command: %s" % args[0])


if __name__ == "__main__":
    main()
