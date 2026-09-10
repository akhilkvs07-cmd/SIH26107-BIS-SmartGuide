"""BIS SmartGuide Role-Based Intelligence Engine.

Provides dedicated workflows, customized dashboard schemas, adaptive AI prompts,
and specialized compliance checklists for the supported SmartGuide personas.
"""

from typing import Any, Dict, List

ROLES_CONFIG = {
    "manufacturer": {
        "id": "manufacturer", "title": "Manufacturer / MSME", "badge": "🏭 FACTORY & PRODUCTION",
        "tagline": "Quality Control, In-House Testing & Scheme I Licensing",
        "dashboard_title": "Manufacturing Compliance & Scheme I Cockpit",
        "kpis": [{"label": "Standard Mapped", "sub": "Factory Production Control"}, {"label": "In-House Test Bench", "sub": "Routine & Acceptance Tests"}, {"label": "Mandatory QCOs", "sub": "Gazette Order Deadlines"}, {"label": "Scheme I Audit", "sub": "BIS Factory Inspection Readiness"}],
        "quick_actions": [{"label": "Check In-House Testing Requirements", "action": "testing"}, {"label": "Screen Scheme I Factory Audit Checklist", "action": "audit"}, {"label": "Verify Applicable Raw Material Standards", "action": "materials"}, {"label": "Generate Manufacturer Compliance Report", "action": "report"}],
        "agent_system_prefix": "You are speaking with a Manufacturer or MSME producing goods in India. Focus your guidance on factory production controls, Scheme I licensing, in-house testing, raw material conformity, and QCO deadlines.",
        "product_perspective": "Manufacturing feasibility, production quality control, and Scheme I licensing route.", "checklist_intro": "Manufacturer Quality Control Checklist: verify factory testing capability and material controls."
    },
    "startup": {
        "id": "startup", "title": "Startup", "badge": "🚀 ACCELERATION & CONCESSIONS", "tagline": "Product launch and BIS compliance roadmap",
        "dashboard_title": "Startup Launch & BIS Roadmap", "kpis": [],
        "quick_actions": [{"label": "View Startup Roadmap", "action": "roadmap"}, {"label": "Find Testing Labs", "action": "labs"}],
        "agent_system_prefix": "You are speaking with an early-stage product startup. Explain BIS requirements in simple, actionable steps and clearly separate verified requirements from guidance.",
        "product_perspective": "Product launch, safety baselines, testing and certification route.", "checklist_intro": "Startup milestone checklist from prototype to market entry."
    },
    "importer": {
        "id": "importer", "title": "Importer", "badge": "📦 IMPORT & FMCS", "tagline": "Cross-border compliance and documentation",
        "dashboard_title": "Import Regulatory Clearance Dashboard", "kpis": [],
        "quick_actions": [{"label": "Check QCO", "action": "qco"}, {"label": "Find Labs", "action": "labs"}],
        "agent_system_prefix": "You are speaking with an importer. Focus on product scope, QCO applicability, foreign-manufacturer routes and documentation, without inventing legal requirements.",
        "product_perspective": "Import compliance and applicable conformity assessment route.", "checklist_intro": "Import due-diligence checklist."
    },
    "procurement": {
        "id": "procurement", "title": "Procurement / Buyer", "badge": "🛒 VENDOR AUDIT & BUYING", "tagline": "Vendor due diligence and evidence review",
        "dashboard_title": "Procurement Verification Cockpit", "kpis": [],
        "quick_actions": [{"label": "Screen CM/L", "action": "cml"}, {"label": "Inspect Test Report", "action": "test_report"}],
        "agent_system_prefix": "You are speaking with a procurement professional. Focus on supplier evidence, CM/L screening, test reports and QCO controls. Never claim a licence is verified without an official source response.",
        "product_perspective": "Vendor verification and evidence-based procurement risk control.", "checklist_intro": "Procurement due-diligence checklist."
    },
    "consumer": {
        "id": "consumer", "title": "Consumer", "badge": "👤 CONSUMER SAFETY", "tagline": "Product safety and genuine-mark guidance",
        "dashboard_title": "Consumer Product Safety Hub", "kpis": [],
        "quick_actions": [{"label": "Verify ISI / CM/L", "action": "cml_check"}, {"label": "Check HUID", "action": "huid"}],
        "agent_system_prefix": "You are speaking with an everyday consumer. Use simple language and explain how to check product markings and safety evidence. Do not call format checks official verification.",
        "product_perspective": "Simple consumer safety and mark-verification guidance.", "checklist_intro": "Consumer safety checklist."
    },
    "laboratory": {
        "id": "laboratory", "title": "Laboratory / Testing", "badge": "🔬 TESTING & MEASUREMENT", "tagline": "Test parameters and evidence mapping",
        "dashboard_title": "Laboratory Test Engineering Workspace", "kpis": [],
        "quick_actions": [{"label": "View Test Parameters", "action": "params"}, {"label": "Search LIMS", "action": "lims"}],
        "agent_system_prefix": "You are speaking with a test engineer. Cite standard evidence where available and never invent limits, tolerances or test methods.",
        "product_perspective": "Testing parameters, measurements and laboratory scope.", "checklist_intro": "Laboratory test protocol checklist."
    },
    "compliance": {
        "id": "compliance", "title": "Compliance Professional", "badge": "🧑‍💼 LEGAL & REGULATORY", "tagline": "Evidence, QCO and audit traceability",
        "dashboard_title": "Regulatory Intelligence Cockpit", "kpis": [],
        "quick_actions": [{"label": "Review QCO", "action": "qco"}, {"label": "Inspect Passport", "action": "passport"}],
        "agent_system_prefix": "You are speaking with a compliance professional. Separate verified source evidence, inference, user-provided information and unavailable data.",
        "product_perspective": "Regulatory compliance and audit-grade evidence traceability.", "checklist_intro": "Regulatory audit checklist."
    },
    "general": {
        "id": "general", "title": "General", "badge": "🌐 UNIFIED PLATFORM", "tagline": "BIS standards discovery and intelligence",
        "dashboard_title": "BIS Standards Intelligence Platform", "kpis": [],
        "quick_actions": [{"label": "Search Standards", "action": "search"}, {"label": "Product Intelligence", "action": "intel"}],
        "agent_system_prefix": "You are the BIS Standards Intelligence Assistant. Use source-grounded evidence and explicitly refuse unsupported claims.",
        "product_perspective": "Standards discovery and decision support.", "checklist_intro": "Standard compliance checklist."
    }
}

ROLE_ALIASES = {"manufacturer_msme": "manufacturer", "compliance_pro": "compliance", "buyer": "procurement", "testing_laboratory": "laboratory"}


class RoleEngine:
    @staticmethod
    def get_role(role_id: str) -> Dict[str, Any]:
        cleaned = str(role_id or "").strip().lower()
        cleaned = ROLE_ALIASES.get(cleaned, cleaned)
        return ROLES_CONFIG.get(cleaned, ROLES_CONFIG["general"])

    @staticmethod
    def list_roles() -> List[Dict[str, str]]:
        return [{"id": k, "title": v["title"], "badge": v["badge"], "tagline": v["tagline"]} for k, v in ROLES_CONFIG.items()]

    @staticmethod
    def adapt_checklist(product_info: Dict[str, Any], role_id: str) -> Dict[str, Any]:
        role = RoleEngine.get_role(role_id); std = product_info.get("standard") or {}; reqs = std.get("requirements", [])
        specialized_checks = [{"requirement": r, "role_focus": role["title"], "role_instruction": f"[{role['title']}] Review '{r}' per {std.get('standard_number', 'the standard')} requirements."} for r in reqs]
        extra_actions = []
        if role["id"] == "manufacturer": extra_actions += ["Maintain objective factory testing evidence.", "Maintain current production quality records."]
        elif role["id"] == "importer": extra_actions += ["Verify the applicable foreign-manufacturer/conformity route from official BIS sources."]
        elif role["id"] == "procurement": extra_actions += ["Request batch-specific objective test evidence.", "Verify supplier claims through an official BIS source."]
        elif role["id"] == "consumer": extra_actions += ["Treat CM/L, R-number and HUID format detection as screening until officially verified."]
        return {"role": role["id"], "role_title": role["title"], "intro": role["checklist_intro"], "standard_number": std.get("standard_number"), "product": product_info.get("product"), "checks": specialized_checks, "role_specific_actions": extra_actions}

    @staticmethod
    def adapt_report(report_data: Dict[str, Any], role_id: str) -> Dict[str, Any]:
        role = RoleEngine.get_role(role_id); res = dict(report_data)
        res["role_metadata"] = {"target_role": role["title"], "perspective": role["product_perspective"], "disclaimer": "AI-assisted guidance. Official BIS certification must be obtained through BIS channels."}
        return res
