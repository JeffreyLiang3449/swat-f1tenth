#!/usr/bin/env bash
# Runs ON THE CAR: install ForzaETH's race stack in Docker and build a config for this car.
# From the Mac:  rr car-forza-setup
#
# Why Docker: ForzaETH's ROS 2 version needs Humble, the car runs Ubuntu 20.04 + Foxy.
# Their container brings Humble with it and runs with network_mode: host, so the car's own Foxy
# drivers (lidar, VESC) can stay outside the container while the race stack runs inside.
set -euo pipefail

REPO=~/race_stack
CAR_NAME="${1:-SWAT}"            # name of this car's config folder inside the race stack
F1TENTH_CFG=~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/config

say() { echo -e "\n=== $*"; }

say "checks"
command -v docker >/dev/null || { echo "docker not installed"; exit 1; }
docker ps >/dev/null 2>&1 || { echo "cannot use docker without sudo: run 'sudo usermod -aG docker $USER', log out and back in"; exit 1; }
ARCH=$(uname -m)
echo "architecture: $ARCH"
if [ "$ARCH" = "aarch64" ]; then
  echo "NOTE: Jetson. Their compose file still points at a Noetic L4T base image while their Dockerfile"
  echo "      wants dustynv/ros:humble-ros-base-l4t-r36.3.0 (JetPack 6). If the build complains about the"
  echo "      base image, edit docker-compose.yaml service 'jet' -> args -> IMAGE to that humble image."
fi

say "get the code ($REPO)"
if [ -d "$REPO/.git" ]; then
  git -C "$REPO" pull --ff-only || true
else
  git clone -b ros2-humble --recurse-submodules https://github.com/ForzaETH/race_stack.git "$REPO"
fi

say "settings (.env)"
cd "$REPO"
cat > .env <<EOF
ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}
RACECAR_VERSION=$CAR_NAME
HOST_UID=$(id -u)
HOST_GID=$(id -g)
EOF
mkdir -p ../race_stack_cache/humble/build ../race_stack_cache/humble/install ../race_stack_cache/humble/log

say "car config: stack_master/config/$CAR_NAME (copied from NUC2, then given this car's real values)"
CFG="$REPO/stack_master/config/$CAR_NAME"
[ -d "$CFG" ] || cp -r "$REPO/stack_master/config/NUC2" "$CFG"
python3 - "$F1TENTH_CFG" "$CFG" "$REPO/stack_master/config/sensors.yaml" <<'PY'
import re, sys, pathlib
src_dir, dst_dir, sensors_dst = (pathlib.Path(p) for p in sys.argv[1:4])

def grab(path, keys):
    out = {}
    if path.exists():
        text = path.read_text()
        for k in keys:
            m = re.search(rf'^\s*{k}\s*:\s*(\S+)', text, re.M)
            if m:
                out[k] = m.group(1)
    return out

# motor + steering calibration: the car's own numbers beat ETH's defaults
vesc_keys = ['speed_to_erpm_gain', 'speed_to_erpm_offset', 'steering_angle_to_servo_gain',
             'steering_angle_to_servo_offset', 'servo_max', 'servo_min', 'speed_max', 'speed_min']
vals = grab(src_dir / 'vesc.yaml', vesc_keys)
dst = dst_dir / 'vesc.yaml'
text = dst.read_text()
for k, v in vals.items():
    text = re.sub(rf'^(\s*{k}\s*:\s*)\S+', rf'\g<1>{v}', text, flags=re.M)
dst.write_text(text)
print('vesc values taken from the car:', vals if vals else 'NONE FOUND, check by hand')

# lidar: address/port and angle limits
lidar = grab(src_dir / 'sensors.yaml', ['ip_address', 'serial_port', 'angle_min', 'angle_max', 'ip_port'])
if lidar and sensors_dst.exists():
    text = sensors_dst.read_text()
    for k, v in lidar.items():
        text = re.sub(rf'^(\s*{k}\s*:\s*)\S+', rf'\g<1>{v}', text, flags=re.M)
    sensors_dst.write_text(text)
print('lidar values taken from the car:', lidar if lidar else 'NONE FOUND, check by hand')
PY

say "build the container (big download, 10-40 min the first time)"
if [ "$ARCH" = "x86_64" ]; then SERVICE=x86; elif [ "$ARCH" = "aarch64" ]; then SERVICE=jet; else SERVICE=arm; fi
echo "service: $SERVICE"
docker compose build "$SERVICE"

say "done"
cat <<EOF
Next, from your Mac:
  rr car-forza            open a shell inside the race stack container
Inside that shell the ForzaETH commands work, e.g.:
  ros2 launch stack_master mapping_launch.xml map_name:=mytrack racecar_version:=$CAR_NAME
EOF
