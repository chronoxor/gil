#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gil (git links) tool allows to describe and manage complex git repositories
dependency with cycles and cross references

This improved version includes:
- Type hints for better code clarity
- Logging instead of print statements
- Custom exceptions for better error handling
- Refactored code for reduced duplication
- F-strings for modern string formatting
- Better separation of concerns
"""

import logging
import os
import re
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from typing import Dict, List, Optional, Set, Tuple

__author__ = "Ivan Shynkarenka"
__email__ = "chronoxor@gmail.com"
__license__ = "MIT License"
__url__ = "https://github.com/chronoxor/gil"
__version__ = "1.26.0.0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Custom Exceptions
class GilException(Exception):
    """Base exception for Gil operations."""
    pass


class GilConfigException(GilException):
    """Exception for configuration/parsing errors."""
    pass


class GilGitException(GilException):
    """Exception for git command failures."""
    pass


class GilLinkException(GilException):
    """Exception for symlink operation failures."""
    pass


class GilRecord:
    """Represents a git repository record with metadata.
    
    Attributes:
        name: Repository name
        path: Repository path
        repo: Repository URL
        branch: Target branch
        links: Dictionary of symlink mappings
        active: Whether this record is active in current context
    """
    
    def __init__(
        self,
        name: str,
        path: str,
        repo: str,
        branch: str,
        links: Optional[Dict[str, str]] = None
    ) -> None:
        self.name = name
        self.path = path
        self.repo = repo
        self.branch = branch
        self.links = links or {}
        self.active = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GilRecord):
            return NotImplemented
        return (
            self.name == other.name
            and self.repo == other.repo
            and self.branch == other.branch
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, GilRecord):
            return NotImplemented
        return self.name < other.name

    def __hash__(self) -> int:
        return hash((self.name, self.repo, self.branch))

    def __str__(self) -> str:
        return f"{self.name} {self.path} {self.repo} {self.branch}"

    def __repr__(self) -> str:
        return (
            f"GilRecord(name={self.name!r}, path={self.path!r}, "
            f"repo={self.repo!r}, branch={self.branch!r})"
        )


class FileSystemManager:
    """Handles filesystem operations for symlink creation and management."""
    
    @staticmethod
    def _safe_remove(path: str) -> None:
        """Safely remove a file, directory, or symlink.
        
        Args:
            path: Path to remove
            
        Raises:
            GilLinkException: If removal fails
        """
        try:
            if os.path.islink(path):
                os.unlink(path)
            elif os.path.isdir(path):
                os.rmdir(path)
            elif os.path.exists(path):
                os.remove(path)
        except OSError as e:
            raise GilLinkException(f"Failed to remove {path}: {e}") from e

    @staticmethod
    def create_link(src_path: str, dst_path: str) -> None:
        """Create a symlink from source to destination.
        
        Args:
            src_path: Source path
            dst_path: Destination symlink path
            
        Raises:
            GilLinkException: If link creation fails
        """
        if not os.path.exists(src_path):
            logger.warning(f"Cannot create git link! Path not found: {src_path}")
            return

        try:
            parent = os.path.dirname(dst_path)
            os.makedirs(parent, exist_ok=True)
            
            FileSystemManager._safe_remove(dst_path)
            
            os.symlink(src_path, dst_path, target_is_directory=True)
            logger.info(f"Create git link: {src_path} -> {dst_path}")
        except (OSError, GilLinkException) as e:
            raise GilLinkException(
                f"Failed to create symlink from {src_path} to {dst_path}: {e}"
            ) from e

    @staticmethod
    def update_link(src_path: str, dst_path: str) -> None:
        """Update or create a symlink, checking if it already points correctly.
        
        Args:
            src_path: Source path
            dst_path: Destination symlink path
        """
        if src_path == dst_path:
            return

        if os.path.islink(dst_path):
            real_path = os.readlink(dst_path)
            if real_path == src_path:
                logger.debug(f"Link already correct: {dst_path}")
                return
            logger.info(f"Updating existing link: {dst_path}")

        FileSystemManager.create_link(src_path, dst_path)


class GitOperations:
    """Handles all git operations with retry logic and proper error handling."""
    
    MAX_CLONE_ATTEMPTS = 10
    CLONE_RETRY_DELAY = 10  # seconds

    @staticmethod
    def _run_git_command(
        cmd: List[str],
        cwd: Optional[str] = None,
        raise_on_error: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a git command with proper error handling.
        
        Args:
            cmd: Command to run as list
            cwd: Working directory for command
            raise_on_error: Whether to raise exception on non-zero return code
            
        Returns:
            CompletedProcess object
            
        Raises:
            GilGitException: If command fails and raise_on_error is True
        """
        try:
            logger.debug(f"Running git command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0 and raise_on_error:
                error_msg = result.stderr or result.stdout or "Unknown error"
                raise GilGitException(
                    f"Git command failed with code {result.returncode}: {error_msg}"
                )
            
            return result
        except subprocess.TimeoutExpired as e:
            raise GilGitException(f"Git command timed out: {e}") from e
        except Exception as e:
            if isinstance(e, GilGitException):
                raise
            raise GilGitException(f"Failed to run git command: {e}") from e

    @classmethod
    def clone(
        cls,
        path: str,
        repo: str,
        branch: str,
        args: Optional[List[str]] = None
    ) -> None:
        """Clone a git repository with retry logic.
        
        Args:
            path: Destination path
            repo: Repository URL
            branch: Branch to clone
            args: Additional git clone arguments
            
        Raises:
            GilGitException: If clone fails after all retries
        """
        args = args or []
        logger.info(f"Cloning {repo} (branch: {branch}) into {path}")
        
        cmd = ["git", "clone", *args, "-b", branch, repo, "--recurse-submodules", path]
        
        for attempt in range(1, cls.MAX_CLONE_ATTEMPTS + 1):
            try:
                cls._run_git_command(cmd)
                logger.info(f"Successfully cloned {repo}")
                return
            except GilGitException as e:
                if attempt < cls.MAX_CLONE_ATTEMPTS:
                    logger.warning(
                        f"Clone attempt {attempt}/{cls.MAX_CLONE_ATTEMPTS} failed, "
                        f"retrying in {cls.CLONE_RETRY_DELAY}s: {e}"
                    )
                    time.sleep(cls.CLONE_RETRY_DELAY)
                else:
                    raise GilGitException(
                        f"Failed to clone {repo} after {cls.MAX_CLONE_ATTEMPTS} attempts"
                    ) from e

    @staticmethod
    def checkout(path: str, branch: str) -> None:
        """Checkout a specific branch.
        
        Args:
            path: Repository path
            branch: Branch to checkout
            
        Raises:
            GilGitException: If checkout fails
        """
        logger.info(f"Checking out branch '{branch}' in {path}")
        GitOperations._run_git_command(["git", "checkout", branch], cwd=path)

    @staticmethod
    def run_command(
        path: str,
        command: str,
        args: Optional[List[str]] = None
    ) -> None:
        """Run an arbitrary git command.
        
        Args:
            path: Repository path
            command: Git command to run
            args: Command arguments
            
        Raises:
            GilGitException: If command fails
        """
        args = args or []
        logger.info(f"Running: git {command} in {path}")
        GitOperations._run_git_command(["git", command, *args], cwd=path)


class ConfigParser:
    """Parses .gitlinks configuration files."""
    
    # Split a string by spaces preserving quoted substrings
    # Author: Ton van den Heuvel
    # https://stackoverflow.com/a/51560564
    QUOTE_PATTERN = re.compile(
        r'"(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\'|[^\s]+'
    )

    @staticmethod
    def split(line: str) -> List[str]:
        """Split a line by spaces while preserving quoted substrings.
        
        Args:
            line: Line to split
            
        Returns:
            List of tokens
        """
        def strip_quotes(s: str) -> str:
            if s and s[0] in ('"', "'") and s[0] == s[-1]:
                return s[1:-1]
            return s

        tokens = ConfigParser.QUOTE_PATTERN.findall(line)
        return [
            strip_quotes(p).replace('\\"', '"').replace("\\'", "'")
            for p in tokens
        ]

    @staticmethod
    def parse_line(
        line: str,
        filename: str,
        line_num: int
    ) -> Tuple[str, str, str, str, Dict[str, str]]:
        """Parse a single gitlinks configuration line.
        
        Args:
            line: Configuration line
            filename: Source filename for error reporting
            line_num: Line number for error reporting
            
        Returns:
            Tuple of (name, path, repo, branch, links_dict)
            
        Raises:
            GilConfigException: If line format is invalid
        """
        line = line.strip()
        if not line or line.startswith('#'):
            return None

        tokens = ConfigParser.split(line)
        
        if len(tokens) < 4 or len(tokens) % 2 != 0:
            raise GilConfigException(
                f"{filename}:{line_num}: Invalid git link format! "
                f"Must be in the form of 'name path repo branch [base_path target_path]'"
            )

        name = tokens[0]
        path = tokens[1]
        repo = tokens[2]
        branch = tokens[3]
        
        links = {}
        for i in range(4, len(tokens), 2):
            links[tokens[i + 1]] = tokens[i]

        return name, path, repo, branch, links


class GilContext:
    """Main context for managing git links and repositories.
    
    Attributes:
        records: Dictionary of discovered git records
        path: Working path
        depth: Maximum recursion depth
    """
    
    def __init__(self, path: str, depth: int = 1000) -> None:
        self.records: Dict[GilRecord, GilRecord] = {}
        self.path = os.path.abspath(path)
        self.depth = depth
        self._processed_paths: Set[str] = set()
        logger.info(f"Working path: {self.path}")

    def show(self) -> None:
        """Display all discovered git records."""
        logger.info("Gil context:")
        for record in self.records.values():
            print(record)

    def _find_root_with_gitlinks(self, start_path: str) -> str:
        """Find the root directory containing a .gitlinks file.
        
        Args:
            start_path: Starting path to search upward from
            
        Returns:
            Root path containing .gitlinks, or start_path if not found
        """
        current = os.path.abspath(start_path)
        root = current
        
        while True:
            parent = os.path.dirname(current)
            if parent == current:  # Reached filesystem root
                break
            
            gitlinks_file = os.path.join(parent, ".gitlinks")
            if os.path.exists(gitlinks_file):
                root = parent
            
            current = parent
        
        return root

    def discover(self, start_path: str) -> None:
        """Discover git links from a starting path.
        
        Args:
            start_path: Path to start discovery from
        """
        current = os.path.abspath(start_path)
        root = self._find_root_with_gitlinks(current)
        
        self._discover_iterative(root)
        
        # Mark active records
        for record in self.records.values():
            if record.path.startswith(current):
                record.active = True

    def _discover_iterative(self, root_path: str) -> None:
        """Iteratively discover repositories to avoid stack overflow.
        
        Args:
            root_path: Root path to start discovery from
        """
        stack: List[Tuple[str, int]] = [(root_path, 0)]
        
        while stack:
            current_path, level = stack.pop(0)
            
            if level >= self.depth:
                logger.error(
                    f"Maximum recursion depth ({self.depth}) reached at {current_path}"
                )
                continue
            
            if current_path in self._processed_paths:
                continue
            
            self._processed_paths.add(current_path)
            
            try:
                records = self._discover_path(current_path)
                for record in records:
                    if record not in self.records:
                        self.records[record] = record
                        stack.append((record.path, level + 1))
            except GilConfigException as e:
                logger.error(f"Configuration error: {e}")
            except Exception as e:
                logger.error(f"Error discovering path {current_path}: {e}")

    def _discover_path(self, path: str) -> List[GilRecord]:
        """Discover git records in a specific path.
        
        Args:
            path: Path to discover
            
        Returns:
            List of discovered records
        """
        gitlinks_file = os.path.join(path, ".gitlinks")
        if not os.path.exists(gitlinks_file):
            return []
        
        logger.info(f"Discovering git links: {gitlinks_file}")
        return self._parse_gitlinks_file(path, gitlinks_file)

    def _parse_gitlinks_file(self, base_path: str, filepath: str) -> List[GilRecord]:
        """Parse a .gitlinks configuration file.
        
        Args:
            base_path: Base path for relative paths in config
            filepath: Path to .gitlinks file
            
        Returns:
            List of parsed records
            
        Raises:
            GilConfigException: If file format is invalid
        """
        records = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    parsed = ConfigParser.parse_line(line, filepath, line_num)
                    if parsed is None:  # Skip empty lines and comments
                        continue
                    
                    name, rel_path, repo, branch, links = parsed
                    abs_path = os.path.abspath(os.path.join(base_path, rel_path))
                    
                    record = GilRecord(name, abs_path, repo, branch, links)
                    if record not in self.records:
                        records.append(record)
        except IOError as e:
            raise GilConfigException(f"Failed to read {filepath}: {e}") from e
        
        return records

    def clone(self, args: Optional[List[str]] = None) -> None:
        """Clone all discovered repositories.
        
        Args:
            args: Additional arguments for git clone
        """
        args = args or []
        stack: List[GilRecord] = list(self.records.values())
        cloned_count = 0
        
        while stack:
            record = stack.pop(0)
            
            if os.path.exists(record.path) and os.listdir(record.path):
                logger.debug(f"Repository already exists: {record.path}")
                # Discover nested repositories
                nested = self._discover_path(record.path)
                for nested_record in nested:
                    if nested_record not in self.records:
                        self.records[nested_record] = nested_record
                        stack.append(nested_record)
                continue
            
            try:
                GitOperations.clone(record.path, record.repo, record.branch, args)
                cloned_count += 1
                
                # Discover nested repositories
                nested = self._discover_path(record.path)
                for nested_record in nested:
                    if nested_record not in self.records:
                        self.records[nested_record] = nested_record
                        stack.append(nested_record)
            except GilGitException as e:
                logger.error(f"Failed to clone {record.name}: {e}")
        
        logger.info(f"Clone complete. {cloned_count} repositories cloned.")

    def link(self, start_path: Optional[str] = None) -> None:
        """Create symlinks for all discovered repositories.
        
        Args:
            start_path: Starting path for linking
        """
        current = os.path.abspath(start_path or self.path)
        root = self._find_root_with_gitlinks(current)
        self._link_records(root)

    def _link_records(self, path: str) -> None:
        """Create symlinks starting from a given path.
        
        Args:
            path: Starting path for linking
        """
        try:
            # Link the root directory
            linked_dirs = self._link_path(path)
            
            # Link all child directories
            for d in linked_dirs:
                self._link_path(d)
            
            # Link all record directories
            for record in self.records.values():
                self._link_path(record.path)
            
            logger.info("Linking complete.")
        except GilLinkException as e:
            logger.error(f"Linking failed: {e}")
            raise

    def _link_path(self, path: str) -> List[str]:
        """Link repositories in a specific path.
        
        Args:
            path: Path to link
            
        Returns:
            List of linked directories
        """
        gitlinks_file = os.path.join(path, ".gitlinks")
        if not os.path.exists(gitlinks_file):
            return []
        
        return self._process_links(path, gitlinks_file)

    def _process_links(self, base_path: str, gitlinks_file: str) -> List[str]:
        """Process and create symlinks from a .gitlinks file.
        
        Args:
            base_path: Base path for relative paths
            gitlinks_file: Path to .gitlinks file
            
        Returns:
            List of linked directories
            
        Raises:
            GilConfigException: If configuration is invalid
            GilLinkException: If linking fails
        """
        linked_dirs = []
        
        try:
            with open(gitlinks_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    parsed = ConfigParser.parse_line(line, gitlinks_file, line_num)
                    if parsed is None:
                        continue
                    
                    name, rel_path, repo, branch, links = parsed
                    abs_path = os.path.abspath(os.path.join(base_path, rel_path))
                    
                    record = GilRecord(name, abs_path, repo, branch, links)
                    
                    # Check if repository exists
                    if record in self.records:
                        base_record = self.records[record]
                        src_path = base_record.path
                        
                        linked_dirs.append(abs_path)
                        FileSystemManager.update_link(src_path, abs_path)
                        
                        # Create custom symlinks if specified
                        for link_name, link_src in links.items():
                            src_link = os.path.abspath(
                                os.path.join(src_path, link_src)
                            )
                            dst_link = os.path.abspath(
                                os.path.join(base_path, link_name)
                            )
                            FileSystemManager.update_link(src_link, dst_link)
                    
                    # Validate repository exists
                    if not (os.path.exists(abs_path) and os.listdir(abs_path)):
                        raise GilLinkException(
                            f"Invalid git link path for {name}: {abs_path} "
                            f"does not exist or is empty"
                        )
        except IOError as e:
            raise GilLinkException(f"Failed to read {gitlinks_file}: {e}") from e
        
        return linked_dirs

    def run_command(
        self,
        command: str,
        args: Optional[List[str]] = None
    ) -> None:
        """Run a git command in all active repositories.
        
        Args:
            command: Git command to run
            args: Command arguments
        """
        args = args or []
        
        logger.info(f"Running command: git {command}")
        
        # Run in root
        try:
            GitOperations.run_command(self.path, command, args)
        except GilGitException as e:
            logger.error(f"Command failed in root: {e}")
        
        # Run in all active records
        for record in self.records.values():
            if record.active:
                try:
                    GitOperations.checkout(record.path, record.branch)
                    GitOperations.run_command(record.path, command, args)
                except GilGitException as e:
                    logger.error(f"Command failed in {record.name}: {e}")


def show_help() -> None:
    """Display help message."""
    help_text = """usage: gil command arguments

Supported commands:
    help       - show this help message
    version    - show version
    context    - show git links context
    clone      - clone git repositories
    link       - create symlinks for git repositories
    update     - clone and link git repositories
    pull       - pull all git repositories
    push       - push all git repositories
    commit     - commit in all git repositories
    status     - show status of all git repositories
"""
    print(help_text)
    sys.exit(1)


def show_version() -> None:
    """Display version."""
    print(__version__)
    sys.exit(0)


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if len(sys.argv) < 2:
        show_help()
    
    command = sys.argv[1]
    
    if command == "help":
        show_help()
    elif command == "version":
        show_version()
    
    try:
        path = os.getcwd()
        context = GilContext(path, depth=1000)
        context.discover(path)
        
        if command == "context":
            context.show()
        elif command == "clone":
            context.clone(sys.argv[2:])
        elif command == "link":
            context.link()
        elif command == "update":
            context.clone()
            context.link()
        elif command in ("pull", "push", "commit", "status"):
            context.run_command(command, sys.argv[2:])
        else:
            logger.error(f"Unknown command: {command}")
            return 1
        
        return 0
    except (GilException, Exception) as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
