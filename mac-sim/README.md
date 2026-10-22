# RoboRacer simulator on a Mac

This gets the F1TENTH simulator running on a Mac so you can write and test
algorithms without the car. Follow the steps in order. Total time is about an
hour, but almost all of it is waiting for downloads.

The simulator needs Linux and ROS 2, which do not run natively on macOS. So it
runs inside a small Linux virtual machine, and RViz (the 3D view) shows up in a
browser tab. You drive the whole thing from one command called `rr`.

## Before you start

You need:

- A Mac with Apple Silicon (M1, M2, M3, M4). This has only been tested there.
  On an Intel Mac the steps should work but nobody has tried it.
- About 15 GB of free disk space.
- Your Mac plugged in. The install is heavy and will drain a battery.

## Step 1: Install OrbStack

OrbStack runs the Linux virtual machine. It is free for personal use.

    brew install orbstack

If you do not have Homebrew, download OrbStack from https://orbstack.dev
instead and drag it to Applications.

Open OrbStack once after installing so it can finish setting itself up.

## Step 2: Install the Python packages the Mac side needs

Only needed for making new tracks, but install it now so nothing surprises you
later.

    pip3 install numpy pillow

## Step 3: Get the code

    git clone -b sim https://github.com/JeffreyLiang3449/swat-f1tenth.git
    cd swat-f1tenth/mac-sim

Everything from here on is run from inside that `mac-sim` folder.

## Step 4: Create the virtual machine

    orbctl create ubuntu:jammy roboracer

This takes about a minute. It makes an empty Ubuntu 22.04 machine named
`roboracer`. Nothing is installed in it yet.

## Step 5: Install ROS 2 and the simulator inside the VM

    ./rr setup

**This is the long step, roughly 30 to 45 minutes.** It installs ROS 2 Humble,
RViz, the F1TENTH gym, and the browser bridge, all inside the VM. Your Mac
itself stays clean.

You will see a lot of scrolling text. That is normal. It is safe to re-run this
command if it fails partway through.

## Step 6: Make `rr` work from anywhere

Optional, but everything below assumes it.

    ln -s "$PWD/rr" /opt/homebrew/bin/rr

Now `rr` works from any folder instead of `./rr`.

## Step 7: Start the simulator

    rr sim Comp1

A browser tab opens with RViz in it, showing a car on a track. If the tab does
not open on its own, run `rr viz` or go to http://localhost:6080

The car will sit still. That is correct, nothing is driving it yet.

## Step 8: Make the car drive

In a second terminal:

    rr run follow_the_gap

The car should start driving itself around the track. If it crashes it gets put
back on the start line automatically.

To see lap times:

    rr laps

To drive it yourself with the keyboard instead:

    rr teleop

## Step 9: Stop when you are done

    rr stop      stops the simulator
    rr down      shuts the VM down and gives your Mac its RAM back

Run `rr down` when you finish for the day. The VM uses memory while it is up.

## Daily use after the first time

You never repeat steps 1 to 6. From then on it is just:

    rr sim Comp1          start
    rr run follow_the_gap  drive
    rr stop                stop
    rr down                shut down

## Writing your own algorithm

    rr list               see what algorithms exist
    rr new my_algo        make a new one from the template
    rr run my_algo        run it

`rr new` creates a file at `ws/src/racer_algos/racer_algos/my_algo.py`. Open it
and edit it. It gives you the lidar scan and expects you to set a speed and a
steering angle. The template has comments explaining what goes where.

Look at `follow_the_gap.py` in that same folder for a complete working example.

After editing, just run `rr run my_algo` again. You do not need to rebuild.

## Picking a track

    rr maps               list all of them

There are 55. The useful ones:

- **`Comp1` through `Comp8`** are built to look like real RoboRacer competition
  tracks: small, twisty, few straights. **Test on these.**
- **`Squiggle`** and `Random1` to `Random5` are simple practice loops.
- **`Real*`**, `ETH*`, `TUW*` are real tracks other teams mapped with a lidar.
- Formula 1 circuits like `Monza` and `Spa` are fun but big and open, so they
  are not representative of competition.

Make a brand new competition-style track:

    rr track new 42

The number is a seed. The same number always gives the same track, so `42` on
your Mac is the same track as `42` on someone else's.

## Changing the camera

    rr view follow        behind the car (default)
    rr view chase         further back
    rr view top           straight down
    rr view orbit         free movement

## If something goes wrong

**The browser tab is blank or will not connect.** Run `rr viz` again. The
display sometimes needs a moment after the sim starts.

**"sim already running".** Run `rr stop` first, then start again.

**The VM will not start.** Open the OrbStack app and check `roboracer` is
listed. `rr up` starts it manually.

**`rr: command not found`.** Step 6 did not work. Use `./rr` from inside the
`mac-sim` folder instead.

**Setup failed partway through.** Just run `rr setup` again. It is safe to
re-run and will skip what is already done.

**Everything is weird and you want to start over.** `orbctl delete roboracer`
then go back to step 4. You lose nothing except the install time.

## Where things are

    rr                  the command, everything runs through this
    ws/src/racer_algos/ your algorithms
    tracks/             the 55 maps
    docs/               three PDFs: handbook, learning guide, setup guide
    scripts/            the setup and helper scripts
    config/rviz/        camera presets

Run `rr help` for the complete command list.

The PDFs in `docs/` go deeper. The Learning Guide explains what ROS actually is
and how to tune things, which is worth reading if this is new to you.

## The rest of this folder

There is more in here than the simulator: scripts for driving the real car over
SSH, lidar and IMU odometry fusion, SLAM mapping, and the ForzaETH race stack.
None of that is needed for the simulator and none of it is covered above. See
the handbook in `docs/` for it.

Status of that other half: driving the real car works, mapping does not yet
(SLAM drops every scan, under investigation), and the ForzaETH-on-car scripts
are written but untested.

## Note for people cloning into a ROS workspace

This folder has a `COLCON_IGNORE` in it, so `colcon build` skips it. It will not
interfere with the `auto` and `pid_msgs` packages in this repo.
