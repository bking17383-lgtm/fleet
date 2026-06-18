# CONTROL — live orders to running agents
# Agents check this file at each loop boundary and obey the latest STATUS line.

STATUS: REDIRECT: PRESERVE (copy only, no deletes). Pull the repo, then run  ./scripts/save-projects.sh <your-name>  (e.g. ./scripts/save-projects.sh puppy). It COPIES your real projects into projects/<your-name>/ and pushes. It does NOT delete or move anything on your machine. Then resume and wait.

# Set STATUS to one of:
#   CONTINUE          - keep working the current goal
#   STOP              - halt and wait for Brian
#   REDIRECT: <note>  - drop current task, do <note> instead
