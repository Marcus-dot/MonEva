This is a perfect match. MonEva’s existing architecture (Projects, Inspections, and Maker-Checker Finance) provides the "Execution Engine" required for KGLCDC.However, MonEva is currently optimized for "Hard Infrastructure" (building roads). To support KGLCDC’s "Soft Infrastructure" (CSR, Social Impact), we need to expand the Metadata Layer (what we track) without breaking the Core Logic (how we track it).Here is the technical roadmap to integrate the KGLCDC Strategy into the MonEva system.1. Conceptual Mapping: KGLCDC vs. MonEvaWe do not need to rewrite the system; we just need to "alias" the existing modules to fit the new use case.KGLCDC ConceptMonEva ModuleAdaptation RequiredThematic Area (e.g., WASH)core / projectsAdd a Category or Theme tag to the Project model.Activity (e.g., Drilling Borehole)projects.MilestoneMilestones are no longer just "Wall Built"; they are now "Borehole Drilled."Output/OutcomeindicatorsExpand this module to track specific counts (e.g., "500 people trained") linked to Projects.Monitoringassessments.InspectionThe "Inspection" form becomes an "Activity Report" form.I-CARE Valuesassessments.InspectionAdd a mandatory "Compliance Checklist" to the Inspection model.2. Backend Implementation (Django)A. Expand core or projects for Strategic TaxonomyWe need to inject the 9 Thematic Areas and 6 KRAs into the system so every project has a "Strategic Parent."File: backend/projects/models.py (or create a new strategy app)Pythonclass StrategicTheme(models.TextChoices):
    # The 9 KGLCDC Thematic Areas
    EDUCATION = 'EDU', 'Education & Skills'
    HEALTH = 'HLT', 'Health'
    WASH = 'WASH', 'Water, Sanitation & Hygiene'
    AGRICULTURE = 'AGR', 'Agriculture'
    # ... add others (Environment, Climate, etc.)

class KeyResultArea(models.TextChoices):
    # The 6 KRAs for Board Reporting
    SOCIO_ECONOMIC = 'SOC', 'Socio-Economic Development'
    REPUTATION = 'REP', 'Corporate Brand Reputation'
    FINANCE = 'FIN', 'Financial Sustainability'
    # ... add others

# Update the Existing Project Model
class Project(models.Model):
    # ... existing fields (name, location, contractor) ...
    
    # NEW: Strategic Mapping
    thematic_area = models.CharField(
        max_length=4, 
        choices=StrategicTheme.choices,
        default=StrategicTheme.EDUCATION
    )
    primary_kra = models.CharField(
        max_length=3,
        choices=KeyResultArea.choices,
        default=KeyResultArea.SOCIO_ECONOMIC
    )
B. Enhance indicators for Impact TrackingCurrently, MonEva tracks financial progress. We need it to track numerical impact (The "Output" and "Outcome" from your logic).File: backend/indicators/models.pyPythonclass Indicator(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)  # e.g., "Boreholes Drilled"
    target_value = models.IntegerField()     # e.g., 50
    current_value = models.IntegerField(default=0) # Updated via Mobile
    unit = models.CharField(max_length=50)   # e.g., "Units", "People", "Hectares"
    
    # Link to the Logical Framework levels
    level = models.CharField(choices=[('OUTPUT', 'Output'), ('OUTCOME', 'Outcome')])
C. Modify assessments for I-CARE ComplianceThe inspection is where "Accountability" happens. We add the I-CARE validation here.File: backend/assessments/models.pyPythonclass Inspection(models.Model):
    # ... existing fields (milestone, inspector, verdict) ...

    # NEW: I-CARE Compliance Check
    # JSONField allows flexible checklists without migrating DB every time
    icare_compliance = models.JSONField(default=dict) 
    # Structure: {"community_consulted": true, "env_impact_checked": true}
3. Frontend Implementation (Next.js)A. The "Impact Dashboard" (web/src/app/dashboard/strategy/)We need a new dashboard view specifically for ZESCO/KGL leadership that aggregates data by KRA instead of by Contract.Visuals:Theme Card: "Agriculture" -> Shows total budget spent vs. "Farmers Trained" (pulled from indicators).KRA Gauge: A radial chart showing the "Socio-Economic Index" (Aggregate % completion of all projects).Filters: Add a dropdown to filter by Chiefdom (Naluama vs. Nkomeshya).B. Project Creation FlowUpdate the Add Project form (web/src/app/dashboard/projects/new) to include the Thematic Area dropdown. This ensures data is categorized correctly from Day 1.4. Mobile Implementation (Flutter)This is the most critical part for the field officers in Naluama/Nkomeshya.A. The "Activity Report" ScreenModify the existing InspectionScreen (mobile/lib/ui/screens/inspection_screen.dart).Logic Switch: If the Project is a "Road," show the engineering checklist. If it is "Agriculture" or "WASH," show the Indicator Input Form.Input Fields:"Number of units completed today?" (Updates Indicator.current_value)"Evidence Photo" (Uploads to Evidence model)"Community Feedback Rating" (1-5 Stars)B. Offline CapabilitySince these Chiefdoms are remote, the Hive/Isar implementation mentioned in your context is now a priority.Workflow:Download Project and Indicator definitions when on Wi-Fi.Field officer enters data offline in Naluama.Data syncs to Django backend when they return to HQ.Summary of the " Use Case" FlowPlan (Web): Admin creates a Project "Naluama Solar" and tags it as Electrification. They set an Indicator target: "Connect 50 Households."Execute (Finance): The contractor submits a claim for buying solar panels. The PM approves it via the Maker-Checker module.Monitor (Mobile): Field officer visits the site. They open the app, select "Naluama Solar," and enter: 10 Households Connected. They attach a photo of the meter.Verify (Web): The M&E Manager sees the entry. They check the photo. If valid, the Electrification KRA on the dashboard updates automatically.This approach utilizes 100% of MonEva's existing "Skeleton" (Auth, Projects, Inspections, Finance) while dressing it in the "Skin" 


