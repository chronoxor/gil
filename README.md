# Gil (git link)

[![Linux build status](https://img.shields.io/travis/chronoxor/gil/master.svg?label=Linux)](https://travis-ci.org/chronoxor/gil)
[![OSX build status](https://img.shields.io/travis/chronoxor/gil/master.svg?label=OSX)](https://travis-ci.org/chronoxor/gil)
[![Cygwin build status](https://img.shields.io/appveyor/ci/chronoxor/gil/master.svg?label=Cygwin)](https://ci.appveyor.com/project/chronoxor/gil)
[![MinGW build status](https://img.shields.io/appveyor/ci/chronoxor/gil/master.svg?label=MinGW)](https://ci.appveyor.com/project/chronoxor/gil)
[![Windows build status](https://img.shields.io/appveyor/ci/chronoxor/gil/master.svg?label=Windows)](https://ci.appveyor.com/project/chronoxor/gil)

Gil (git link) tool allows to describe and manage complex git repositories
dependency with cycles and cross references.

This tool provies a solution to the recursive git submodules dependency
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

Where:
* Blue rectangles are third-party components
* Green rectangles are components that we develop
* Arrows show dependency with branch name

![gil sample](https://github.com/chronoxor/gil/raw/master/images/sample.png)

In order to describe the sample model with git links we have to define root
.gitlink file with a following content:
```
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
2. Relative path of the repository (started from the path of .gitlink file)
3. Git repository which will be used in 'git clone' command
4. Repository branch to checkout

Empty line or line started with '#' are not parsed (treated as comment).

# Usage
