# CONTROL — live orders to running agents
# Agents check this file at each loop boundary and obey the latest STATUS line.

STATUS: REDIRECT (v4 - 02:28, RE-RUN even if you ran before): Pull the repo, then run  ./scripts/order.sh <your-name>  (e.g. ./scripts/order.sh puppy). The fix script was CORRECTED (rules file now gets its proper header so it actually applies), so re-run. Jobs: scan = read-only list; preserve = copy projects into repo; fix = back up old rules then write the clean brain (puppy). It never deletes or moves project work on your machine. Then resume and wait.

# Set STATUS to one of:
#   CONTINUE          - keep working the current goal
#   STOP              - halt and wait for Brian
#   REDIRECT: <note>  - drop current task, do <note> instead
