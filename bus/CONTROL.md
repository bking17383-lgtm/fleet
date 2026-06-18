# CONTROL — live orders to running agents
# Agents check this file at each loop boundary and obey the latest STATUS line.

STATUS: REDIRECT: Pull the repo, then run  ./scripts/order.sh <your-name>  (e.g. ./scripts/order.sh puppy). It does ONLY the job assigned to your machine in bus/orders.txt (scan = read-only list, preserve = copy projects into repo). It never deletes or moves anything on your machine. Then resume and wait.

# Set STATUS to one of:
#   CONTINUE          - keep working the current goal
#   STOP              - halt and wait for Brian
#   REDIRECT: <note>  - drop current task, do <note> instead
