# Business & Tech Contacts Registry

This is the designated registry for business and tech-only contacts, kept completely separate from your personal Google Contacts/Gmail list to preserve privacy, secure credential segregation, and ensure compatibility with local command-line agents (like Puppy Linux or Cursor).

## Contacts Table

| Name | Role | Company | Email | Phone | Category |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sarah Burgeson** | Solutions Provider / Network Advisor | My Drive Setup | `sburgeson@myyahoo.com` | `831-383-6582` | Tech / Infrastructure |
| **Michael Jorishie** | Loan Officer | Truss Financial Group | `michael@trussfinancialgroup.com` | `858-266-8306` | Financial / Loan |
| **Savka Yurac** | Associate | proSapient Expert Network | `savkayurac@experts.prosapient.com` | `+12268390957` | Tech / Consultation |
| **Annie Jongebreur** | Customer Operations Analyst | Tegus by AlphaSense | `anniejongebreur@tegus.com` | `+1 872-204-4528` | Tech / Market Research |
| **Paul Tollefson** | Solar Proposal Specialist | Smart Energy Today, Inc. | `pault@smartenergytoday.net` | `360-637-4343 ext 2212` | Business / Energy |
| **Graciela Grader** | Marina Branch Manager | Wescom Financial / Credit Union | `mail@wescom.org` | `1-888-4WESCOM` | Financial / Credit Union |
| **Edwin Rosales** | UCLA Assistant Branch Manager | Wescom Credit Union | `mail@wescom.org` | `1-888-4WESCOM` | Financial / Credit Union |
| **Eric Smith** | Professional Contact | Independent | — | — | Professional |

---

## Contact Cards (Agent-Readable Schema)

```yaml
- name: "Sarah Burgeson"
  title: "Solutions Provider / Network Advisor"
  company: "My Drive Setup / Local Network"
  email: "sburgeson@myyahoo.com"
  phone: "831-383-6582"
  category: "tech"
  notes: "Author of Spectrum + T-Mobile dual SIM/eSIM network redundancy & home server failover plan."

- name: "Michael Jorishie"
  title: "Loan Officer"
  company: "Truss Financial Group / Equity Access Group"
  email: "michael@trussfinancialgroup.com"
  phone: "858-266-8306"
  category: "financial"
  notes: "Contact for mortgage pre-approval, loan document uploads, and soft credit checks."

- name: "Savka Yurac"
  title: "Associate"
  company: "proSapient Expert Network"
  email: "savkayurac@experts.prosapient.com"
  phone: "+12268390957"
  category: "consultation"
  notes: "Consultancy coordinator for paid expert interviews on supply chain / plastic crate pooling."

- name: "Annie Jongebreur"
  title: "Customer Operations Analyst"
  company: "Tegus by AlphaSense"
  email: "anniejongebreur@tegus.com"
  phone: "+1 872-204-4528"
  category: "consultation"
  notes: "Contact regarding compensated market research consultations on procurement topics."

- name: "Paul Tollefson"
  title: "Manager-Solar Proposal Specialist / Sales Support"
  company: "Smart Energy Today, Inc."
  email: "pault@smartenergytoday.net"
  phone: "360-637-4343 ext 2212"
  mobile: "360-915-2009"
  category: "business"
  notes: "Lead for solar proposal systems, shade reports, and sales support infrastructure."

- name: "Graciela Grader"
  title: "Branch Manager I"
  company: "Wescom Financial / Credit Union (Marina Branch)"
  email: "mail@wescom.org"
  phone: "1-888-493-7266"
  category: "financial"
  notes: "Regional credit union manager for electronic direct deposits, card sweeps, and account alerts."

- name: "Edwin Rosales"
  title: "Assistant Branch Manager"
  company: "Wescom Credit Union (UCLA Branch)"
  email: "mail@wescom.org"
  phone: "1-888-493-7266"
  category: "financial"
  notes: "Credit union UCLA branch assistance."

- name: "Eric Smith"
  title: "Professional Contact"
  company: "Independent"
  category: "business"
  notes: "Direct mutual email conversation contact."
```

---

*Note: This contact file is stored in `drop_pile/contacts/TECH_CONTACTS.md` in plain text format so that local Linux command-line tools can read and write entries autonomously without requiring Google Doc editor formatting.*
