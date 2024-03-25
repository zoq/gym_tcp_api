# gym-tcp-api

This project provides a distributed infrastructure (TCP API) to the OpenAI Gym toolkit, allowing development in languages other than python.

The server is written in elixir, enabling a distributed infrastructure. Where each node makes use of a limitted set of processes that can be used to perform time consuming tasks (4 python instances per default).

## Contents

  1. [Dependencies](#dependencies)
  2. [Installation](#installation)
  3. [Getting started](#getting-started)
  3. [Demo](#demo)
  4. [Distributed Server](#distributed-server)
  5. [API specification](#api-specification)
  6. [FAQ](#faq)

## Dependencies

The server has the following dependencies:

    Python3
    Elixir >= 1.0
    OpenAI Gym.

The c++ example agent has the following dependencies:

      Armadillo     >= 4.200.0
      Boost (system, thread, iostreams)
      CMake         >= 2.8.5

## Installation

### Server

First, checkout the repo and change into the unpacked directory:

      $  git clone https://github.com/zoq/gym_tcp_api.git
      $  cd gym_tcp_api

Then install the elixir dependencies:

      $ mix deps.get

### C++ Client

First, checkout the repo and change into the unpacked c++ client directory:

      $  git clone https://github.com/zoq/gym_tcp_api.git
      $  cd gym_tcp_api/cpp/

Then, make a build directory. The directory can have any name, not just 'build', but 'build' is sufficient.

      $ mkdir build
      $ cd build

The next step is to run CMake to configure the project. Running CMake is the equivalent to running ./configure with autotools

      $ cmake ../

Once CMake is configured, building the example agent is as simple as typing 'make'.

      $ make

## Getting started

To start the server from the command line:
   * For Python server run:
    
          $ python python/server.py
    
   * For Elixir server run:

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
We use JSON as the format to cimmunicate with the server.

Create the specified environment:

    {"env" {"name": "CartPole-v0"}}

Close the environment:

    {"env" {"action": "close"}}

Reset the state of the environment:

    {"env" {"action": "reset"}}

Set the enviroment seed:

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

Start the record episode statistics:

    {"record_episode_stats" {"action": "start"}}
  
## FAQ
<b>1. In the Erlang/OTP 21, erlport may not be compiled, because the latest version was not reflected in the official Erlport GitHub.</b>

  - SOL) Change the version of erlport manually in <b>mix.exs</b>. As of October, 2018, the "0.10.0" version worked. See this https://github.com/hdima/erlport
    ```
    defp deps do
        [
          {:erlport, "~> 0.10.0"}, # Choose the version.
          {:poolboy, "~> 1.5"}
        ]
    end
    ```
  
<b>2. Failed to fetch record for 'hexpm/poolboy' from registry (using cache)</b>

  - SOL) This was a cache problem, remove the cache file and try again.
    ```bash
    rm "~/.hex/cache.ets"
    ```
    
<b>3. TypeError: super() takes at least 1 argument (0 given)
            super().__init__((), np.int64) </b>
  
  - SOL 1) Using Python3 VirtualEnv (Recommended).

        $ virtualenv -p python3 envname
          
  - SOL 2) Make Python3 as the default Python (since gym is built on Python3).

        $ sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
