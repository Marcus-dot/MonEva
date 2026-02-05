# MVP: Contractor Monitoring & Evaluation System
**Project:** Contractor M&E — Roads, Hospitals, Schools, CSR

## Purpose
Provide a minimum viable product (MVP) that enables organisations to monitor contractor performance across infrastructure and CSR activities, verify compliance, collect evidence, manage finances & payments, capture stakeholder feedback, and produce management-grade reports and dashboards.

## 1. Objectives (MVP scope)
- Enable field data capture (inspections, photos, geo-tags, forms) for contractor progress and quality.
- Track contract milestones, variations, and payment verification against physical progress.
- Provide dashboards and exception-based alerts for project managers and executives.
- Collect, triage and manage community feedback and grievances.
- Maintain basic financial tracking & value-for-money checks (payments vs progress).
- Support evidence-based sign-offs (engineer sign-off, photo + GPS + timestamp) and document storage.
- Provide role-based web portal (Admin / PM / Inspector / Finance / Community Officer) and an offline-capable mobile app for site teams.

## 2. User personas
- **Project Manager (PM):** Monitor multiple projects, approvals, dashboards, decisions.
- **Engineer / Inspector (Field):** Perform site inspections, fill forms, upload photos/GPS/evidence, offline mode.
- **Finance Officer:** Validate contractor invoices and payment certificates against progress claims.
- **Contract Administrator:** Manage contract milestones, variations, claims, sanctions.
- **Community Liaison / Grievance Officer:** Collect and manage community feedback and complaints.
- **Executive / Board Member:** High-level KPIs and periodic reports.
- **Contractor Representative:** View contract schedule, submit progress claims and evidence (optional MVP).

## 3. Core modules (MVP)

### 3.1 Projects & Contracts Module
- Create/manage projects (type: road/hospital/school/CSR).
- Register contracts (contractor, contract value, start/end, milestones, deliverables).
- Link EIAs, tender documents, drawings, Bill of Quantities (BoQ).
- Milestone schedule (Gantt-like data) with % completion target per milestone.

### 3.2 Field Inspections & Evidence
- Customizable inspection forms (templates for roads/hospitals/schools/CSR).
- **Offline-capable mobile app to capture:**
    - Form fields (structured answers)
    - Photos with EXIF & GPS auto-capture
    - Video (optional)
    - Digital signature (engineer)
    - Pre-populated checklists
- Geo-tagged photos and map view of inspection points.
- Attachments & versioning for evidence.

### 3.3 Progress & Quality Monitoring
- Link inspection reports to contract milestones.
- Auto-calc physical completion % per milestone.
- Quality scoring per inspection (pass/fail + comments).
- Non-conformance report (NCR) workflow: raise, assign contractor remedial action, verify closure.

### 3.4 Finance & Payments
- Record contractor claims and attach supporting evidence.
- Payment recommendation workflow (Inspector -> PM -> Finance).
- Simple cost-progress reconciliation (spent vs physical % complete).
- Variation order logging (reason, cost, approval status).

### 3.5 Risk, Safeguards & Compliance
- Register H&S incidents and EHS checklists.
- Track EIA mitigation actions & compliance items.
- Risk register with mitigation actions and owners.

### 3.6 Stakeholder Feedback & Grievances
- Public-facing intake (SMS/USSD/web form) or in-person registration.
- Case management (open/acknowledged/investigating/resolved) and SLA tracking.
- Maps of complaint hotspots and feedback trends.

### 3.7 Dashboards & Reporting
- **Executive dashboard:** portfolio-level summary (RAG status, cost vs progress, top risks).
- **Project dashboard:** milestones, upcoming approvals, inspection summary, finances.
- **Custom reports exportable to PDF/Excel:** monthly progress, payment certificates, audit packs.

### 3.8 Admin & Governance
- User and role management (RBAC).
- Audit logs (user actions, document uploads, sign-offs).
- System settings (indicator config, form templates, notification preferences).

## 4. Data model (High-level entities)
- Users
- Organisations (owner, contractor)
- Projects
- Contracts
- Milestones
- Inspections
- InspectionTemplates
- Evidence (photo/video/docs)
- PaymentClaims
- Payments
- Variations
- Risks
- Incidents
- Grievances
- Notifications
- AuditLog

**Key relationships:**
- Project -> Contract -> Milestones
- Milestone -> Inspections -> Evidence
- PaymentClaim -> Milestone(s) & Evidence
- Grievance -> Project

## 5. Minimal database schema (selected tables)
### projects
`id`, `name`, `type`, `description`, `location` (lat/lng center), `start_date`, `end_date`, `status`, `owner_org_id`

### contracts
`id`, `project_id`, `contractor_id`, `contract_value`, `currency`, `start_date`, `end_date`, `status`

### milestones
`id`, `contract_id`, `title`, `description`, `due_date`, `target_percent`, `status`

### inspections
`id`, `milestone_id`, `inspector_id`, `date`, `form_data` (json), `geo_point`, `quality_score`, `status`

### evidence
`id`, `inspection_id`, `uploader_id`, `file_path`, `file_type`, `exif` (json), `gps_lat`, `gps_lng`, `timestamp`

### payment_claims
`id`, `contract_id`, `claimant_id`, `amount_claimed`, `amount_approved`, `status`, `linked_milestones` (json)

### grievances
`id`, `project_id`, `reporter_contact`, `type`, `description`, `status`, `assigned_to`, `resolution_date`

## 6. APIs (Representative endpoints)
### Auth
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`

### Projects & Contracts
- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `GET /api/v1/projects/{id}`
- `GET /api/v1/contracts/{id}`
- `POST /api/v1/contracts`

### Inspections & Evidence
- `POST /api/v1/inspections` (accepts multipart for evidence)
- `GET /api/v1/inspections?project_id=&milestone_id=`
- `GET /api/v1/evidence/{id}`

### Payments
- `POST /api/v1/payment_claims`
- `POST /api/v1/payment_claims/{id}/approve`

### Grievances
- `POST /api/v1/grievances`
- `GET /api/v1/grievances/{id}`

### Dashboards
- `GET /api/v1/dashboard/portfolio`
- `GET /api/v1/dashboard/project/{id}`

### Admin
- `GET /api/v1/users`
- `POST /api/v1/users`

## 7. Workflows (user journeys)
### 7.1 Inspector site inspection (mobile)
1. Inspector opens mobile app (offline cache of templates & project list).
2. Select project -> milestone -> start inspection.
3. Fill structured form, take geo-tagged photos, record notes, sign.
4. Submit: if offline, store locally and sync when online.
5. Server creates inspection record, triggers notifications to PM and Contract Admin.

### 7.2 Contractor payment claim validation
1. Contractor (or admin) uploads claim with supporting evidence.
2. Inspector reviews attached evidence and links to milestone(s), adds inspection verification.
3. PM reviews and recommends payment; Finance validates budget & issues payment (or holds).
4. Payment record created; dashboard RAG updates accordingly.

### 7.3 Grievance intake
1. Complaint received via web form, SMS, or entry by community officer.
2. Case created and assigned; reporter receives acknowledgement.
3. Investigation assigned (field inspection may be initiated).
4. Resolution recorded and reporter notified; case closed with metadata for reporting.

## 8. KPIs & Indicators (MVP set)
**Output / Activity:**
- % Milestones completed on time
- Number of inspections performed (period)
- % Inspections passing quality checks

**Financial:**
- % Payment claims validated vs approved
- Cost variance (actual vs contracted)

**Safeguards / Risk:**
- Number of H&S incidents
- % EIA mitigations completed

**Stakeholder / Impact:**
- Number of grievances received and average resolution time
- Beneficiary satisfaction (survey score)

## 9. UI (screens & brief wireframes)
**Web Admin Portal**
- Login
- Portfolio Dashboard (cards: Projects, Contracts, Payments, Grievances, Risks)
- Project Detail: timeline, milestone list, inspections feed, payments
- Inspections Viewer: gallery with map pins, filter by date / inspector / milestone
- Payments: claims queue, supporting evidence, approve/reject
- Grievances: case list with SLA, assignment, notes
- Settings: templates, roles, indicator config

**Mobile App (Inspector)**
- Login / Project list
- Offline-synced templates & forms
- Start Inspection -> form -> add photos (GPS auto) -> sign -> submit
- View assigned NCRs & remedial actions

## 10. Notifications & Alerts
- Threshold-based alerts: lagging milestones, cost overrun > X%, overdue variations.
- Email & in-app notifications.
- SMS integration for critical alerts and grievance acknowledgements (optional integration).

## 11. Integrations (MVP + optional)
- GIS / Map tile provider (OpenStreetMap) for plotting inspections and project extents.
- SMS gateway (Twilio or local provider) for reports & user notifications.
- Financial system (optional): export payments to accounting.
- Document storage (S3-compatible) for evidence.

## 12. Security & Compliance
- RBAC (Admin, PM, Inspector, Finance, Community Officer, Contractor)
- TLS for all transport; secure signed URL for evidence access
- Audit log for all approvals and record edits
- Data retention policy and export capability for audits
- GDPR-like privacy controls for personal data in grievances

## 13. Minimum Acceptance Criteria for MVP
- Field users can create and sync inspections with geo-tagged photos and sign-off.
- PMs can view project dashboards and milestone progress.
- Finance can receive and approve/reject payment claims linked to evidence.
- Grievances can be logged, assigned, tracked, and closed.
- System produces a management progress report (PDF/Excel) per project.

## 14. Non-functional requirements (MVP)
- Basic offline-first mobile support for inspections.
- Scalable storage for photos (S3-compatible).
- Responsive web UI.
- Auditable trails for all sign-offs.

## 15. Prioritised backlog (MVP -> Next)
**Must-have (MVP):**
- User auth & RBAC
- Projects / Contracts / Milestones CRUD
- Mobile inspections with photo GPS & offline sync
- Evidence storage
- Payment claim workflow
- Dashboard (portfolio + project)
- Grievance intake & case management
- Reporting export (PDF / Excel)

**Should-have (post-MVP):**
- Contract performance scoring & contractor profiles
- Automated physical % calculation per BoQ
- SMS intake & alerting
- Advanced map analytics (heatmaps)

**Nice-to-have (later):**
- Machine-assisted image QA (detect missing rebar, cracks) — ML module
- USSD intake for remote communities
- Integration with procurement and accounting systems
- Public-facing portal for project transparency

## 16. Implementation architecture (recommended)
**Frontend**
- Web: React or Next.js (Admin portal)
- Mobile: Flutter (single codebase iOS & Android) — offline-first with local DB (SQLite)

**Backend**
- Django and Django REST Framework (Python)
- PostgreSQL (PostGIS extension if heavy geo queries required)
- Object storage: S3-compatible (MinIO / AWS S3)
- Authentication: JWT + refresh tokens

**Hosting**
- Containerised (Docker) and deployed to cloud (AWS/GCP/Azure) or self-hosted VM

**Observability**
- Basic logging (centralized), health checks, backup strategy for DB + storage

## 17. Data governance & Audit
- All inspections and payments must be signed and recorded with timestamp + uploader ID.
- Versioning for edited records where applicable.
- Exportable audit pack per project (inspections, evidence, payments, grievances).

## 18. Example user stories (Granular)
- **As an Inspector**, I want to start an inspection offline, attach geo-tagged photos and sync when online so that I can capture site evidence in remote areas.
    - *Acceptance:* form saved locally, photos stored encrypted, sync succeeds and evidence available in admin portal.
- **As a PM**, I want to see projects with RAG status so I can immediately identify which projects need attention.
    - *Acceptance:* dashboard shows red/amber/green based on rule config.
- **As Finance**, I want to approve a payment claim only after inspection sign-off so that payments are evidence-backed.
    - *Acceptance:* payment claim cannot be approved unless inspector verification exists.
- **As a Community Officer**, I want to record a grievance from a phone call and assign it for investigation with an SLA so the reporter knows progress.
    - *Acceptance:* grievance case created, acknowledgement sent, SLA countdown visible.

## 19. QA & Testing (MVP)
- Unit tests for core APIs
- Integration tests for inspection upload and sync
- Manual UAT with 3 pilot projects (1 road, 1 hospital, 1 school/CSR)
- Field test in low-connectivity scenario

## 20. Launch / Pilot recommendations
- Pilot with 1–3 small projects covering each project type.
- Run pilot with: PMs, 2–3 field inspectors, 1 finance officer, 1 contractor contact, 1 community officer.
- Collect feedback and iterate backlog.

## 21. Next deliverables
- Detailed ERD and normalized DB schema
- OpenAPI spec for backend endpoints
- Clickable UI mockups for Admin and Mobile flows (Figma-ready)
- Sprint-ready backlog with 1–3 week sprint breakdown
- Procurement-ready technical specification for tendering development

*Prepared as an actionable, granular MVP blueprint — ready for conversion into backlog items, wireframes, and development sprints.*
