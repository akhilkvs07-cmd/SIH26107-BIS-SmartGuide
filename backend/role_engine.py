"""BIS SmartGuide Role-Based Intelligence Engine.

Provides dedicated workflows, customized dashboard schemas, adaptive AI prompts,
and specialized compliance checklists for:
1. Manufacturer / MSME
2. Startup
3. Importer
4. Procurement / Buyer
5. Consumer
6. Laboratory / Testing
7. Compliance Professional
8. General
"""

from typing import Any, Dict, List

ROLES_CONFIG = {
    "manufacturer": {
        "id": "manufacturer",
        "title": "Manufacturer / MSME",
        "badge": "🏭 FACTORY & PRODUCTION",
        "tagline": "Quality Control, In-House Testing & Scheme I Licensing",
        "dashboard_title": "Manufacturing Compliance & Scheme I Cockpit",
        "kpis": [
            {"label": "Standard Mapped", "sub": "Factory Production Control"},
            {"label": "In-House Test Bench", "sub": "Routine & Acceptance Tests"},
            {"label": "Mandatory QCOs", "sub": "Gazette Order Deadlines"},
            {"label": "Scheme I Audit", "sub": "BIS Factory Inspection Readiness"}
        ],
        "quick_actions": [
            {"label": "Check In-House Testing Requirements", "action": "testing"},
            {"label": "Screen Scheme I Factory Audit Checklist", "action": "audit"},
            {"label": "Verify Applicable Raw Material Standards", "action": "materials"},
            {"label": "Generate Manufacturer Compliance Report", "action": "report"}
        ],
        "agent_system_prefix": (
            "You are speaking with a Manufacturer or MSME producing goods in India. "
            "Focus your guidance on factory production controls, Scheme I (ISI Mark) licensing, "
            "in-house testing equipment requirements, raw material conformity, and Gazette QCO legal deadlines."
        ),
        "product_perspective": "Manufacturing feasibility, production quality control, and Scheme I licensing route.",
        "checklist_intro": "Manufacturer Quality Control Checklist: verify factory testing capability and material controls."
    },
    "startup": {
        "id": "startup",
        "title": "Startup",
        "badge": "🚀 ACCELERATION & CONCESSIONS",
        "tagline": "Fast-Track Certification, Fee Concessions & Regulatory Roadmap",
        "dashboard_title": "Startup Launch & BIS Concession Roadmap",
        "kpis": [
            {"label": "50% Fee Rebate", "sub": "DPIIT Recognized Startup Concession"},
            {"label": "Prototyping Safety", "sub": "Essential Safety Milestones"},
            {"label": "Testing Options", "sub": "Third-Party Lab Hand-Off"},
            {"label": "Go-To-Market Gate", "sub": "Mandatory QCO Verification"}
        ],
        "quick_actions": [
            {"label": "View Startup Roadmap (7 Steps)", "action": "roadmap"},
            {"label": "Check DPIIT Startup Concession Eligibility", "action": "concessions"},
            {"label": "Find Low-Cost Pre-Compliance Testing Labs", "action": "labs"},
            {"label": "Download Minimum Viable Compliance Checklist", "action": "checklist"}
        ],
        "agent_system_prefix": (
            "You are speaking with an early-stage hardware or product Startup founder. "
            "Explain BIS requirements in simple, encouraging, actionable steps. "
            "Highlight DPIIT/MSME fee concessions (up to 50% rebate on application and inspection fees), "
            "recommend using accredited third-party labs for pre-compliance testing before factory setup, and warn of mandatory QCO gates."
        ),
        "product_perspective": "Fast-track launch roadmap, startup fee rebates, and essential safety baselines.",
        "checklist_intro": "Startup Milestone Checklist: progressive steps from product prototype to BIS market launch."
    },
    "importer": {
        "id": "importer",
        "title": "Importer",
        "badge": "📦 IMPORT & FMCS",
        "tagline": "Cross-Border Clearance, Port Requirements & FMCS Verification",
        "dashboard_title": "Import Regulatory Clearance & FMCS Dashboard",
        "kpis": [
            {"label": "FMCS Status", "sub": "Foreign Manufacturer Certification"},
            {"label": "Customs Port Gate", "sub": "B/E & QCO Verification at Port"},
            {"label": "Authorized Rep (AIR)", "sub": "Indian Representative Mandate"},
            {"label": "Lab Port Testing", "sub": "Consignment Testing Clearance"}
        ],
        "quick_actions": [
            {"label": "Check FMCS License for Foreign Factory", "action": "fmcs"},
            {"label": "Verify Import Port QCO Clearance Requirement", "action": "customs"},
            {"label": "Check Authorized Indian Representative (AIR) Rules", "action": "air"},
            {"label": "Generate Import Consignment Due-Diligence Report", "action": "report"}
        ],
        "agent_system_prefix": (
            "You are speaking with an Importer bringing manufactured goods into India. "
            "Focus on the Foreign Manufacturers Certification Scheme (FMCS Scheme IV), "
            "requirement of appointing an Authorized Indian Representative (AIR), "
            "customs clearance requirements under Directorate General of Foreign Trade (DGFT) and QCOs, and port sampling rules."
        ),
        "product_perspective": "Import compliance, FMCS scheme applicability, and customs clearance regulations.",
        "checklist_intro": "Import Consignment Due Diligence: cross-border documentation and factory licensing checks."
    },
    "procurement": {
        "id": "procurement",
        "title": "Procurement / Buyer",
        "badge": "🛒 VENDOR AUDIT & BUYING",
        "tagline": "Vendor Due Diligence, CM/L Validation & Batch Quality",
        "dashboard_title": "Procurement Verification & Vendor Audit Cockpit",
        "kpis": [
            {"label": "CM/L Active", "sub": "Supplier License Legitimacy"},
            {"label": "Batch Test Report", "sub": "Certificate of Analysis (CoA)"},
            {"label": "QCO Mandate", "sub": "Legal Compliance Risk"},
            {"label": "Counterfeit Screen", "sub": "Fake ISI Marking Alert"}
        ],
        "quick_actions": [
            {"label": "Validate Supplier CM/L Number Format", "action": "cml"},
            {"label": "Generate Vendor Procurement Checklist", "action": "vendor_check"},
            {"label": "Inspect Supplier Batch Test Report", "action": "test_report"},
            {"label": "Screen Potential Fake Mark / Suspicious Claims", "action": "fake_screen"}
        ],
        "agent_system_prefix": (
            "You are speaking with a Procurement Officer, Institutional Buyer or Supply Chain Manager. "
            "Provide rigorous due-diligence guidance: verifying supplier CM/L license authenticity on BIS portal, "
            "auditing batch test certificates (CoA), enforcing mandatory QCO clauses in purchase orders, and detecting counterfeit markings."
        ),
        "product_perspective": "Vendor verification, batch test certificate audit, and procurement risk mitigation.",
        "checklist_intro": "Procurement Due Diligence Checklist: mandatory criteria before approving purchase orders."
    },
    "consumer": {
        "id": "consumer",
        "title": "Consumer",
        "badge": "👤 CONSUMER SAFETY",
        "tagline": "Everyday Safety, Mark Verification & Buying Guide",
        "dashboard_title": "Consumer Product Safety & Genuine Mark Hub",
        "kpis": [
            {"label": "Genuine ISI Mark", "sub": "7-Digit CM/L Format"},
            {"label": "CRS Mark (IT Goods)", "sub": "8-Digit R-Number"},
            {"label": "HUID Hallmark", "sub": "Gold & Silver Jewellery"},
            {"label": "BIS Care App", "sub": "Official Verification Tool"}
        ],
        "quick_actions": [
            {"label": "What to Check on the Product Box Before Buying", "action": "box_check"},
            {"label": "Verify 7-Digit CM/L Number on BIS Care", "action": "cml_check"},
            {"label": "Understand What the IS Number Means", "action": "is_meaning"},
            {"label": "Draft a Complaint for Fake Mark or Hazardous Product", "action": "complaint"}
        ],
        "agent_system_prefix": (
            "You are speaking with an everyday Indian Consumer shopping for household products. "
            "Use clear, simple, non-technical language. Do not overwhelm with complex engineering clauses. "
            "Explain how to check the ISI mark, what the 7-digit CM/L number or CRS R-number means, "
            "how to use the BIS Care mobile app, and what safety hazards to look out for."
        ),
        "product_perspective": "Simple consumer buying advice, safety verification, and recognizing genuine marks.",
        "checklist_intro": "Consumer Safety Checklist: quick checks before making a purchase."
    },
    "laboratory": {
        "id": "laboratory",
        "title": "Laboratory / Testing",
        "badge": "🔬 TESTING & MEASUREMENT",
        "tagline": "Test Methods, Parameters, Tolerances & LIMS Directory",
        "dashboard_title": "Laboratory Scope & Test Engineering Workspace",
        "kpis": [
            {"label": "Test Standard Clauses", "sub": "Prescribed Test Procedures"},
            {"label": "Measured Limits", "sub": "Permissible Parameter Tolerances"},
            {"label": "LIMS IS Search", "sub": "Accredited Laboratory Directory"},
            {"label": "Test Report Schema", "sub": "Data Extraction & Comparison"}
        ],
        "quick_actions": [
            {"label": "View Clause-Level Testing Parameters", "action": "params"},
            {"label": "Search BIS LIMS for Accredited Testing Labs", "action": "lims"},
            {"label": "Parse Test Report for Measured Values", "action": "parse_report"},
            {"label": "Verify Sampling & Acceptance Criteria", "action": "sampling"}
        ],
        "agent_system_prefix": (
            "You are speaking with a Test Engineer or Laboratory Analyst. "
            "Provide precise technical and testing guidance: test methods, instrument accuracy, "
            "calibration standards, limits, tolerances, sampling plans, and BIS LIMS scope codes. "
            "Never invent test limits; cite authentic clauses and standard numbers."
        ),
        "product_perspective": "Laboratory testing specifications, instrument procedures, and measured limit parameters.",
        "checklist_intro": "Laboratory Test Protocol Checklist: verification of parameters against standard clauses."
    },
    "compliance": {
        "id": "compliance",
        "title": "Compliance Professional",
        "badge": "🧑‍💼 LEGAL & REGULATORY",
        "tagline": "Gazette Notifications, Legal Liability & Regulatory Passport",
        "dashboard_title": "Regulatory Intelligence & Compliance Passport Cockpit",
        "kpis": [
            {"label": "Gazette QCO Orders", "sub": "Statutory Quality Orders"},
            {"label": "Audit Traceability", "sub": "SHA-256 Evidence Hashing"},
            {"label": "Corrective Action Log", "sub": "SQLite Persistent Actions"},
            {"label": "Compliance Passport", "sub": "Persistent Audit Document"}
        ],
        "quick_actions": [
            {"label": "Review Gazette Quality Control Order Details", "action": "qco"},
            {"label": "Inspect Compliance Passport and Evidence Hash", "action": "passport"},
            {"label": "Track Corrective Actions & Resolution Status", "action": "actions"},
            {"label": "Export Audit-Ready Legal Compliance Report", "action": "legal_report"}
        ],
        "agent_system_prefix": (
            "You are speaking with a Senior Regulatory Affairs and Compliance Professional. "
            "Provide rigorous, legally grounded guidance: Gazette Quality Control Orders (QCOs), "
            "enforcing ministries (DPIIT, MeitY, MoPNG, MoRTH), statutory effective dates, "
            "penal provisions under Section 29 of the BIS Act 2016, and evidence trail hashing."
        ),
        "product_perspective": "Statutory regulatory compliance, Gazette notifications, and audit-grade evidence trail.",
        "checklist_intro": "Regulatory Audit Checklist: clause-level conformity and statutory order verification."
    },
    "general": {
        "id": "general",
        "title": "General",
        "badge": "🌐 UNIFIED PLATFORM",
        "tagline": "Full-Spectrum BIS Standards Discovery & Intelligence",
        "dashboard_title": "BIS Standards Intelligence Platform",
        "kpis": [
            {"label": "Standards Indexed", "sub": "Authentic Indian Standards"},
            {"label": "Retrieval Chunks", "sub": "Agentic RAG Engine"},
            {"label": "Official Resources", "sub": "BIS Portal & LIMS"},
            {"label": "Decision Support", "sub": "Zero Fabricated Data"}
        ],
        "quick_actions": [
            {"label": "Search Product or Indian Standard", "action": "search"},
            {"label": "Run Natural-Language Product Intelligence", "action": "intel"},
            {"label": "Evaluate Interactive Compliance Checklist", "action": "compliance"},
            {"label": "Ask Multilingual AI Standards Agent", "action": "agent"}
        ],
        "agent_system_prefix": (
            "You are the BIS Standards Intelligence Assistant. "
            "Provide authoritative, source-grounded guidance on Indian Standards (IS), "
            "certification schemes, laboratory testing, and mandatory Quality Control Orders."
        ),
        "product_perspective": "Comprehensive overview covering standards, compliance, and official resources.",
        "checklist_intro": "Standard Compliance Checklist: evaluate requirement satisfaction."
    }
}

class RoleEngine:
    @staticmethod
    def get_role(role_id: str) -> Dict[str, Any]:
        cleaned = str(role_id or "").strip().lower()
        return ROLES_CONFIG.get(cleaned, ROLES_CONFIG["general"])

    @staticmethod
    def list_roles() -> List[Dict[str, str]]:
        return [
            {"id": k, "title": v["title"], "badge": v["badge"], "tagline": v["tagline"]}
            for k, v in ROLES_CONFIG.items()
        ]

    @staticmethod
    def adapt_checklist(product_info: Dict[str, Any], role_id: str) -> Dict[str, Any]:
        role = RoleEngine.get_role(role_id)
        std = product_info.get("standard") or {}
        reqs = std.get("requirements", [])

        specialized_checks = []
        for r in reqs:
            specialized_checks.append({
                "requirement": r,
                "role_focus": role["title"],
                "role_instruction": f"[{role['title']}] Review '{r}' per {std.get('standard_number', 'the standard')} requirements."
            })

        extra_actions = []
        if role["id"] in ["manufacturer", "startup"]:
            extra_actions.append("Establish internal calibration log for test apparatus before application.")
            extra_actions.append("Maintain Scheme I Quality Assurance Plan (QAP).")
        elif role["id"] == "importer":
            extra_actions.append("Verify foreign factory FMCS license validity.")
            extra_actions.append("Ensure Authorized Indian Representative (AIR) power of attorney is registered.")
        elif role["id"] == "procurement":
            extra_actions.append("Request manufacturer test certificate (CoA) for the specific batch.")
            extra_actions.append("Verify CM/L number in official BIS directory before issuing PO.")
        elif role["id"] == "consumer":
            extra_actions.append("Confirm the presence of 7-digit CM/L number beneath the ISI mark.")
            extra_actions.append("Verify standard number on the label matches product application.")

        return {
            "role": role["id"],
            "role_title": role["title"],
            "intro": role["checklist_intro"],
            "standard_number": std.get("standard_number"),
            "product": product_info.get("product"),
            "checks": specialized_checks,
            "role_specific_actions": extra_actions
        }

    @staticmethod
    def adapt_report(report_data: Dict[str, Any], role_id: str) -> Dict[str, Any]:
        role = RoleEngine.get_role(role_id)
        res = dict(report_data)
        res["role_metadata"] = {
            "target_role": role["title"],
            "perspective": role["product_perspective"],
            "disclaimer": "AI-assisted guidance tailored to " + role["title"] + ". Official BIS certification must be obtained through BIS portals."
        }
        return res
