# CONTROL — live orders to running agents
# Agents check this file at each loop boundary and obey the latest STATUS line.

STATUS: REDIRECT: Report your CURRENT standing orders and rules. Write them to bus/reports/<your-name>.md (e.g. bus/reports/cb2.md). Include every naming convention, "universal rule", old law (NAMING_LAW, DEAD_WORDS, PROJECT_LAW, etc.), and any instruction you are still operating under -- even stale ones. Then: git add -A && git commit && git push. Then resume normal work.

# Set STATUS to one of:
#   CONTINUE          - keep working the current goal
#   STOP              - halt and wait for Brian
#   REDIRECT: <note>  - drop current task, do <note> instead
