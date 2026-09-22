# JANE RIVER — kids mail test PARTIAL · by=forge — 2026-08-15T14:23:00Z

by: forge
kid: independent checker ran ./scripts/kids-fetch-mail.py
exit: 1
verdict: PARTIAL

## speak
Kids can fetch. Jane river mail works. Gmail door is open (imap 993) but this box has no app password, so inbox stayed empty. Do not paste the password in chat.

## proof
- git_river: PASS
- gmail_reach: PASS imap.gmail.com:993
- gmail_inbox: FAIL-NO-CREDS
- report: bus/jane/river/mail-last.txt
