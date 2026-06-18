# Tech Business Contacts Registry

This is a dedicated, separate registry for new tech-related business contacts. It is stored in plain-text Markdown format for easy parsing and offline usage by local systems and agents.

---

## Contact Directory

| Company / Project | Contact Name | Role | Email | Phone / Discord / Slack | Services / Infrastructure | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | | |

---

## Schema Format for New Entries (YAML)

*To add a new contact, append a block using the following structure:*

```yaml
- name: ""
  company: ""
  role: ""
  email: ""
  phone_or_handle: ""
  category: "" # e.g., hosting, API, hardware, contractor, client
  systems_access: "" # e.g., none, local, server, specific repo
  notes: ""
```
