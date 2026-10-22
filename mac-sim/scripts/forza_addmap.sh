#!/usr/bin/env bash
# Inside the forzaeth VM: turn one of our tracks into a ForzaETH map (race line + speed sectors).
# Usage: forza_addmap.sh <track>      (called by `rr forza addmap <track>`)
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/forza_env.sh"
t="$1"; src="$ROOT/tracks/$t"; M=~/ws/src/race_stack/stack_master/maps/$t
img="$src/${t}_clean.png"; [ -f "$img" ] || img="$src/$t.png"

mkdir -p "$M"
cp "$img" "$M/$t.png"
cp "$src/forza.yaml" "$M/$t.yaml"
rm -f "$M/global_waypoints.json"

# Their planner writes global_waypoints.json and then waits forever for a ROS message,
# so run it in the background and stop it as soon as the file appears.
cd ~/ws
MPLBACKEND=Agg RMW_IMPLEMENTATION=rmw_fastrtps_cpp nice -n 15 \
  ros2 run global_planner global_planner --ros-args -r __node:=global_planner \
  --params-file src/race_stack/stack_master/config/global_planner/global_planner_params.yaml \
  -p map_name:="$t" > /tmp/planner_$t.log 2>&1 &
pid=$!
for _ in $(seq 1 300); do
  [ -s "$M/global_waypoints.json" ] && sleep 2 && break
  kill -0 $pid 2>/dev/null || break
  sleep 1
done
pkill -f "[g]lobal_planner.*map_name:=$t" || true
if [ ! -s "$M/global_waypoints.json" ]; then
  echo "planner failed, last lines of /tmp/planner_$t.log:"; tail -5 /tmp/planner_$t.log; exit 1
fi
grep -o 'IQP estimated lap time[^;]*; IQP maximum speed[^;]*' "$M/global_waypoints.json" | head -1
python3 "$ROOT/scripts/forza_sectors.py" "$M"
colcon build --packages-select stack_master > /dev/null
echo "ready"
