# Gil (git links) tool

[![Linux (clang)](https://github.com/chronoxor/gil/actions/workflows/build-linux-clang.yml/badge.svg)](https://github.com/chronoxor/gil/actions/workflows/build-linux-clang.yml)
[![Linux (gcc)](https://github.com/chronoxor/gil/actions/workflows/build-linux-gcc.yml/badge.svg)](https://github.com/chronoxor/gil/actions/workflows/build-linux-gcc.yml)
<br/>
[![MacOS](https://github.com/chronoxor/gil/actions/workflows/build-macos.yml/badge.svg)](https://github.com/chronoxor/gil/actions/workflows/build-macos.yml)
<br/>
[![Windows (Cygwin)](https://github.com/chronoxor/gil/actions/workflows/build-windows-cygwin.yml/badge.svg)](https://github.com/chronoxor/gil/actions/workflows/build-windows-cygwin.yml)
[![Windows (MSYS2)](https://github.com/chronoxor/gil/actions/workflows/build-windows-msys2.yml/badge.svg)](https://github.com/chronoxor/gil/actions/workflows/build-windows-msys2.yml)
[![Windows (MinGW)](https://github.com/chronoxor/gil/actions/workflows/build-windows-mingw.yml/badge.svg)](https://github.com/chronoxor/gil/actions/workflows/build-windows-mingw.yml)
[![Windows (Visual Studio)](https://github.com/chronoxor/gil/actions/workflows/build-windows-vs.yml/badge.svg)](https://github.com/chronoxor/gil/actions/workflows/build-windows-vs.yml)

Gil is a git links tool to manage complex git repositories dependencies with
cycles and cross references.

This tool provides a solution to the [git recursive submodules dependency problem](https://github.com/chronoxor/gil#recursive-submodules-problem).

# Contents
  * [Requirements](#requirements)
  * [Setup](#setup)
  * [Sample](#sample)
  * [Usage](#usage)
  * [Motivation: git submodules vs git links](#motivation-git-submodules-vs-git-links)
    * [Git submodules management](#git-submodules-management)
    * [Recursive submodules problem](#recursive-submodules-problem)
  * [Motivation: git subtrees vs git links](#motivation-git-subtrees-vs-git-links)
    * [Git subtrees management](#git-subtrees-management)
    * [Subtrees manual management problem](#subtrees-manual-management-problem)

# Requirements
* Linux
* MacOS
* Windows
* [git](https://git-scm.com)
* [python3](https://www.python.org)

# Setup

```shell
sudo pip3 install --prefix /usr/local gil
```

# Sample
Consider we have the following git repository dependency graph:

![gil sample](https://github.com/chronoxor/gil/raw/master/images/sample.png)

Where:
* Blue nodes are third-party components
* Green nodes are components that we develop
* Edges show components dependency with a branch

### Root .gitlinks file
In order to describe the sample model with git links we have to define root
.gitlinks file in your sample repository with a following content:
```shell
# Projects
CppBenchmark CppBenchmark https://github.com/chronoxor/CppBenchmark.git master
CppCommon CppCommon https://github.com/chronoxor/CppCommon.git master
CppLogging CppLogging https://github.com/chronoxor/CppLogging.git master

# Modules
Catch2 modules/Catch2 https://github.com/catchorg/Catch2.git master
cpp-optparse modules/cpp-optparse https://github.com/weisslj/cpp-optparse.git master
fmt modules/fmt https://github.com/fmtlib/fmt.git master
HdrHistogram modules/HdrHistogram https://github.com/HdrHistogram/HdrHistogram_c.git master
zlib modules/zlib https://github.com/madler/zlib.git master

# Scripts
build scripts/build https://github.com/chronoxor/CppBuildScripts.git master
cmake scripts/cmake https://github.com/chronoxor/CppCMakeScripts.git master
```

Each line describe git link in the following format:
1. Unique name of the repository
2. Relative path of the repository (started from the path of .gitlinks file)
3. Git repository which will be used in `git clone` command
4. Repository branch to checkout
5. (Optional) Relative path in the base repository
6. (Optional) Relative path in the target repository

Empty line or line started with `#` are not parsed (treated as comment).

### CppBenchmark .gitlinks file
CppBenchmark .gitlinks file should be committed into the CppBenchmark project
and have the following content:
```shell
# Modules
Catch2 modules/Catch2 https://github.com/catchorg/Catch2.git master
cpp-optparse modules/cpp-optparse https://github.com/weisslj/cpp-optparse.git master
HdrHistogram modules/HdrHistogram https://github.com/HdrHistogram/HdrHistogram_c.git master
zlib modules/zlib https://github.com/madler/zlib.git master

# Scripts
build build https://github.com/chronoxor/CppBuildScripts.git master
cmake cmake https://github.com/chronoxor/CppCMakeScripts.git master
```

### CppCommon .gitlinks file
CppCommon .gitlinks file should be committed into the CppCommon project and
have the following content:
```shell
# Modules
Catch2 modules/Catch2 https://github.com/catchorg/Catch2.git master
CppBenchmark modules/CppBenchmark https://github.com/chronoxor/CppBenchmark.git master
fmt modules/fmt https://github.com/fmtlib/fmt.git master

# Scripts
build build https://github.com/chronoxor/CppBuildScripts.git master
cmake cmake https://github.com/chronoxor/CppCMakeScripts.git master
```

### CppLogging .gitlinks file
CppLogging .gitlinks file should be committed into the CppLogging project and
have the following content:
```shell
# Modules
Catch2 modules/Catch2 https://github.com/catchorg/Catch2.git master
cpp-optparse modules/cpp-optparse https://github.com/weisslj/cpp-optparse.git master
CppBenchmark modules/CppBenchmark https://github.com/chronoxor/CppBenchmark.git master
CppCommon modules/CppCommon https://github.com/chronoxor/CppCommon.git master
zlib modules/zlib https://github.com/madler/zlib.git master

# Scripts
build build https://github.com/chronoxor/CppBuildScripts.git master
cmake cmake https://github.com/chronoxor/CppCMakeScripts.git master
```

### Update the repository
Finally you have to update your root sample repository:
```shell
# Clone and link all git links dependencies from .gitlinks file
gil clone
gil link

# The same result with a single command
gil update
```

As the result you'll clone all required projects and link them to each other
in a proper way:
```shell
Working path: ~/gil/sample
...
Updating git links: ~/gil/sample/.gitlinks
Updating git links: ~/gil/sample/CppBenchmark/.gitlinks
Update git link: ~/gil/sample/modules/Catch2 -> ~/gil/sample/CppBenchmark/modules/Catch2
Update git link: ~/gil/sample/modules/cpp-optparse -> ~/gil/sample/CppBenchmark/modules/cpp-optparse
Update git link: ~/gil/sample/modules/HdrHistogram -> ~/gil/sample/CppBenchmark/modules/HdrHistogram
Update git link: ~/gil/sample/modules/zlib -> ~/gil/sample/CppBenchmark/modules/zlib
Update git link: ~/gil/sample/scripts/build -> ~/gil/sample/CppBenchmark/build
Update git link: ~/gil/sample/scripts/cmake -> ~/gil/sample/CppBenchmark/cmake
Updating git links: ~/gil/sample/CppCommon/.gitlinks
Update git link: ~/gil/sample/modules/Catch2 -> ~/gil/sample/CppCommon/modules/Catch2
Update git link: ~/gil/sample/CppBenchmark -> ~/gil/sample/CppCommon/modules/CppBenchmark
Update git link: ~/gil/sample/modules/fmt -> ~/gil/sample/CppCommon/modules/fmt
Update git link: ~/gil/sample/scripts/build -> ~/gil/sample/CppCommon/build
Update git link: ~/gil/sample/scripts/cmake -> ~/gil/sample/CppCommon/cmake
Updating git links: ~/gil/sample/CppLogging/.gitlinks
Update git link: ~/gil/sample/modules/Catch2 -> ~/gil/sample/CppLogging/modules/Catch2
Update git link: ~/gil/sample/modules/cpp-optparse -> ~/gil/sample/CppLogging/modules/cpp-optparse
Update git link: ~/gil/sample/CppBenchmark -> ~/gil/sample/CppLogging/modules/CppBenchmark
Update git link: ~/gil/sample/CppCommon -> ~/gil/sample/CppLogging/modules/CppCommon
Update git link: ~/gil/sample/modules/zlib -> ~/gil/sample/CppLogging/modules/zlib
Update git link: ~/gil/sample/scripts/build -> ~/gil/sample/CppLogging/build
Update git link: ~/gil/sample/scripts/cmake -> ~/gil/sample/CppLogging/cmake
```

All repositories will be checkout to required branches.

If content of any .gitlinks changes it is required to run `gil update` command
to re-update git links - new repositories will be cloned and linked properly!

### Commit, push, pull
You can work and change any files in your repositories and perform all git
operations for any repository to commit and contribute your changes.

If you want to commit all changes in some repository with all changes in
child linked repositories you can do it with a single command:
```shell
gil commit -a -m "Some big update"
```

This command will visit the current and all child repositories and perform
the corresponding `git commit` command with provided arguments.

Please note that gil command visit only child repositories that are described
in .gitlinks file no parent dependencies will be processed. For this reason
if you want to commit, pull or push all repositories the corresponding command
should be run in the root directory where root .gitlinks is placed.

Pull, push commands works in a similar way:
```shell
gil pull
gil push
```

### Build
Please investigate and follow links in the sample repository in order to
understand the logic how gil (git links) tool manages dependencies.

Finally you can build sample projects with provided build scripts:
* `~/gil/sample/CppBenchmark/build`
* `~/gil/sample/CppCommon/build`
* `~/gil/sample/CppLogging/build`

Additionally each module can be cloned and successfully build without root
repository. In this case local .gitlinks file will be used to resolve all
dependencies!

# Usage
Gil (git links) tool supports the following commands:
```
usage: gil command arguments
Supported commands:
        help - show this help
        version - show version
        context - show git links context
        clone [args] - clone git repositories
        link - link git repositories
        update - update git repositories (clone & link)
        pull [args] - pull git repositories
        push [args] - push git repositories
        commit [args] - commit git repositories
        status [args] - show status of git repositories
```

* `gil context` - command will show the current git link context of the current directory;
* `gil clone [args]` - clone all repositories that are missed in the current context;
* `gil link` - link all repositories that are missed in the current context;
* `gil update` - clone and link in a single operation;
* `gil pull [args]` - pull all repositories in the current directory;
* `gil push [args]` - push all repositories in the current directory;
* `gil commit [args]` - commit all repositories in the current directory;
* `gil status [args]` - show status of all repositories in the current directory;

# Motivation: git submodules vs git links
Git submodules allow to get the same idea of repositories dependency, but with
a serious limitation - git submodules degrade to tree-like recursive structure
with repositories duplication.

## Git submodules management
Git submodules provides several operations to manage repositories dependency.

### Add submodule dependency
```shell
# Add git submodule of 'master' branch into the relative directory 'modules/zlib'
git submodule add -b master https://github.com/madler/zlib.git modules/zlib
```

### Initialize submodules
```shell
# Update all submodules in the current repository
git submodule update --init --recursive --remote
```

### Refresh submodules from remote repositories
```shell
git pull
git submodule update --init --recursive --remote
git pull --recurse-submodules
git submodule foreach "(git checkout master; git pull)"
```

### Synchronize submodules with remote repositories
```shell
git pull
git submodule update --init --recursive --remote
git pull --recurse-submodules
git submodule foreach "(git checkout master; git pull)"
git add --all
git commit -m "Submodule Sync"
git push
```

### Remove submodule dependency
```shell
# Remove git submodule from the relative directory 'modules/zlib'
git submodule deinit -f -- modules/zlib
rm -rf .git/modules/modules/zlib
git rm -f modules/zlib
```

## Recursive submodules problem
Git submodules representation of the described sample repository is the
following:
```shell
~/gil/sample/CppBenchmark
~/gil/sample/CppBenchmark/build
~/gil/sample/CppBenchmark/cmake
~/gil/sample/CppBenchmark/modules/Catch2
~/gil/sample/CppBenchmark/modules/cpp-optparse
~/gil/sample/CppBenchmark/modules/HdrHistogram
~/gil/sample/CppBenchmark/modules/zlib
~/gil/sample/CppCommon
~/gil/sample/CppCommon/build - DUPLICATE!
~/gil/sample/CppCommon/cmake - DUPLICATE!
~/gil/sample/CppCommon/modules/Catch2 - DUPLICATE!
~/gil/sample/CppCommon/modules/CppBenchmark - DUPLICATE!
~/gil/sample/CppCommon/modules/CppBenchmark/build - DUPLICATE!
~/gil/sample/CppCommon/modules/CppBenchmark/cmake - DUPLICATE!
~/gil/sample/CppCommon/modules/CppBenchmark/modules/Catch2 - DUPLICATE!
~/gil/sample/CppCommon/modules/CppBenchmark/modules/cpp-optparse - DUPLICATE!
~/gil/sample/CppCommon/modules/CppBenchmark/modules/HdrHistogram - DUPLICATE!
~/gil/sample/CppCommon/modules/CppBenchmark/modules/zlib - DUPLICATE!
~/gil/sample/CppCommon/modules/fmt
~/gil/sample/CppLogging
~/gil/sample/CppLogging/build - DUPLICATE!
~/gil/sample/CppLogging/cmake - DUPLICATE!
~/gil/sample/CppLogging/modules/Catch2 - DUPLICATE!
~/gil/sample/CppLogging/modules/cpp-optparse - DUPLICATE!
~/gil/sample/CppLogging/modules/CppBenchmark - DUPLICATE!
~/gil/sample/CppLogging/modules/CppBenchmark/build - DUPLICATE!
~/gil/sample/CppLogging/modules/CppBenchmark/cmake - DUPLICATE!
~/gil/sample/CppLogging/modules/CppBenchmark/modules/Catch2 - DUPLICATE!
~/gil/sample/CppLogging/modules/CppBenchmark/modules/cpp-optparse - DUPLICATE!
~/gil/sample/CppLogging/modules/CppBenchmark/modules/HdrHistogram - DUPLICATE!
~/gil/sample/CppLogging/modules/CppBenchmark/modules/zlib - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon/build - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon/cmake - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon/modules/Catch2 - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon/modules/CppBenchmark - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon/modules/CppBenchmark/build - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon/modules/CppBenchmark/cmake - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon/modules/CppBenchmark/modules/Catch2 - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon/modules/CppBenchmark/modules/cpp-optparse - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon/modules/CppBenchmark/modules/HdrHistogram - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon/modules/CppBenchmark/modules/zlib - DUPLICATE!
~/gil/sample/CppLogging/modules/zlib - DUPLICATE!
```

Only 10 of 41 repositories are unique. Other duplicates each other multiple
times. Moreover some nested repositories included recursively! CppLogging
project has the third level of nesting (`CppLogging -> CppCommon -> CppBenchmark`).

Each new level heavily increases the rate of duplication. As the result all
submodule management operations becomes slow and requires multiple executions
of synchronize script to pass changes from top level to the bottom. The count
of synchronizations in the worst case equals to recursive levels count.

All this issues are solved with gil (git links) tool which allows to link all
required repositories together avoiding duplication. The tool also provides
operations to manage changes in all repositories with a [simple easy to use
commands](https://github.com/chronoxor/gil#usage).

# Motivation: git subtrees vs git links
Git subtrees is an easy to use alternative to git submodules. It allows to nest
one repository inside another as a sub-directory.

From the one side git subtrees are very lightweight with simple workflow. They
don't add any metadata files like git submodule does (i.e., .gitmodule) and
sub-project's code is available right after the clone of the super project is
done. Contents of the module can be modified without having a separate
repository copy of the dependency somewhere else.

However they have several drawbacks. Contributing code back upstream for the
sub-projects is slightly more complicated. And developer should be very careful
of not mixing super and sub-project code in commits.

Git subtrees requires precise manual management in case use have complicated
projects structure and lots of upstream commits to dependent projects.

## Git subtrees management
Git subtrees provides several operations to manage repositories dependency.

### Add subtree dependency
```shell
# Add git subtree of 'master' branch into the relative directory 'modules/zlib'
git subtree add -P modules/zlib https://github.com/madler/zlib.git master --squash
```

### Update subtree from the upstream remote repository
```shell
git subtree pull -P modules/zlib https://github.com/madler/zlib.git master --squash
```

### Contribute changes from subtree back to the upstream remote repository
```shell
git subtree push -P modules/zlib https://github.com/madler/zlib.git master
```

### Remove subtree dependency
```shell
# Remove git subtree from the relative directory 'modules/zlib'
git rm -f modules/zlib
```

## Subtrees manual management problem
Initially git subtrees lack of the same [repository duplicate problem](#recursive-submodules-problem)
which git submodules have. Therefore all repositories with multiple dependencies
will be duplicated and require manual and careful management.

For instance `CppBenchmark` repository presented four times in our [sample](#sample):
```shell
~/gil/sample/CppBenchmark
~/gil/sample/CppCommon/modules/CppBenchmark - DUPLICATE!
~/gil/sample/CppLogging/modules/CppBenchmark - DUPLICATE!
~/gil/sample/CppLogging/modules/CppCommon/modules/CppBenchmark - DUPLICATE!
```

The first problem if you updated `CppBenchmark` and want to get the fix in all
dependent repositories you have to update them manually with the set of
`git subtree pull` commands:
```shell
# Commit and push changes in CppBenchmark repository
cd CppBenchmark
git commit -a -m "Bugfix in CppBenchmark"
git push
cd ..

# Update CppCommon repository
cd CppCommon
git subtree pull --prefix modules/CppBenchmark https://github.com/chronoxor/test-CppBenchmark.git main --squash
git push
cd ..

# Update CppLogging repository
cd CppLogging
git subtree pull --prefix modules/CppBenchmark https://github.com/chronoxor/test-CppBenchmark.git main --squash
git subtree pull --prefix modules/CppCommon https://github.com/chronoxor/test-CppCommon.git main --squash
git push
cd ..
```

The second problem if you found a bug in `CppBenchmark` while debugging
`CppLogging` and want to fix it in place, push the changes and update all
repositories properly. In this case you need to make the following steps:
```shell
# Commit and push changes in CppBenchmark but from CppLogging repository
cd CppLogging
git commit -a -m "Bugfix in CppBenchmark (found in CppLogging repository)"
git push
git subtree push --prefix modules/CppBenchmark https://github.com/chronoxor/test-CppBenchmark.git main --squash
cd ..

# Update CppBenchmark repository
cd CppBenchmark
git pull
cd ..

# Update CppCommon repository
cd CppCommon
git subtree pull --prefix modules/CppBenchmark https://github.com/chronoxor/test-CppBenchmark.git main --squash
git push
cd ..

# Update CppLogging repository
cd CppLogging
git subtree pull --prefix modules/CppBenchmark https://github.com/chronoxor/test-CppBenchmark.git main --squash
git subtree pull --prefix modules/CppCommon https://github.com/chronoxor/test-CppCommon.git main --squash
git push
cd ..
```

As the result too much manual work should be done to make all repositories up
to date. Definitely all commands should be stored into scripts with care. And
this job requires some efforts and testing because it is very easy to make a
mistake. Git subtrees are good and easy to use for small repositories without
complicated hierarchy. But working with huge complicated repositories using
git subtrees is a big challenge as git subtrees do not suppot recursing
pull/push/update commands.
