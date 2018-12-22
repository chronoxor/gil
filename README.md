# Gil (git link)

[![Linux build status](https://img.shields.io/travis/chronoxor/gil/master.svg?label=Linux)](https://travis-ci.org/chronoxor/gil)
[![OSX build status](https://img.shields.io/travis/chronoxor/gil/master.svg?label=OSX)](https://travis-ci.org/chronoxor/gil)
[![Cygwin build status](https://img.shields.io/appveyor/ci/chronoxor/gil/master.svg?label=Cygwin)](https://ci.appveyor.com/project/chronoxor/gil)
[![MinGW build status](https://img.shields.io/appveyor/ci/chronoxor/gil/master.svg?label=MinGW)](https://ci.appveyor.com/project/chronoxor/gil)
[![Windows build status](https://img.shields.io/appveyor/ci/chronoxor/gil/master.svg?label=Windows)](https://ci.appveyor.com/project/chronoxor/gil)

Gil (git link) tool allows to describe and manage complex git repositories
dependency with cycles and cross references.

This tool provides a solution to the recursive git submodules dependency
problem.

# Contents
  * [Requirements](#requirements)
  * [Setup](#setup)
  * [Sample](#sample)
  * [Usage](#usage)

# Requirements
* Linux
* OSX
* Windows 10
* [git](https://git-scm.com)
* [python](https://www.python.org)

# Setup

### Clone repository
```shell
git clone https://github.com/chronoxor/git.git
```

### Linux, OSX
```shell
# Add gil (git link) tool alias in .bashrc
alias gil=~/gil/gil.sh
```

### Windows
```shell
# Add gil (git link) tool to the PATH environment variable
PATH=%HOMEDRIVE%%HOMEPATH%\gil;%PATH%
```

# Sample
Consider we have the following git repository dependency.

![gil sample](https://github.com/chronoxor/gil/raw/master/images/sample.png)

Where:
* Blue rectangles are third-party components
* Green rectangles are components that we develop
* Arrows show dependency with branch name

## Root .gitlinks file
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

Empty line or line started with `#` are not parsed (treated as comment).

## CppBenchmark .gitlinks file
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

## CppCommon .gitlinks file
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

## CppLogging .gitlinks file
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

## Update the repository
Finally you have to update your root sample repository:
```shell
# Clone and link all gil (git link) dependencies from .gitlinks file
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
Update Git Link: ~/gil/sample/modules/Catch2 -> ~/gil/sample/CppBenchmark/modules/Catch2
Update Git Link: ~/gil/sample/modules/cpp-optparse -> ~/gil/sample/CppBenchmark/modules/cpp-optparse
Update Git Link: ~/gil/sample/modules/HdrHistogram -> ~/gil/sample/CppBenchmark/modules/HdrHistogram
Update Git Link: ~/gil/sample/modules/zlib -> ~/gil/sample/CppBenchmark/modules/zlib
Update Git Link: ~/gil/sample/scripts/build -> ~/gil/sample/CppBenchmark/build
Update Git Link: ~/gil/sample/scripts/cmake -> ~/gil/sample/CppBenchmark/cmake
Updating git links: ~/gil/sample/CppCommon/.gitlinks
Update Git Link: ~/gil/sample/modules/Catch2 -> ~/gil/sample/CppCommon/modules/Catch2
Update Git Link: ~/gil/sample/CppBenchmark -> ~/gil/sample/CppCommon/modules/CppBenchmark
Update Git Link: ~/gil/sample/modules/fmt -> ~/gil/sample/CppCommon/modules/fmt
Update Git Link: ~/gil/sample/scripts/build -> ~/gil/sample/CppCommon/build
Update Git Link: ~/gil/sample/scripts/cmake -> ~/gil/sample/CppCommon/cmake
Updating git links: ~/gil/sample/CppLogging/.gitlinks
Update Git Link: ~/gil/sample/modules/Catch2 -> ~/gil/sample/CppLogging/modules/Catch2
Update Git Link: ~/gil/sample/modules/cpp-optparse -> ~/gil/sample/CppLogging/modules/cpp-optparse
Update Git Link: ~/gil/sample/CppBenchmark -> ~/gil/sample/CppLogging/modules/CppBenchmark
Update Git Link: ~/gil/sample/CppCommon -> ~/gil/sample/CppLogging/modules/CppCommon
Update Git Link: ~/gil/sample/modules/zlib -> ~/gil/sample/CppLogging/modules/zlib
Update Git Link: ~/gil/sample/scripts/build -> ~/gil/sample/CppLogging/build
Update Git Link: ~/gil/sample/scripts/cmake -> ~/gil/sample/CppLogging/cmake
```

All repositories will be checkout to required branches.

If content of any .gitlinks changes it is required to run `gil update` command
to re-update git links - new repositories will be cloned and linked properly!

## Commit, push, pull
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

## Build
Please investigate and follow links in the sample repository in order to
understand the logic how gil (git link) tool manages dependencies.

Finally you can build sample projects with provided build scripts:
* ~/gil/sample/CppBenchmark/build
* ~/gil/sample/CppCommon/build
* ~/gil/sample/CppLogging/build

# Usage
Gil (git link) tool supports the following commands:
```
usage: gil command arguments
Supported commands:
        help - show this help
        context - show git links context
        clone - clone git repositories
        link - link git repositories
        update - update git repositories (clone & link)
        pull - pull git repositories
        push - push git repositories
        commit - commit git repositories
```

* `gil context` - command will show the current git link context of the current directory;
* `gil clone [args]` - clone all repositories that are missed in the current context;
* `gil link` - link all repositories that are missed in the current context;
* `gil update` - clone and link in a single operation;
* `gil pull [args]` - pull all repositories in the current directory;
* `gil push [args]` - push all repositories in the current directory;
* `gil commit [args]` - commit all repositories in the current directory;
