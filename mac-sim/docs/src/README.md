# Rebuilding the PDFs

    python3 -m venv /tmp/pdfenv && /tmp/pdfenv/bin/pip install reportlab pypdfium2
    /tmp/pdfenv/bin/python build_handbook.py      # RoboRacer_Handbook.pdf      (daily use)
    /tmp/pdfenv/bin/python build_learning.py      # RoboRacer_Learning_Guide.pdf (ROS, tuning, real car)
    /tmp/pdfenv/bin/python build_guide.py         # RoboRacer_Mac_Setup_Guide.pdf (how it was installed)

Each script writes straight into ../ (this docs folder). Edit the script, not the PDF.
