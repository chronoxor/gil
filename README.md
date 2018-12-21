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
  * [Usage](#usage)

# Requirements
* Linux
* OSX
* Windows 10
* [git](https://git-scm.com)
* [python3](https://www.python.org)

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

# Usage
