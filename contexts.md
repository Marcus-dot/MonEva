# MonEva: Comprehensive System Context

## 1. Project Mission & Strategic Core
**MonEva (Contractor Monitoring & Evaluation)** is a unified platform for tracking infrastructure and CSR projects. It bridges the gap between field activity and financial oversight using a "Verification-Led Disbursement" model.

### Strategic Alignment
All projects are aligned with:
- **Strategic Themes**: Education, Health, WASH, Agriculture, Environment, Energy.
- **Key Result Areas (KRAs)**: Socio-Economic Development, Corporate Brand Reputation, Financial Sustainability, Operational Excellence.

---

## 2. Technical Architecture
### Full Stack Specification
- **Frontend**: Next.js 15+ (App Router), React 19, TypeScript.
    - **UI**: Tailwind CSS, Lucide Icons, Recharts (Analytics).
    - **State/Data**: SWR (Stale-While-Revalidate) for intelligent caching and auto-refresh.
- **Backend**: Django 4.2+, Django REST Framework.
    - **Auth**: SimpleJWT (Access/Refresh tokens) + RBAC (Role-Based Access Control).
    - **Worker**: Django-Q (planned for scheduled reports).
- **Database**: PostgreSQL with UUID primary keys for all entities.
- **Maps**: Leaflet.js with custom logical clustering (Chiefdom -> Project).

---

## 3. The "MonEva Engine": Project lifecycle
### Project Registry (`projects`)
- **Project**: Core entity managing metadata, thematic alignment, and GeoJSON coordinates (Lat/Lng).
- **Contract**: Financial envelope for a project. Links a `Project` to an `Organization` (Contractor/Partner).
- **Milestone**: The unit of progress.
    - **Target %**: Physical completion required.
    - **Value Amount**: Financial value released upon completion.
    - **Weight Validation**: System enforces that the sum of milestone weights must equal 100% for a contract.

### Finance & Payments (`finance`)
- **Maker-Checker Workflow**:
    1. **Maker (PM/Contractor)**: Submits a `PaymentClaim` linked to completed milestones.
    2. **checker (Finance/Admin)**: Verifies evidence and approves/rejects.
- **Auditability**: Tracks `prepared_by` and `approved_by` to prevent collusion.
- **Risk Scoring**: Claims are assigned a `risk_score` (0-100) based on timing, evidence proximity, and history.

---

## 4. Impact & Evaluation
### Indicator Engine (`indicators`)
- **Indicators**: Measurable KPIs (e.g., "Meters of Road Paved"). Supports directions (Increasing/Decreasing is Good).
- **Logical Framework (`LogFrameNode`)**: A tree structure (Goal -> Outcome -> Output -> Activity) defining how a project achieves impact.
- **Framework Templates**: Pre-defined Logframes (e.g., "Road Works Standard") that can be cloned into new projects.

### Field Assessments (`assessments`)
- **Inspection**: Field-level pass/fail checks conducted by Inspectors.
- **Evidence**: Geo-tagged photos/videos linked to inspections, milestones, or investigations.
- **Post-Project Evaluation**: Long-term impact follow-ups after construction is finished.

---

## 5. Accountability & Feedback Loop
### Grievance & Investigation (`grievances`, `investigations`)
- **Grievance**: Public/Stakeholder feedback. Can be "Open", "Investigating", or "Resolved".
- **Investigation**: Deep-dive investigations (Fraud, Quality, Environment).
    - **InvestigationUpdate**: Timeline of events/notes.
    - **InvestigationMilestone**: Actionable steps to resolve the case.
    - **Sync Logic**: Investigation status changes trigger automated notifications to stakeholders.

---

## 6. Security & RBAC (`core`)
- **Core Entities**: `User`, `Role`, `Permission`.
- **RBAC Logic**: Permissions (e.g., `projects.create_project`) are assigned to Roles (e.g., `Project Manager`).
- **Standard Roles**:
    - **ADMIN**: Full system override and User management.
    - **PM (Project Manager)**: Project creation, Claim submission.
    - **FINANCE**: Claim approval, Budget oversight.
    - **INSPECTOR**: Field data collection, Evidence capture.

---

## 7. Developer & DevOps Context
### Environmental Config
- `NEXT_PUBLIC_API_URL`: Points to backend V1 API.
- `NEXT_PUBLIC_OPENWEATHER_API_KEY`: For localized weather overlays on the GIS map.

### Testing Strategy
- **E2E**: Playwright suite in `web/tests/e2e`.
    - `gis_map.spec.ts`: Map responsiveness.
    - `grievance_investigation.spec.ts`: Resolution flow validation.
    - `sustainability.spec.ts`: Post-project tracking.

### Critical Utilities
- `backend/system_verification.py`: Full system health check (DB, Auth, API).
- `web/src/lib/api.ts`: Centralized fetcher with JWT injection and error toasting.
