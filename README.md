# cmtg

The signal level monitoring system, that uses programmable modules [Pololu Wixel](https://www.pololu.com/product/1336) for spectrum analysis. It was developed at context of the [research work](https://ieeexplore.ieee.org/document/8632151).
> Note: the publication is based on the draft version of the monitoring system. However, it had the same concepts of realization.

**cmtg** is [Python3.7+](https://docs.python.org/3/) application, that provides real-time signal level monitoring at range 2403.47–2476.50 MHz. For example, you can improve Wi-Fi router work quality, by checking free channels. It's built by client-server architecture and has interactive Web UI.
The monitoring system was designed with attention to run it on the **single-board computers** like [Raspberry Pi](https://www.raspberrypi.org/).
> Note: first two versions of the monitoring system: [COMonitoring](https://github.com/anzodev/COMonitoring), [COMonitoring2](https://github.com/anzodev/COMonitoring2).

![cmtg Web UI](https://github.com/anzodev/cmtg/blob/media/web-interface.png)

## [Hardware](#hardware)

The programmable module Pololu Wixel is based on the [CC2511F32](http://www.ti.com/product/CC2511) system-on-chip (SoC), which has an integrated 2.4 GHz radio transceiver. We can load [firmware](https://github.com/anzodev/cmtg/tree/master/wixel-sdk/apps/spectrum_analysis) to scan radio ether on different channels:
1. Install platform-specific [driver](https://www.pololu.com/docs/0J46/3).
2. Turn the module's [bootloader mode](https://www.pololu.com/docs/0J46/5.c) and connect it to the computer.
3. Load the firmware (file with .wxl extension) via [Wixel Configuration Utility](https://www.pololu.com/docs/0J46/3.d).
> Note: there is alternative way to load firmware via [wixel-sdk](https://pololu.github.io/wixel-sdk/). Get more details by [Pololu Wixel User's Guide](https://www.pololu.com/docs/0J46).

On Linux distributions, you have to set group [dialout](https://wiki.debian.org/SystemGroups) (for our case it gives serial port access):
```bash
$ sudo usermod -aG dialout $USER
```
Otherwise, you should run monitoring system with **root permissions**.

> Note: if you don't have Pololu Wixel modules, the monitoring system supports functional, that emulates module's connection. So, you can check how monitoring system works without real modules. This is described at [run](#run) section.


## [Startup with docker](#startup-with-docker)

This is the simplest way to run application:
1. Install [docker](https://docs.docker.com/install/).
2. Clone repository:
```bash
$ git clone https://github.com/anzodev/cmtg.git
```
3. Build docker image:
```bash
$ cd cmtg
$ docker build -t cmtg .
```

After that, you will have docker image with *cmtg:latest* tag, but you can set your specific [tag](https://docs.docker.com/engine/reference/commandline/build/#tag-an-image--t).  
The monitoring system [run process](#run-docker-container) is described below.

## [Startup with Python virtual environment](#startup-with-python-virtual-environment)

Firstly, install Python3.7. There are several platform-specific ways to install Python interpreters ([see more](https://docs.python.org/3/using/index.html)).
However, we recommend to use [pyenv](https://github.com/pyenv/pyenv) tool. It's preferable way to manage several Python interpreters on single machine.
> Note: if you use [Raspbian](https://www.raspberrypi.org/downloads/raspbian/), the Python3.7 is installed already by system (actual info for 2019-07-10 release date). So, you can just install virtualenv, because pyenv compiles interpreter from source, that can take much time.

After the interpreter is installed, you have several ways to get [virtualenv](https://pypi.org/project/virtualenv/) tool:
* With pyenv there is available [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) plugin already. You don't need to install virtualenv.
* There is [Pipfile](https://github.com/anzodev/cmtg/blob/master/Pipfile) file at project repository, so you can use [pipenv](https://docs.pipenv.org/en/latest/) tool (this alternative way, use it your own).
* Use method, that is described in [docs](https://virtualenv.pypa.io/en/latest/installation/).


Create [environment](https://virtualenv.pypa.io/en/latest/userguide/#usage), activate it and install dependencies from [requirements.txt](https://github.com/anzodev/cmtg/blob/master/requirements.txt) file:
```bash
(cmtg-venv)$ pip install -r requirements.txt
```
Lets reproduce all steps using pyenv (**don't forget** to check [prerequisites](https://github.com/pyenv/pyenv/wiki/Common-build-problems)):
```bash
# Install pyenv.
$ curl https://pyenv.run | bash

# Install Python3.7 interpreter.
$ pyenv install 3.7.4 -v

# Create virtual environment.
$ pyenv virtualenv 3.7.4 cmtg-venv

# Clone repository.
$ mkdir ~/apps && cd ~/apps
$ git clone https://github.com/anzodev/cmtg.git

# Activate virtual environment.
$ cd cmtg
$ pyenv activate cmtg-venv

# Install dependencies.
(cmtg-venv)$ pip install -r requirements.txt
```


## [Run](#run)

Note, that you have to run cmtg package **as module**:
```bash
$ python -m cmtg
```

The application supports some command line arguments:
```
$ python -m cmtg -h
usage: cmtg [-h] [--log string] [--host string] [--port int] [--wxls int]

Pololu Wixel Spectrum Analysis (monitoring system).

optional arguments:
  -h, --help     show this help message and exit
  --log string   system logs level
  --host string  web service host
  --port int     web service port
  --wxls int     quantity of emulated Pololu Wixel connections
```

| arguments | type | default   | description                                                                                                                                                                                               |
| --------- | ---- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--log`   | str  | "INFO"    | The system log's handler level. Supported values: "NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL". Get more details from [docs](https://docs.python.org/3/library/logging.html#logging-levels). |
| `--host`  | str  | "0.0.0.0" | The web service host.                                                                                                                                                                                     |
| `--port`  | int  | 5000      | The web service port.                                                                                                                                                                                     |
| `--wxls`  | int  | 0         | The quantity of emulated Pololu Wixel connections. If you set emulated connections, the real module connection **will not recognize anymore** while app is running.                                       |

### [Run docker container](#run-docker-container)
You can run docker container after the [docker image](#startup-with-docker) is built. There are two important options:
1. The `/dev` volume is required, that the monitoring system works with dynamically plugged modules.
2. Run container with `--privileged` option to give monitoring system access for serial port reading.

Also, you have to **publish [port](https://docs.docker.com/config/containers/container-networking/#published-ports)** to get access for web service. For example:
``` bash
# Run the monitoring system for real module connections and change logs level.
$ docker run -p 5000:5000 -v /dev:/dev --privileged cmtg:latest --log DEBUG

# Run the monitoring system with 2 emulated Pololu Wixel modules.
$ docker run -p 5000:5000 cmtg:latest --wxls 2
```


### [Run into the virtual environment](#run-into-the-virtual-environment)
Firstly, you need to activate your virtual environment. After that, run the monitoring system. For example:
```bash
# Run the monitoring system and change port.
(cmtg-venv)$ python -m cmtg --port 8080

# Run the monitoring system with 2 emulated Pololu Wixel modules
# and change host.
(cmtg-venv)$ python -m cmtg --wxls 2 --host 127.0.0.1
```


## [Todo](#todo)
- [ ] To add the functional for neighbor cmtg app detection at the local network (common access point).
- [ ] To add parameters for controlling intervals of some operations (e.g. search connected modules, read data from serial).


## [Authors](#authors)
[Vladimir Sokolov](https://github.com/Oestoidea) (manager)  
Ivan Bogachuk (developer)
