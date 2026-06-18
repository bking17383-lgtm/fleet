# CONTROL — live orders to running agents
# Agents check this file at each loop boundary and obey the latest STATUS line.

STATUS: REDIRECT: READ-ONLY. Pull the repo, then run  ./scripts/projects.sh <your-name>  (e.g. ./scripts/projects.sh puppy). It lists every project and website on you and pushes bus/reports/<your-name>-projects.md. Do NOT copy, move, or delete anything. Then resume.

# Set STATUS to one of:
#   CONTINUE          - keep working the current goal
#   STOP              - halt and wait for Brian
#   REDIRECT: <note>  - drop current task, do <note> instead
