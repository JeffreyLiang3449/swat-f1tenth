# mac-sim

A simulator setup and terminal tool for working on the RoboRacer from a Mac, plus scripts
for driving the real car over SSH. Everything runs through one command, `rr`.

This folder has a `COLCON_IGNORE` in it, so it will not be picked up by `colcon build`
if you cloned this repo into your ROS workspace's `src/`. It is standalone.

## Why this exists

The F1TENTH gym expects Linux and ROS 2. On Apple Silicon this runs it in a lightweight
OrbStack Linux VM instead of Docker, and shows RViz in a browser tab over noVNC, so the
whole loop is one terminal command and one browser window.

## Setup

Needs [OrbStack](https://orbstack.dev). Then:

    brew install orbstack                   # if you do not have it
    orbctl create ubuntu:jammy roboracer    # Ubuntu 22.04 arm64
    ./rr setup                              # ROS 2 Humble + the gym, inside the VM, takes a while
    ln -s "$PWD/rr" /opt/homebrew/bin/rr    # optional, so rr works from anywhere

For the ForzaETH race stack (separate VM, optional):

    orbctl create ubuntu:jammy forzaeth
    rr forza setup

## Common commands

Simulator:

    rr sim <track>        start the sim on a track, e.g. rr sim Comp1
    rr viz                open RViz in the browser (port 6080)
    rr maps               list the competition-style tracks
    rr laps               lap times from the running sim
    rr reset              put the car back on the start line
    rr stop               stop the sim
    rr down               shut the VMs down and free their RAM

Algorithms (they live in `ws/src/racer_algos`):

    rr list               list available algorithms
    rr new <name>         scaffold a new one from the template
    rr run <name>         run one against the sim
    rr param <algo> <name> <value>     change a parameter live

ForzaETH:

    rr forza sim <track>  run the ForzaETH stack on a track
    rr forza speed <x>    scale the target speed, 0.0 to 1.0
    rr forza laps         lap times
    rr forza addmap <t>   generate a raceline for a track, about 6 seconds

Real car (reads `car.env` for the address):

    rr car-key            copy your SSH key to the car, do this once
    rr status             check the car is reachable
    rr car-start          start the drivers, odometry and SLAM on the car
    rr car-check          health check on every topic and transform
    rr car-run <algo>     run one of the algorithms on the car
    rr car-stop           STOP THE CAR
    rr car-map-view       look at the map being built
    rr car-map-save <n>   save the map

Run `rr help` for the full list.

## Tracks

`tracks/` has 55 maps ready to drive:

- `Comp1` to `Comp8`: generated in the style of official RoboRacer tracks, small and
  twisty with few straights, duct walls with lidar-visible gaps, variable width.
- `Real*`: real lidar-mapped tracks imported from other teams.
- `ETH*`, `TUW*`, `Blackbox*`: tracks from the ForzaETH and TU Wien map sets.
- Formula 1 circuits (`Monza`, `Spa`, and so on), scaled down. These are big and open,
  so they are less representative of competition.
- `Squiggle`, `Random*`: simple generated test loops.

Make a new competition-style track with `rr track new <seed>`. The seed is any number,
and the same seed always gives the same track.

## Docs

`docs/` has three PDFs: a handbook with all the commands, a learning guide covering what
ROS is and how to tune, and the Mac setup guide describing how this was installed.
They are built from the scripts in `docs/src`.

## Safety

This car's drive mux has no autonomous lock. Anything published on `/drive` moves the car
immediately, with no button held down. `rr car-stop` is the stop command. Know it before
you run anything.

## State of things

Working and tested:

- both simulators, driving and lap timing
- track generation and import
- ForzaETH raceline generation and live speed tuning
- `follow_the_gap` on the real car

Not working yet:

- SLAM mapping on the real car. `slam_toolbox` drops every scan with
  "Message Filter dropping message: frame 'laser' ... reason 'Unknown'", even though the
  transforms and timestamps check out and an independent node can look up odom to laser
  at the scan timestamp. `rr car-map-save` therefore times out. Under investigation.

Untested, written but not yet run on hardware:

- `rr car-forza-setup` and `rr car-forza`, which install and run ForzaETH on the car
- the wheel plus lidar odometry fusion in `config/car/ekf.yaml`

## Layout

    rr                  the CLI, all commands live here
    car.env             the real car's address and settings
    scripts/            setup and helper scripts, VM side and car side
    config/car/         EKF and DDS config for the car
    config/rviz/        RViz camera presets
    ws/src/racer_algos/ the algorithms
    tracks/             maps
    docs/               PDFs and their build scripts
