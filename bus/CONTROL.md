# CONTROL — live orders to running agents
# Agents check this file at each loop boundary and obey the latest STATUS line.

STATUS: REDIRECT (v2 - 01:33, RE-RUN even if you ran before): Pull the repo, then run  ./scripts/order.sh <your-name>  (e.g. ./scripts/order.sh cb2). The scan tool was UPDATED to also open your GoogleDrive folder, so re-running will find new projects. It does ONLY your assigned job in bus/orders.txt (scan = read-only list incl. GoogleDrive, preserve = copy projects into repo). It never deletes or moves anything on your machine. Then resume and wait.

# Set STATUS to one of:
#   CONTINUE          - keep working the current goal
#   STOP              - halt and wait for Brian
#   REDIRECT: <note>  - drop current task, do <note> instead
