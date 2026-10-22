#!/usr/bin/env bash
# Inside a VM: make openbox open every window maximized and borderless, so RViz fills the browser tab.
mkdir -p ~/.config/openbox
grep -q 'rr-maximize' ~/.config/openbox/rc.xml 2>/dev/null || sed 's#</applications>#<application class="*"><!-- rr-maximize --><maximized>yes</maximized><decor>no</decor></application></applications>#' /etc/xdg/openbox/rc.xml > ~/.config/openbox/rc.xml
