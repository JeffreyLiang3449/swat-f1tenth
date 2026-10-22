#!/usr/bin/env bash
# Inside the forzaeth VM: set the whole lap's speed (every sector's scaling + the global cap) live.
# Usage: forza_speed.sh <0-1>
source "$(dirname "$0")/forza_env.sh"
v="$1"
ros2 param set /sector_tuner global_limit "$v" > /dev/null
n=$(ros2 param get /sector_tuner n_sectors | grep -o '[0-9]*$')
for i in $(seq 0 $((n - 1))); do
  ros2 param set /sector_tuner "Sector$i.scaling" "$v" > /dev/null
done
echo "all $n sector(s) now at $v of the race line's speed"
