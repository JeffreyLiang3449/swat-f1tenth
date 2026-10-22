#!/usr/bin/env bash
# Provision the "forzaeth" VM (a clone of "roboracer") for the ETH Zurich ForzaETH race stack.
# It gets its own VM because ForzaETH pins numpy 1.22 / scipy 1.7, which would break the
# official f1tenth_gym in the roboracer VM. Follows race_stack/.install_utils/README.md
# "manually install dependencies" + the .devcontainer/Dockerfile. Run from the Mac: rr forza setup
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FWS="$ROOT/forzaeth/ws"
RS="$FWS/src/race_stack"
export DEBIAN_FRONTEND=noninteractive

echo "==> drop the roboracer VM's python packages (conflicting versions)"
rm -rf ~/.local/lib/python3.10 ~/.local/bin
sed -i '/# roboracer-env/,+2d' ~/.bashrc

echo "==> ForzaETH apt deps (linux_req.txt)"
sudo apt-get update -q
xargs sudo apt-get install -y -q < "$RS/.install_utils/linux_req/linux_req.txt"

echo "==> ForzaETH python deps (python_req.txt), same as their Dockerfile"
python3 -m pip install -q --user --upgrade 'pip<24'
PIP="$HOME/.local/bin/pip3"
"$PIP" install -q --user -r "$RS/.install_utils/python_req.txt"
"$PIP" install -q --user 'quadprog~=0.1.11'
"$PIP" install -q --user -e "$RS/base_system/f110_simulator/f1tenth_gym/"
# TUM raceline optimizer used by their global planner (their .install_utils/gb_opt_setup.sh)
"$PIP" install -q --user -e "$RS/planner/global_planner/global_planner/global_racetrajectory_optimization/"

echo "==> workspace at ~/ws (their launch files expect it), stored in the Mac folder"
[ -L ~/ws ] || ln -s "$FWS" ~/ws
set +u; source /opt/ros/humble/setup.bash; set -u
cd ~/ws
rosdep install -i -y -q --from-paths src --rosdistro humble || true
# Local fixes: gym is pip-installed above, and stack_master/setup.py globs a folder (NUC5/pacejka/dubi) as a file.
touch "$RS/base_system/f110_simulator/f1tenth_gym/COLCON_IGNORE"
sed -i -E "s/glob\(os\.path\.join\('config', '(NUC[0-9])', '\*\/\*'\), recursive=True\)/[f for f in glob(os.path.join('config', '\1', '*\/*'), recursive=True) if os.path.isfile(f)]/" "$RS/stack_master/setup.py"
colcon build --symlink-install

echo "==> shell setup"
grep -q forzaeth-env ~/.bashrc || printf '# forzaeth-env\nsource "%s/scripts/forza_env.sh"\ncd ~/ws\n' "$ROOT" >> ~/.bashrc
echo "==> done"
