# Sourced inside the VM by every `rr` command and by interactive shells.
RR_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/humble/setup.bash
[ -f "$RR_ROOT/ws/install/setup.bash" ] && source "$RR_ROOT/ws/install/setup.bash"
export PATH="$HOME/.local/bin:$PATH"
export DISPLAY=:1
