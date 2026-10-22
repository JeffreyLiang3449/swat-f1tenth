#!/usr/bin/env bash
# Inside the forzaeth VM: put the car on the map's start line (maps made with rr forza addmap carry
# an initial_pose; ForzaETH's own maps don't and use their fixed spawn point).
source "$(dirname "$0")/forza_env.sh"
y=~/ws/src/race_stack/stack_master/maps/$1/$1.yaml
pose=$(grep initial_pose "$y" 2>/dev/null | sed 's/[^0-9.,-]//g; s/,/ /g')
[ -n "$pose" ] || exit 0
sleep 12
python3 "$(dirname "$0")/auto_reset.py" $pose --once
