# CONTROL — live orders to running agents
# Agents check this file at each loop boundary and obey the latest STATUS line.

STATUS: CONTINUE

# Set STATUS to one of:
#   CONTINUE          - keep working the current goal
#   STOP              - halt and wait for Brian
#   REDIRECT: <note>  - drop current task, do <note> instead
