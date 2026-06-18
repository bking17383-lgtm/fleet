# CONTROL — live orders to running agents
# Agents check this file at each loop boundary and obey the latest STATUS line.

STATUS: REDIRECT (v3 - 02:25, RE-RUN even if you ran before — jobs changed in bus/orders.txt): Pull the repo, then run  ./scripts/order.sh <your-name>  (e.g. ./scripts/order.sh puppy). Your assigned job may have CHANGED, so re-run. Jobs: scan = read-only list; preserve = copy projects into repo; fix = back up old rules then write the clean brain (puppy). It never deletes or moves project work on your machine. Then resume and wait.

# Set STATUS to one of:
#   CONTINUE          - keep working the current goal
#   STOP              - halt and wait for Brian
#   REDIRECT: <note>  - drop current task, do <note> instead
