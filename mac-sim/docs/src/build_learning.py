"""Builds roboracer/docs/RoboRacer_Learning_Guide.pdf: ROS, ForzaETH tuning, and getting to the real car."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (Flowable, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path.home() / 'Documents/Projects/robotics/roboracer'
OUT = ROOT / 'docs' / 'RoboRacer_Learning_Guide.pdf'
W = 7.0 * inch

RED = colors.HexColor('#B3261E'); RED_LIGHT = colors.HexColor('#FBEAE9')
INK = colors.HexColor('#1F2328'); MUTED = colors.HexColor('#5B636B'); RULE = colors.HexColor('#E3E6EA')
CODEBG = colors.HexColor('#F4F5F7'); ZEBRA = colors.HexColor('#FAFAFB')
TIP_BG = colors.HexColor('#EAF4EC'); TIP_BAR = colors.HexColor('#2E7D32')
WARN_BG = colors.HexColor('#FFF4E0'); WARN_BAR = colors.HexColor('#C77700')
IDEA_BG = colors.HexColor('#EEF2FB'); IDEA_BAR = colors.HexColor('#3558A8')

S = lambda name, **kw: ParagraphStyle(name, **kw)
BODY = S('body', fontName='Helvetica', fontSize=10, leading=14.2, textColor=INK, spaceAfter=6)
SMALL = S('small', parent=BODY, fontSize=8.5, leading=11.5, textColor=MUTED, spaceAfter=4)
LEDE = S('lede', parent=BODY, fontSize=11, leading=15.5, textColor=MUTED, spaceAfter=12)
H2 = S('h2', fontName='Helvetica-Bold', fontSize=12.5, leading=16, textColor=INK, spaceBefore=12, spaceAfter=5,
       keepWithNext=1)
CELL = S('cell', parent=BODY, fontSize=9.2, leading=12.2, spaceAfter=0)
CMD = S('cmd', parent=CELL, fontName='Courier-Bold', fontSize=8.9)
CODE = S('code', fontName='Courier', fontSize=8.8, leading=11.6, textColor=INK)
BUL = S('bul', parent=BODY, leftIndent=14, bulletIndent=3, spaceAfter=3)
M = lambda t: f'<font face="Courier">{t}</font>'

story = []
P = lambda t, s=BODY: story.append(Paragraph(t, s))


class Band(Flowable):
    def __init__(self, num, title):
        super().__init__(); self.num, self.title = num, title

    def wrap(self, aw, ah):
        self.aw = aw; return aw, 40

    def draw(self):
        c = self.canv
        c.setFillColor(RED); c.roundRect(0, 6, 30, 30, 6, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont('Helvetica-Bold', 15); c.drawCentredString(15, 15.5, str(self.num))
        c.setFillColor(INK); c.setFont('Helvetica-Bold', 19); c.drawString(42, 13, self.title)
        c.setStrokeColor(RULE); c.setLineWidth(1); c.line(0, 0, self.aw, 0)


def chapter(num, title, lede=None):
    story.append(PageBreak()); story.append(Band(num, title)); story.append(Spacer(1, 8))
    if lede:
        P(lede, LEDE)


def code(text):
    t = Table([[Preformatted(text.strip('\n'), CODE)]], colWidths=[W])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), CODEBG), ('LEFTPADDING', (0, 0), (-1, -1), 10),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 7),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]))
    head = [story.pop()] if story and isinstance(story[-1], Paragraph) and story[-1].style is H2 else []
    story.append(KeepTogether(head + [t, Spacer(1, 8)]))


def callout(kind, text):
    bg, bar, label = {'tip': (TIP_BG, TIP_BAR, 'TIP'), 'warn': (WARN_BG, WARN_BAR, 'HEADS UP'),
                      'idea': (IDEA_BG, IDEA_BAR, 'THE IDEA')}[kind]
    p = Paragraph(f'<font color="{bar.hexval()}"><b>{label}</b></font>&nbsp;&nbsp;{text}',
                  S('co', parent=BODY, fontSize=9.4, leading=13, spaceAfter=0))
    t = Table([['', p]], colWidths=[4, W - 4])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), bar), ('BACKGROUND', (1, 0), (1, 0), bg),
                           ('LEFTPADDING', (1, 0), (1, 0), 10), ('RIGHTPADDING', (1, 0), (1, 0), 10),
                           ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                           ('LEFTPADDING', (0, 0), (0, 0), 0), ('RIGHTPADDING', (0, 0), (0, 0), 0)]))
    story.append(KeepTogether([t, Spacer(1, 10)]))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, BUL, bulletText='•'))
    story.append(Spacer(1, 4))


def table(rows, widths, code_col=None):
    data = [[Paragraph(f'<b>{v}</b>' if r == 0 else v,
                       CMD if (code_col is not None and c == code_col and r > 0) else CELL)
             for c, v in enumerate(row)] for r, row in enumerate(rows)]
    t = Table(data, colWidths=[w * inch for w in widths], repeatRows=1)
    st = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 4.5),
          ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5), ('LINEBELOW', (0, 0), (-1, -1), 0.4, RULE),
          ('BACKGROUND', (0, 0), (-1, 0), RED_LIGHT)]
    st += [('BACKGROUND', (0, i), (-1, i), ZEBRA) for i in range(2, len(data), 2)]
    t.setStyle(TableStyle(st))
    head = [story.pop()] if story and isinstance(story[-1], Paragraph) and story[-1].style is H2 else []
    story.append(KeepTogether(head + [t, Spacer(1, 10)]) if len(data) < 16 else t)
    if len(data) >= 16:
        story.append(Spacer(1, 10))


def steps(items):
    data = [[Paragraph(f'<font color="{RED.hexval()}"><b>{i}</b></font>', S('n', parent=BODY, fontSize=12)),
             Paragraph(t, S('st', parent=BODY, spaceAfter=0))] for i, t in enumerate(items, 1)]
    t = Table(data, colWidths=[0.35 * inch, W - 0.35 * inch])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 3),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 5), ('LEFTPADDING', (0, 0), (0, -1), 2)]))
    story.append(t); story.append(Spacer(1, 6))


class Flow(Flowable):
    """Boxes-and-arrows row: a pipeline diagram."""
    def __init__(self, boxes, caption=None):
        super().__init__(); self.boxes, self.caption = boxes, caption

    def wrap(self, aw, ah):
        self.aw = aw; return aw, 70 if self.caption else 56

    def draw(self):
        c = self.canv; n = len(self.boxes); gap = 16
        bw = (self.aw - gap * (n - 1)) / n; y = 14 if self.caption else 4; bh = 42
        for i, (title, sub) in enumerate(self.boxes):
            x = i * (bw + gap)
            c.setFillColor(RED_LIGHT if i % 2 == 0 else colors.HexColor('#F3F4F6'))
            c.setStrokeColor(RED if i % 2 == 0 else MUTED); c.setLineWidth(0.8)
            c.roundRect(x, y, bw, bh, 6, fill=1, stroke=1)
            c.setFillColor(INK); c.setFont('Helvetica-Bold', 8.6); c.drawCentredString(x + bw / 2, y + 26, title)
            c.setFillColor(MUTED); c.setFont('Courier', 7.6); c.drawCentredString(x + bw / 2, y + 12, sub)
            if i < n - 1:
                ax = x + bw + 2; ay = y + bh / 2
                c.setStrokeColor(INK); c.setLineWidth(1); c.line(ax, ay, ax + gap - 5, ay)
                c.setFillColor(INK); p = c.beginPath(); p.moveTo(ax + gap - 4, ay); p.lineTo(ax + gap - 9, ay + 3)
                p.lineTo(ax + gap - 9, ay - 3); p.close(); c.drawPath(p, fill=1, stroke=0)
        if self.caption:
            c.setFillColor(MUTED); c.setFont('Helvetica-Oblique', 8); c.drawString(0, 0, self.caption)


# ======================================================== cover
class Cover(Flowable):
    def wrap(self, aw, ah):
        return aw, 3.1 * inch

    def draw(self):
        c = self.canv
        c.setFillColor(INK); c.roundRect(0, 0, W, 3.0 * inch, 10, fill=1, stroke=0)
        c.setFillColor(RED); c.rect(0, 0, 10, 3.0 * inch, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#F28B82')); c.setFont('Helvetica-Bold', 11)
        c.drawString(30, 3.0 * inch - 40, 'LEARNING GUIDE')
        c.setFillColor(colors.white); c.setFont('Helvetica-Bold', 36)
        c.drawString(30, 3.0 * inch - 92, 'From sim to real car')
        c.setFont('Helvetica', 13)
        c.drawString(30, 3.0 * inch - 120, 'What ROS is, how ForzaETH works, how to tune it yourself,')
        c.drawString(30, 3.0 * inch - 138, 'and how to push it onto your RoboRacer.')
        c.setFont('Helvetica', 10); c.setFillColor(colors.HexColor('#C9CED4'))
        c.drawString(30, 24, 'Companion to the RoboRacer Handbook  ·  September 2026')


story.append(Cover()); story.append(Spacer(1, 20))
P('The plan in one picture', S('pp', parent=H2, spaceBefore=0))
story.append(Flow([('1. Learn ROS', 'rr ros ...'), ('2. Tune in sim', 'rr forza ...'),
                   ('3. Save settings', 'yaml files'), ('4. Car setup', 'your car config'),
                   ('5. Push + drive', 'git pull, build')],
                  'Each chapter of this guide is one box. Do them in order; each one makes the next easier.'))
story.append(Spacer(1, 12))
toc = [('1', 'ROS in plain words', 'nodes, topics, parameters, launch files, builds'),
       ('2', 'How ForzaETH drives', 'the pipeline from map to motor'),
       ('3', 'Tuning ForzaETH in the sim', 'the knobs, what they do, how to know what to change'),
       ('4', 'A test plan', 'which maps, which speeds, in what order'),
       ('5', 'Saving your settings', 'which files, so tuning survives a restart'),
       ('6', 'Pushing to the real car', 'what "push" means and the steps to ForzaETH on your car'),
       ('7', 'Cheat sheet', 'every command from this guide')]
t = Table([[Paragraph(f'<font color="{RED.hexval()}"><b>{n}</b></font>', CELL), Paragraph(f'<b>{a}</b>', CELL),
            Paragraph(b, S('tm', parent=CELL, textColor=MUTED))] for n, a, b in toc],
          colWidths=[0.4 * inch, 2.4 * inch, 4.2 * inch])
t.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 0.4, RULE), ('TOPPADDING', (0, 0), (-1, -1), 5),
                       ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
story.append(t); story.append(Spacer(1, 12))
callout('tip', 'Try every command in this guide yourself while reading. Nothing here can break anything: '
               'the worst case is rr forza stop, then start again.')

# ======================================================== 1 ROS
chapter(1, 'ROS in plain words',
        'ROS (Robot Operating System) is not an operating system. It is a way to split a robot\'s software into '
        'small programs that talk to each other. Your car, the simulator and ForzaETH all use ROS 2 (version "Humble").')
callout('idea', 'Every piece of the robot is a separate program. They never call each other directly; they '
                'publish and subscribe to named streams of data. Swap one program for another that uses the same '
                'streams and nothing else notices. That is why the sim and the real car can run the same code.')
P('The five words you need', H2)
table([['Word', 'What it is', 'On your car'],
       ['Node', 'One running program with one job.', 'lidar driver, motor driver, your algorithm, ForzaETH\'s controller'],
       ['Topic', 'A named stream of messages. Anyone can publish, anyone can listen.', f'{M("/scan")} (lidar), {M("/drive")} (speed + steering), {M("/odom")} (where the car thinks it is)'],
       ['Message', 'The data format on a topic.', f'{M("/scan")} carries a LaserScan: about 1080 distances, 40 times a second'],
       ['Parameter', 'A setting inside a node you can read or change while it runs.', f'{M("m_l1")} on the controller, {M("global_limit")} on the sector tuner'],
       ['Launch file', 'A recipe that starts many nodes at once with their settings.', f'{M("time_trials_launch.xml")} starts the controller, state machine, planner...']],
      [1.0, 2.8, 3.2])
P('How the car\'s programs talk', H2)
story.append(Flow([('Lidar node', '-> /scan'), ('ForzaETH / your algo', '/scan -> /drive'),
                   ('Mux (safety)', 'joystick gate'), ('VESC node', '/drive -> motor')],
                  'The mux only lets /drive through while you hold the joystick\'s autonomous button. Let go = stop.'))
story.append(Spacer(1, 6))
P('Look around yourself (start rr sim first; these are read-only and safe)', H2)
table([['Command', 'What you will see'],
       ['rr ros node list', 'Every running program (node).'],
       ['rr topics', 'Every data stream (topic).'],
       ['rr echo /drive', 'The speed and steering commands, live. Ctrl-C to stop.'],
       ['rr ros topic hz /scan', 'How many lidar scans per second arrive.'],
       ['rr ros topic info /drive', 'Who publishes and who subscribes to a topic.'],
       ['rr forza params controller', 'Every setting of ForzaETH\'s controller (with rr forza sim running).']],
      [2.6, 4.4], code_col=0)
P('Workspaces and building', H2)
bullets([f'Code lives in a <b>workspace</b>: a folder with {M("src/")} (your code) and, after building, '
         f'{M("build/")} and {M("install/")}.',
         f'{M("colcon build")} compiles every <b>package</b> in {M("src/")} into {M("install/")}. A package is one folder '
         f'with a {M("package.xml")} (ForzaETH has 28).',
         f'{M("source install/setup.bash")} tells your terminal where the built packages are. rr does this for you.',
         'Settings files (yaml) are linked, not copied, so editing them needs a restart but no rebuild. '
         'Adding new files needs a rebuild.'])

# ======================================================== 2 ForzaETH
chapter(2, 'How ForzaETH drives',
        'ForzaETH is ETH Zurich\'s full race stack. Unlike follow_the_gap, it plans the whole lap in advance and '
        'then follows that plan precisely.')
story.append(Flow([('Map', 'png + yaml'), ('Global planner', 'race line'), ('Sector tuner', 'x scaling'),
                   ('Controller', 'MAP / PP'), ('Car', '/drive')],
                  'Offline (once per track): map and planner. Live (every 25 ms): sector tuner, controller, car.'))
story.append(Spacer(1, 8))
table([['Piece', 'What it does', 'Where you see it'],
       ['Global planner', 'Reads the track image, finds the centerline, then computes the fastest line (the '
        '"minimum curvature" line) and a speed for every point, based on how hard the car can corner and brake.',
        f'{M("rr forza addmap")} runs it. Red and yellow dots in RViz.'],
       ['Sector tuner', 'Multiplies the planned speeds by a factor per sector (piece of the lap). This is your '
        'main speed knob.', f'{M("rr forza speed")}, {M("rr forza sector")}'],
       ['State machine', 'Decides the mode: follow the race line, trail a slower car, or overtake.',
        'rr forza logs, window "drive"'],
       ['Controller (MAP)', 'Looks a distance ahead on the race line and steers toward that point. The distance '
        'grows with speed.', 'Settings m_l1, q_l1, t_clip_min, t_clip_max'],
       ['Lap analyser', 'Times every lap.', f'{M("rr forza laps")}']], [1.25, 3.85, 1.9])
callout('tip', 'The race line assumes perfect grip. Running near 1.0 (100%) can work in the sim; on the real car, '
               'start at 0.3 and earn your way up.')

# ======================================================== 3 tuning
chapter(3, 'Tuning ForzaETH in the sim',
        'Tuning is a loop: measure, change one thing, measure again, write it down.')
steps([f'Start: {M("rr forza sim Comp1")}, then {M("rr forza race")}. Open the browser view.',
       f'Measure: watch 3 to 5 laps and run {M("rr forza laps")}. Note the lap time and anything bad '
       '(wall touches, wobbling, cutting corners). You do not need more laps than that per setting.',
       'Change <b>one</b> setting with the commands below.',
       'Measure again. Better? Keep it. Worse? Put it back.',
       'Write it down (the log in chapter 4). When happy, save it to the files in chapter 5.'])
P('The knobs, in the order to learn them', H2)
table([['Knob', 'Command', 'What it does', 'Start at'],
       ['Overall speed', 'rr forza speed 0.6', 'Fraction of the race line\'s speed for the whole lap.', '0.5 (sim), 0.3 (car)'],
       ['One sector', 'rr forza sector 1 0.4', 'Slow down or speed up just one part of the lap (needs sectors, chapter 5).', 'same as overall'],
       ['Lookahead gain', 'rr forza param controller m_l1 0.35', 'How much further ahead it aims per m/s of speed. Bigger = smoother but cuts corners.', '0.3'],
       ['Lookahead base', 'rr forza param controller q_l1 0.2', 'Aim distance at zero speed. Bigger = calmer at low speed.', '0.15'],
       ['Lookahead limits', 'rr forza param controller t_clip_min 0.8', 'Never aim closer than min or further than max (meters).', '1 and 5'],
       ['Steer anticipation', 'rr forza param controller speed_lookahead_for_steer 0.1', 'Steers a little earlier to make up for delay. Faster laps, more corner cutting. Max 0.2.', '0']],
      [1.25, 2.35, 2.45, 0.95], code_col=1)
P('The controller aims at a point this far ahead: <b>distance = q_l1 + speed x m_l1</b>, kept between '
  't_clip_min and t_clip_max. Almost every steering problem is this distance being too short or too long.', SMALL)
P('How to know what to change', H2)
table([['You see', 'Why', 'Try'],
       ['Clean laps, nothing scary', 'You have margin.', 'rr forza speed +0.05, repeat.'],
       ['Touches the wall in one specific corner', 'That corner is too fast for the line.', 'Split that corner into its own sector and lower only it.'],
       ['Swings side to side (wobble) on straights', 'Aiming too close: over-correcting.', 'Raise m_l1 or q_l1 a little.'],
       ['Cuts the inside of corners, clips inner wall', 'Aiming too far ahead.', 'Lower m_l1, or lower speed_lookahead_for_steer.'],
       ['Runs wide at corner exit', 'Too fast in the corner.', 'Lower that sector, or lower overall speed.'],
       ['Slow but perfectly smooth', 'Leaving time on the table.', 'Speed up the straight sectors only.'],
       ['Lap times jump around a lot', 'The car is near its limit somewhere.', 'Back off 0.05 and find the worst corner.'],
       ['Crashes right after the start', 'Start pose or wrong map.', 'rr forza stop, check the map name, start again.']],
      [2.1, 2.1, 2.8])
callout('warn', 'Change one thing at a time. If you change speed and lookahead together and it gets worse, '
                'you will not know which one did it.')

# ======================================================== 4 test plan
chapter(4, 'A test plan', 'Go from easy to hard. Move on once the current stage is clean for 5 laps in a row.')
table([['Stage', 'Maps', 'Goal', 'Speeds to try'],
       ['A. Known good', 'glc_ot_ez (ETH\'s real track)', 'Learn the commands; see what clean laps look like.', '0.5, 0.6, 0.7, 0.8'],
       ['B. Short and tight', 'Comp6 (27 m), Comp4 (28 m), Comp8 (31 m), Comp1 (34 m)', 'Hairpins and choke points: learn lookahead tuning.', '0.5 up to the first touch, then back 0.05'],
       ['C. Longer, faster', 'Comp7 (40 m), Comp5 (45 m), Comp3 (46 m); race lines hit 9-11 m/s', 'High speed into tight corners: learn sector tuning.', '0.5 up; add sectors for the hard corners'],
       ['D. New tracks', 'rr track new, then rr forza addmap CompN', 'Does your tuning work on a track it has never seen?', 'Start from your best settings'],
       ['E. Racing', 'glc_ot_ez, rr forza h2h', 'Trailing and overtaking.', 'Your best time-trial settings']],
      [1.1, 2.2, 2.3, 1.4])
P('Keep a log', H2)
P('A simple table is enough. Keep it in a notes file, for example roboracer/notes/tuning.md:')
code('''
map    speed  m_l1  q_l1  lookahead_steer  best lap  touches  notes
Comp1  0.50   0.30  0.15  0.0              7.21      0        baseline
Comp1  0.70   0.30  0.15  0.0              5.20      0        clean
Comp1  0.80   0.30  0.15  0.0              ?         ?        ...
''')
P('The first two rows are real: that is what the setup check measured on Comp1.', SMALL)
P('Making a new track for ForzaETH', H2)
code('''
rr track new 42            # makes Comp42, a competition-style track
rr forza addmap Comp42     # computes its race line (a few seconds)
rr forza sim Comp42        # then: rr forza race
''')

# ======================================================== 5 saving
chapter(5, 'Saving your settings',
        'Live changes (rr forza speed, rr forza param) disappear when the sim restarts. To keep them, write them into '
        'the files ForzaETH reads at start-up.')
P(f'All paths below are inside {M("~/Documents/Projects/robotics/roboracer/forzaeth/ws/src/race_stack/stack_master/")}. '
  'Edit them on your Mac with any text editor, then restart the sim (no rebuild needed).')
table([['What', 'File', 'Keys'],
       ['Speed per track', 'maps/&lt;map&gt;/speed_scaling.yaml', 'global_limit, n_sectors, Sector0.scaling ...'],
       ['Controller (sim)', 'config/SIM/l1_params.yaml', 'm_l1, q_l1, t_clip_min, t_clip_max, speed_lookahead_for_steer'],
       ['Controller (your car)', 'config/&lt;YOURCAR&gt;/l1_params.yaml', 'same keys, tuned separately for the real car'],
       ['Overtaking zones', 'maps/&lt;map&gt;/ot_sectors.yaml', 'Overtaking_sectorN.ot_flag: true where passing is allowed'],
       ['Race line safety margin', 'config/global_planner/global_planner_params.yaml', 'safety_width (m): bigger keeps the line further from walls; then rr forza addmap again']],
      [1.5, 2.8, 2.7])
P('Splitting a lap into sectors', H2)
P('The race line is a list of numbered points (waypoints), about 200 on a Comp track. A sector is a range of '
  'them. In RViz the sector markers show where each sector starts. Example: three sectors on Comp1 '
  '(waypoints 0 to 181), slowing only a hairpin in the middle:')
code('''
sector_tuner:
  ros__parameters:
    global_limit: 0.8
    n_sectors: 3
    Sector0: {start: 0,   end: 70,  scaling: 0.8,  only_FTG: false, no_FTG: false}
    Sector1: {start: 71,  end: 110, scaling: 0.55, only_FTG: false, no_FTG: false}  # hairpin
    Sector2: {start: 111, end: 181, scaling: 0.8,  only_FTG: false, no_FTG: false}
''')
P(f'Sectors must cover every waypoint with no gaps, and global_limit caps every sector. After editing, restart the '
  f'sim; then {M("rr forza sector 1 0.5")} tunes that sector live.', SMALL)

# ======================================================== 6 real car
chapter(6, 'Pushing to the real car',
        '"Pushing" means three things: copy the code and settings onto the car, build them there, then launch them. '
        'The car is just a small Linux computer.')
story.append(Flow([('Your Mac', 'edit + tune'), ('git / rsync', 'copy over'), ('Car: colcon build', 'compile'),
                   ('Car: ros2 launch', 'drive')]))
story.append(Spacer(1, 8))
P('Route 1: your own algorithms (ready now)', H2)
P(f'rr already does this. {M("rr car-push")} copies racer_algos with rsync and builds it on the car; '
  f'{M("rr car-run follow_the_gap")} launches it. The car just needs its IP in car.env. Do this first: it proves '
  'the Wi-Fi link, SSH, building on the car and the joystick safety gate all work, with simple code.')
P('Before either route: this car needs laser odometry', H2)
P('Checked on the car 2026-09-22: the VESC connects and reports firmware 6.2, but publishes no '
  'sensor data with the driver installed. So there is no wheel odometry, no odom to base_link transform, '
  'and SLAM drops every lidar scan (mapping produces nothing). Two of the three causes are fixed; this one '
  'is not, and it does not affect plain driving, which needs only the lidar.')
bullets([f'{M("rr car-odom-setup")} once: installs rf2o, which works out the car\'s motion by comparing lidar '
         'scans, plus the fusion that blends it with the VESC IMU (the IMU works; only the wheel packets are '
         'missing). It does not touch the VESC or its firmware.',
         f'{M("rr car-odom")} before mapping, left running in its own tab. It publishes /odometry/filtered '
         'and the odom to base_link transform that SLAM needs.',
         f'{M("rr car-check")} tells you in one screen which piece is missing if mapping stays empty.',
         'The other option, not taken because Ben does not want to touch the VESC: update the car\'s vesc_driver '
         'to a version that understands firmware 6.x, or put the VESC back on 5.x.'])
P('Route 2: ForzaETH on the car (the real goal)', H2)
P('ForzaETH has to live on the car, because the car drives even when your Mac is not connected. The steps:')
steps(['<b>Find out what is on the car.</b> SSH in (rr car) and check: computer type (Jetson: '
       f'{M("cat /etc/nv_tegra_release")}), Ubuntu version ({M("lsb_release -a")}), ROS version ({M("ls /opt/ros")}), '
       'and the lidar model. ForzaETH\'s ROS 2 version needs ROS 2 Humble (Ubuntu 22.04), or its Docker image '
       '(they have a "jet" target for Jetsons).',
       f'<b>Get the code there.</b> Best: make your own copy (fork) of ForzaETH/race_stack on GitHub, commit your '
       f'tuned yaml files to it from the Mac, and {M("git clone")} / {M("git pull")} it on the car. Then every '
       f'"push" is {M("git push")} on the Mac and {M("git pull")} on the car.',
       '<b>Install and build on the car</b>, following their install guide (Docker "jet" target on a Jetson, or '
       'the manual steps). Same idea as your Mac: dependencies, rosdep, colcon build.',
       f'<b>Make your car\'s config.</b> Copy {M("config/NUC2")} to {M("config/YOURCAR")}. In {M("vesc.yaml")} set '
       f'{M("speed_to_erpm_gain")} (motor speed per m/s) and {M("steering_angle_to_servo_offset")} (the value where '
       'the wheels point straight). Measure these on your car: wrong values mean it drives at the wrong speed or '
       f'pulls to one side. In {M("config/sensors.yaml")} set your lidar\'s IP or serial port.',
       f'<b>Map your track.</b> {M("ros2 launch stack_master mapping_launch.xml map_name:=mytrack racecar_version:=YOURCAR")}. '
       'Drive one slow lap with the joystick; it builds the map and computes the race line, like rr forza addmap does in the sim.',
       f'<b>Start the base system</b>: {M("ros2 launch stack_master base_system_launch.xml map_name:=mytrack sim:=false racecar_version:=YOURCAR")}.',
       f'<b>Time trials, slowly</b>: {M("ros2 launch stack_master time_trials_launch.xml racecar_version:=YOURCAR LU_table:=NUC2_hangar_pacejka ctrl_algo:=MAP")}, '
       'with global_limit 0.3 and a hand on the joystick. The steering lookup table (LU_table) describes how your '
       'tires grip; borrow ETH\'s at first, and later measure your own with their system identification tools.',
       'Tune exactly like in the sim, starting slow. Save settings to config/YOURCAR and maps/mytrack, commit, push.'])
callout('warn', 'On the real car: wheels off the ground for the first run of anything new, global_limit 0.3 to '
                'start, a hand on the joystick, and nobody on the track.')
P('What to ask your friend before starting', H2)
bullets(['The car\'s IP on the Wi-Fi, and the password for swat-roboracer-2026.',
         'Which computer it has (Jetson model?) and which Ubuntu and ROS version.',
         'Which lidar (Hokuyo UST-10LX, UST-30LX, other?) and how it connects (Ethernet IP or USB).',
         'Whether the VESC (motor controller) settings are already calibrated, and where they are saved.',
         'Which joystick button enables autonomous driving.'])

# ======================================================== 7 cheat sheet
chapter(7, 'Cheat sheet', 'Everything in this guide, in one place.')
table([['Command', 'What it does'],
       ['rr forza sim [map]', 'Start the ForzaETH sim (browser: http://localhost:6081).'],
       ['rr forza race', 'Time trials on the race line (MAP controller). rr forza race PP = pure pursuit.'],
       ['rr forza h2h', 'Head-to-head racing with overtaking.'],
       ['rr forza laps', 'Lap times so far.'],
       ['rr forza speed 0.6', 'Whole-lap speed, as a fraction of the race line\'s speed.'],
       ['rr forza sector 1 0.4', 'Speed for one sector.'],
       ['rr forza param controller m_l1 0.35', 'Change any setting live.'],
       ['rr forza params [node]', 'List a node\'s settings (default: controller).'],
       ['rr forza maps', 'Maps ForzaETH can drive.'],
       ['rr track new [seed]', 'New competition-style track, named Comp&lt;seed&gt;.'],
       ['rr forza addmap Comp42', 'Give a track to ForzaETH (computes its race line).'],
       ['rr forza logs', 'Live logs of every ForzaETH node (Ctrl-b n = next window, Ctrl-b d = leave).'],
       ['rr forza stop', 'Stop the ForzaETH sim.'],
       ['rr ros node list / rr topics / rr echo /drive', 'Look around ROS (in the gym sim).'],
       ['rr car / rr car-push / rr car-run', 'Real car: log in, send your algorithms, run one.'],
       ['rr down', 'Turn everything off when done.']], [2.7, 4.3], code_col=0)


def on_page(canvas, doc):
    if doc.page == 1:
        return
    canvas.saveState(); canvas.setStrokeColor(RULE)
    canvas.line(0.75 * inch, 0.62 * inch, 7.75 * inch, 0.62 * inch)
    canvas.setFont('Helvetica', 8); canvas.setFillColor(MUTED)
    canvas.drawString(0.75 * inch, 0.45 * inch, 'RoboRacer Learning Guide')
    canvas.drawRightString(7.75 * inch, 0.45 * inch, str(doc.page)); canvas.restoreState()


SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                  topMargin=0.7 * inch, bottomMargin=0.85 * inch, title='RoboRacer Learning Guide',
                  author='Ben').build(story, onFirstPage=on_page, onLaterPages=on_page)
print(OUT)
