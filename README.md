# gym-tcp-api

This project provides a distributed infrastructure (TCP API) to the OpenAI Gym toolkit, allowing development in languages other than python.

The server is written in elixir, enabling a distributed infrastructure. Where each node makes use of a limitted set of processes that can be used to perform time consuming tasks (8 python instances per default).

## Contents

  1. [Dependencies](#dependencies)
  2. [Installation](#installation)
  3. [Getting started](#getting-started)
  3. [Demo](#demo)
  4. [Distributed Server](#distributed-server)
  5. [API specification](#api-specification)

## Dependencies

The server has the following dependencies:

    Elixir >= 1.0
    OpenAI Gym

The c++ example agent has the following dependencies:

      Armadillo     >= 4.200.0
      Boost (system, thread, iostreams)
      CMake         >= 2.8.5

## Installation

### Server

First, checkout the repo and change into the unpacked directory:

      git clone https://github.com/zoq/gym_tcp_api.git
      cd gym_tcp_api

Then install the elixir dependencies:

      $ mix deps.get

### C++ Client

First, checkout the repo and change into the unpacked c++ client directory:

      git clone https://github.com/zoq/gym_tcp_api.git
      cd gym_tcp_api/cpp/

Then, make a build directory. The directory can have any name, not just 'build', but 'build' is sufficient.

      $ mkdir build
      $ cd build

The next step is to run CMake to configure the project. Running CMake is the equivalent to running ./configure with autotools

      $ cmake ../

Once CMake is configured, building the the example agent is as simple as typing 'make'.

      $ make

## Getting started

To start the server from the command line, run:

      $ iex -S mix

In a separate terminal, you can then run the example agent:

      $ ./example

## Demo

The distributed demo server is reachable at ```kurg.org (port 4040```) and can be used for testing. Each node provides access to the Classic control and Atari environments. Note that each node has limited resources so that the response time might vary. If you record your algorithm's performance on an environment you can access the video and metadata at https://kurg.org/media/gym/

<p align="center">
<img src="https://kurg.org/media/breakout_sample.gif" alt="breakout sample image sequence"> <img src="https://kurg.org/media/space_invaders_sample.gif" alt="breakout sample image sequence"> <img src="https://kurg.org/media/enduro_sample.gif" alt="breakout sample image sequence">
</p>

## Distributed Server

First, we need to find out the IP addresses of both machines. In this case, the IP address is 192.168.0.103 for the first machine. On the other machine, the IP address is 192.168.0.104.

In the first window:

     $ iex --name one@192.168.0.103 --cookie "gym" -S mix

In the second window:

    $ iex --name two@192.168.0.104 --cookie "gym" -S mix

In the interactive shell of the second node type:

    $ Node.connect :'one@192.168.0.103'

## API specification
We use JSON is an a format to cimmunicate with the server.

Create the specified environment:

    {"env" {"name": "CartPole-v0"}}

Close the environment:

    {"env" {"action": "close"}}

Reset the state of the environment:

    {"env" {"action": "reset"}}

Set the the enviroment seed:

    {"env" {"seed": "3"}}

Get the action space information:

    {"env" {"action": "actionspace"}}

Get observation space information:

    {"env" {"action": "observationspace"}}

Get action space sample:

    {"env" {"actionspace": "sample"}}

Step though an environment using an action:

    {"step" {"action": "1"}}

    {"step" {"action": "[0, 1, 0, 0]"}}

Start the monitor:

    {"monitor" {"action": "start", "force" : "1", "resume" : "0", "directory", "/home/gym/"}}

Close the monitor:

    {"monitor" {"action": "close"}}
