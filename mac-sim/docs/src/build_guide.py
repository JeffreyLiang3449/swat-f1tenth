"""Builds ~/Downloads/RoboRacer_Mac_Setup_Guide.pdf"""
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path.home() / 'Documents/Projects/robotics/roboracer'
OUT = ROOT / 'docs' / 'RoboRacer_Mac_Setup_Guide.pdf'
SCRATCH = Path(__file__).parent

ACCENT = colors.HexColor('#B3261E')
INK = colors.HexColor('#1F2328')
MUTED = colors.HexColor('#57606A')
CODEBG = colors.HexColor('#F3F4F6')
RULE = colors.HexColor('#D0D7DE')

ss = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=ss['Heading1'], fontName='Helvetica-Bold', fontSize=17, leading=21,
                    textColor=ACCENT, spaceBefore=14, spaceAfter=6)
H2 = ParagraphStyle('H2', parent=ss['Heading2'], fontName='Helvetica-Bold', fontSize=12.5, leading=16,
                    textColor=INK, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle('B', parent=ss['BodyText'], fontName='Helvetica', fontSize=10, leading=14,
                      textColor=INK, spaceAfter=5)
SMALL = ParagraphStyle('S', parent=BODY, fontSize=8.5, leading=11, textColor=MUTED)
BUL = ParagraphStyle('BL', parent=BODY, leftIndent=14, bulletIndent=4, spaceAfter=3)
CELL = ParagraphStyle('C', parent=BODY, fontSize=9, leading=12, spaceAfter=0)
CELLC = ParagraphStyle('CC', parent=CELL, fontName='Courier', fontSize=8.5)
CODE = ParagraphStyle('CODE', fontName='Courier', fontSize=8.6, leading=11.2, textColor=INK,
                      backColor=CODEBG, borderPadding=(6, 6, 6, 6), leftIndent=6, rightIndent=6,
                      spaceBefore=4, spaceAfter=10)
TITLE = ParagraphStyle('T', parent=H1, fontSize=26, leading=31, spaceBefore=0, spaceAfter=4)
SUB = ParagraphStyle('SUB', parent=BODY, fontSize=12, leading=16, textColor=MUTED, spaceAfter=14)
M = lambda t: f'<font face="Courier">{t}</font>'

story = []
P = lambda t, s=BODY: story.append(Paragraph(t, s))
C = lambda t: story.append(Preformatted(t.strip('\n'), CODE))


def B(items):
    for it in items:
        story.append(Paragraph(it, BUL, bulletText='•'))


def T(rows, widths, code_col=None):
    data = []
    for r, row in enumerate(rows):
        cells = []
        for c, v in enumerate(row):
            st = CELLC if (code_col is not None and c == code_col and r > 0) else CELL
            cells.append(Paragraph(f'<b>{v}</b>' if r == 0 else v, st))
        data.append(cells)
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('LINEBELOW', (0, 0), (-1, -1), 0.4, RULE),
                           ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                           ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FBEAE9'))]))
    story.append(t)
    story.append(Spacer(1, 8))


# ---------------------------------------------------------------- cover
P('RoboRacer on a Mac', TITLE)
P('How the F1TENTH simulator, ROS 2, the ForzaETH race stack and a one-command terminal tool '
  'were installed on an Apple Silicon MacBook, and how to use them.', SUB)
T([['What', 'Details'],
   ['Machine', 'MacBook, Apple Silicon (arm64), macOS 26, 24 GB RAM'],
   ['Approach', 'Small Ubuntu 22.04 VMs in OrbStack (no Docker), ROS 2 Humble inside'],
   ['Disk used', 'About 8 GB total (4 GB per VM) plus ~150 MB of project files'],
   ['Control', f'One command, {M("rr")}, run from the Mac terminal'],
   ['Viewer', 'RViz shown in a web browser through noVNC (no accounts, no X11 setup)'],
   ['Project folder', M('~/Documents/Projects/robotics/roboracer')],
   ['Set up', 'September 2026']], [1.3 * inch, 5.2 * inch])

P('Why it is built this way', H2)
B(['ROS 2 does not run natively on macOS, so it runs in Linux. The official F1TENTH instructions use Docker; '
   'OrbStack VMs were used instead because they are lighter on a Mac, start in seconds, and see the Mac\'s '
   'files directly, so code is edited on the Mac with any editor.',
   'Two VMs, not one: ForzaETH pins old Python packages (numpy 1.22, scipy 1.7) that break the current '
   'official simulator (which needs scipy 1.13+). Keeping them apart means neither can break the other.',
   'RViz is shown in the browser (noVNC) because it is the one GUI piece, and this avoids XQuartz and '
   'Foxglove accounts entirely.',
   f'Algorithms use the same ROS topics as the real car ({M("/scan")} in, {M("/drive")} out), so code '
   'tested in the sim runs unchanged on the car.',
   'Autoware was skipped on purpose: tens of GB, aimed at x86 with NVIDIA GPUs, and not needed for testing '
   'racing algorithms.'])

P('How the pieces fit', H2)
T([['Layer', 'Runs where', 'What it is'],
   ['rr', 'Mac terminal', 'Bash script; every command in this guide goes through it'],
   ['VM "roboracer"', 'OrbStack', 'Ubuntu 22.04, ROS 2 Humble (ros-base + RViz), f1tenth_gym + '
    'f1tenth_gym_ros (dev-humble branches), your algorithms. RViz at http://localhost:6080'],
   ['VM "forzaeth"', 'OrbStack', 'Clone of the first VM plus ETH Zurich\'s race stack (ros2-humble). '
    'RViz at http://localhost:6081'],
   ['Real car', 'Its own Jetson', 'Keeps its own ROS install. The Mac only connects over SSH']],
  [1.2 * inch, 1.0 * inch, 4.3 * inch])

story.append(PageBreak())
# ---------------------------------------------------------------- install
P('1. Install, step by step', H1)
P(f'Everything below was run from the Mac terminal. The scripts live in the project\'s {M("scripts/")} '
  'folder and are safe to re-run.')

P('Step 1: OrbStack (the VM manager)', H2)
C('''
brew install --cask orbstack
open -a OrbStack                       # finish its first-run setup
orbctl create ubuntu:jammy roboracer   # Ubuntu 22.04, arm64
''')
P('Step 2: Get the official simulator (Humble branches)', H2)
C('''
mkdir -p ~/Documents/Projects/robotics/roboracer/{ws/src,scripts,notes}
cd ~/Documents/Projects/robotics/roboracer
git clone -b dev-humble https://github.com/f1tenth/f1tenth_gym.git
git clone -b dev-humble https://github.com/f1tenth/f1tenth_gym_ros.git ws/src/f1tenth_gym_ros
''')
P(f'The {M("main")} branch of f1tenth_gym_ros targets ROS 2 Foxy; {M("dev-humble")} matches Ubuntu 22.04 '
  'and Humble.', SMALL)

P('Step 3: Provision the VM (scripts/vm_setup.sh)', H2)
P('Run inside the VM (the Mac folder shows up at the same path there):')
C('orb -m roboracer bash ~/Documents/Projects/robotics/roboracer/scripts/vm_setup.sh')
P('What it does, in order:')
B([f'Adds the ROS 2 apt repository and installs {M("ros-humble-ros-base")}, {M("ros-humble-rviz2")}, colcon, '
   'rosdep and keyboard teleop (not the full desktop install, to stay small).',
   f'Installs a virtual display for RViz: {M("tigervnc-standalone-server novnc websockify openbox libgl1-mesa-dri")}.',
   f'Upgrades pip for the user, then installs f1tenth_gym in editable mode with the constraint {M("numpy&lt;2")} '
   '(ROS Humble\'s Python packages are built against numpy 1.x).',
   f'Runs {M("rosdep install")} for the workspace (nav2 map server, foxglove bridge, ackermann messages, ...) '
   f'and {M("colcon build --symlink-install")}.',
   f'Adds one line to the VM\'s ~/.bashrc that sources {M("scripts/env.sh")}.'])

P('Step 4: The rr command', H2)
C('''
chmod +x ~/Documents/Projects/robotics/roboracer/rr
ln -s ~/Documents/Projects/robotics/roboracer/rr /opt/homebrew/bin/rr
rr help
''')
P(f'rr wraps {M("orb -m &lt;vm&gt; bash -c ...")}, keeps the sim, RViz, the crash auto-reset and the VNC '
  'display in tmux sessions inside the VM (so they survive closing the terminal), and opens the browser view.')

P('Step 5: Tracks', H2)
C('''
git clone --depth 1 https://github.com/f1tenth/f1tenth_racetracks.git tracks/src
python3 scripts/make_tracks.py           # 23 real F1 circuits -> tracks/<Name>/
python3 scripts/gen_track.py squiggle    # small practice circuit
python3 scripts/gen_track.py random 7    # random competition-style circuit, seed 7
''')
P('The downloaded track images are white with thin outlines, which lets a car wander off. make_tracks.py '
  'redraws each track from its centerline and widths (track white, everything else black), so every map is '
  'a closed circuit. It also copies the centerline and raceline CSVs next to the map, which turns on lap '
  'counting in the simulator.')

P('Step 6 (optional): ForzaETH, ETH Zurich\'s race stack', H2)
C('''
orbctl stop roboracer && orbctl clone roboracer forzaeth && orbctl start roboracer forzaeth
mkdir -p forzaeth/ws/src && cd forzaeth/ws/src
git clone -b ros2-humble --recurse-submodules https://github.com/ForzaETH/race_stack.git
orb -m forzaeth bash ~/Documents/Projects/robotics/roboracer/scripts/forza_setup.sh
''')
P(f'forza_setup.sh follows their manual-install notes and Dockerfile: removes the first VM\'s Python packages, '
  f'installs {M("linux_req.txt")} and {M("python_req.txt")}, quadprog, their f1tenth_gym fork and the TUM '
  f'race-line optimizer, links the workspace to {M("~/ws")} (their launch files expect it) and builds all 28 '
  f'packages. It uses the Zenoh middleware ({M("RMW_IMPLEMENTATION=rmw_zenoh_cpp")}) like they do.')

story.append(PageBreak())
# ---------------------------------------------------------------- gotchas
P('2. Problems we hit, and the fixes', H1)
P('Useful if you set this up yourself. Every fix is already built into the scripts.', SMALL)
T([['Symptom', 'Cause', 'Fix'],
   ['pip error: "uv-build was not properly installed"', 'Ubuntu 22.04 ships pip 22, too old for '
    'f1tenth_gym\'s packaging', 'Upgrade pip for the user first, then install'],
   ['"AMENT_TRACE_SETUP_FILES: unbound variable"', f'ROS setup.bash breaks under bash {M("set -u")}',
    f'Wrap it: {M("set +u; source ...; set -u")}'],
   ['Browser stuck at "Connecting..."', f'A check like {M("pgrep -f websockify")} matched its own command '
    'line, so the bridge was never started', f'Run display services in a tmux session; use the {M("[w]ebsockify")} '
    'pattern trick'],
   ['Page will not load at roboracer.orb.local', 'That name did not resolve on this Mac',
    'Use http://localhost:6080 (OrbStack forwards VM ports)'],
   ['Map choice ignored, car drives out of the building', f'macOS sed has no {M("\\\\s")}, so the map line '
    'was never replaced', f'Use {M("[[:space:]]")}'],
   ['Car drives through walls after a crash', 'The gym only reports collisions, it does not stop the car',
    f'{M("scripts/auto_reset.py")} watches {M("/ego_racecar/collision")} and puts the car back on the start line'],
   ['Gym refuses a map yaml', 'Its loader rejects extra keys like initial_pose',
    f'Separate {M("forza.yaml")} with initial_pose for ForzaETH'],
   ['ForzaETH breaks the official gym', 'Conflicting numpy/scipy pins', 'Separate VM'],
   ['ForzaETH build: f110_gym and stack_master fail', 'Gym is pip-only; setup.py globs a folder as a file',
    'COLCON_IGNORE in the gym; filter the globs to files'],
   ['ForzaETH planner: "No module named global_racetrajectory_optimization"',
    f'Needs {M("gb_opt_setup.sh")} from their post-install', 'pip install -e the optimizer'],
   ['Mac slows down', 'ForzaETH\'s race-line optimizer on a big (450 m) track pegs the CPU for 10+ minutes',
    'Only run it on small tracks, when the Mac is idle']],
  [1.75 * inch, 2.35 * inch, 2.4 * inch])

# ---------------------------------------------------------------- daily use
P('3. Daily use', H1)
T([['Command', 'What it does'],
   ['rr sim [track]', 'Start the sim and RViz (default Squiggle). Opens http://localhost:6080'],
   ['rr run follow_the_gap', 'Let an algorithm drive. Ctrl-C stops it and stops the car'],
   ['rr ps', 'What is running: sim, which algorithm, ROS nodes'],
   ['rr reset / rr crashes', 'Car back to the start line (crashes do this automatically) / crash count'],
   ['rr view follow|chase|top|orbit', 'Camera: above the car / behind it / whole track / free 3D'],
   ['rr teleop', 'Drive with the keyboard (i forward, j and l turn, k stop)'],
   ['rr maps', 'List every map'],
   ['rr track new [seed]', 'Generate a random competition-style track'],
   ['rr new my_idea', 'New algorithm from the template'],
   ['rr param &lt;algo&gt; &lt;name&gt; &lt;value&gt;', 'Tune a running algorithm live'],
   ['rr stop', 'Stop the sim'],
   ['rr down', 'Stop the VMs (otherwise they keep running in the background until restart)'],
   ['rr forza sim / race / h2h', 'ForzaETH sim, time trials on its race line, head-to-head racing'],
   ['rr shell, rr logs, rr topics, rr ros ...', 'Linux shell, sim logs (tmux), any ros2 command']],
  [2.3 * inch, 4.2 * inch], code_col=0)
P('In RViz (browser): scroll to zoom, drag to rotate or pan, shift+drag to pan. <b>2D Pose Estimate</b> then '
  'click-drag puts the car somewhere new. The <b>Views</b> panel on the right changes the camera by hand.')

P('Tracks', H2)
imgs = []
for n in ['Squiggle', 'Random1', 'Random2', 'Random4']:
    im = PILImage.open(ROOT / 'tracks' / n / f'{n}.png')
    im.thumbnail((360, 360))
    tmp = SCRATCH / f'thumb_{n}.png'
    im.save(tmp)
    w, h = im.size
    s = 1.45 * inch / max(w, h)
    imgs.append((Image(str(tmp), w * s, h * s), Paragraph(n, SMALL)))
story.append(Table([[i[0] for i in imgs], [i[1] for i in imgs]], colWidths=[1.62 * inch] * 4,
                   style=[('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
story.append(Spacer(1, 6))
B(['<b>Squiggle</b>: hand-designed 89 m practice loop with a start straight, an S-bend, a 1.0 m hairpin dip '
   'and a chicane. The default map.',
   '<b>Random&lt;seed&gt;</b>: generated like procedural racing-game tracks (random points, their outline, '
   'edges pushed in and out for hairpins and S-bends, smoothed with a spline), and kept only if it passes '
   'F1TENTH-style rules: closed, never crosses itself, walls of neighbouring stretches at least 0.6 m apart, '
   'every corner radius at least 1.2 m (the car can turn about 0.75 m), width 1.3 to 1.9 m, lap 35 to 80 m. '
   'Same seed gives the same track.',
   '<b>23 real F1 circuits</b> (Monza, Spa, Silverstone, ...) from f1tenth_racetracks, scaled for F1TENTH, '
   '250 to 550 m laps. Good for top speed, less for tight handling.'])

story.append(PageBreak())
# ---------------------------------------------------------------- algorithms
P('4. Writing and testing algorithms', H1)
P(f'Each file in {M("ws/src/racer_algos/racer_algos/")} with a {M("main()")} is an algorithm. Shared plumbing '
  f'lives in {M("_base.py")}: it subscribes to the lidar and odometry, calls your {M("on_scan()")}, clamps '
  'steering to the car\'s 0.419 rad limit and a max speed, and stops the car on Ctrl-C.')
C('''
from racer_algos._base import RacerNode, spin, deg

class Algo(RacerNode):
    def __init__(self):
        super().__init__('my_idea', speed=1.0, gain=1.0)   # each keyword = live parameter

    def on_scan(self, ranges, angles, scan):
        # numpy arrays; angle 0 = straight ahead, + = left. self.odom = latest odometry
        left, right = self.range_at(ranges, angles, deg(90)), self.range_at(ranges, angles, deg(-90))
        return self.p('speed'), self.p('gain') * (left - right) * 0.1   # (m/s, rad)

def main():
    spin(Algo)
''')
P('Included: <b>follow_the_gap</b> (reactive: bubbles out the closest obstacle and aims into the widest free '
  'gap) and <b>wall_follow</b> (PID on the distance to the left wall).')

# ---------------------------------------------------------------- real car
P('5. Moving to the real car', H1)
P('Not done yet. The car keeps its own ROS; the Mac only connects over SSH.', SMALL)
P('One-time setup', H2)
B([f'Get from the car\'s current driver: its Wi-Fi IP ({M("hostname -I")} on the car), the password for user '
   f'{M("swat-roboracer-2026")}, its ROS version ({M("ls /opt/ros")}), and its workspace folder (usually ~/f1tenth_ws).',
   f'Put the IP in {M("car.env")} ({M("CAR_HOST")}). Mac and car on the same Wi-Fi; {M("rr status")} should say reachable.',
   f'{M("rr car-key")} once (copies an SSH key, so no more passwords), then {M("rr car")} to check you get a shell.'])
P('Each session', H2)
B(['Battery charged. <b>Wheels off the ground</b> (car on a box) for the first run of any new algorithm.',
   f'Terminal 1: {M("rr car-bringup")} (lidar, motor controller, joystick). Leave it running.',
   f'Terminal 2: {M("rr car-push")} (copies and builds your algorithms on the car).',
   f'Terminal 2: {M("rr car-run follow_the_gap -p max_speed:=1.0")}.',
   'The stock F1TENTH stack only obeys the algorithm while you <b>hold the joystick\'s autonomous button</b> '
   '(usually RB). Let go and the car stops. Ctrl-C also stops it.',
   'Once it behaves on the box, run it on the floor in open space and raise max_speed gradually.'])
P('ForzaETH on the real car is a bigger project (their Docker on the car, mapping your track, tuning a steering '
  'table for your car). Get your own algorithms working on the car first.')

P('6. Removing everything', H1)
C('''
rr down
orbctl delete forzaeth roboracer
brew uninstall --cask orbstack
rm /opt/homebrew/bin/rr
rm -rf ~/Documents/Projects/robotics/roboracer
''')

P('Sources', H2)
T([['Project', 'Link', 'Version used'],
   ['f1tenth_gym_ros', 'github.com/f1tenth/f1tenth_gym_ros', 'dev-humble @ 0839576'],
   ['f1tenth_gym', 'github.com/f1tenth/f1tenth_gym', 'dev-humble @ bdaec14'],
   ['f1tenth_racetracks', 'github.com/f1tenth/f1tenth_racetracks', 'master'],
   ['ForzaETH race_stack', 'github.com/ForzaETH/race_stack', 'ros2-humble @ 3f8eb3f'],
   ['OrbStack', 'orbstack.dev', '2.2.3'],
   ['ROS 2 Humble', 'docs.ros.org/en/humble', 'apt, Ubuntu 22.04 arm64']],
  [1.5 * inch, 2.9 * inch, 2.1 * inch])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.75 * inch, 0.5 * inch, 'RoboRacer on a Mac: setup guide')
    canvas.drawRightString(7.75 * inch, 0.5 * inch, f'Page {doc.page}')
    canvas.restoreState()


SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                  topMargin=0.7 * inch, bottomMargin=0.8 * inch, title='RoboRacer on a Mac',
                  author='Ben').build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
