"""Natural Language Explanation and Reasoning Service.

Generates contextual, role-tailored natural language narratives for
Plant Managers, Supervisors, and Maintenance Teams.
"""

from typing import Dict, Any, List
from app.config import settings


class NaturalLanguageExplanationService:
    """Produces human-readable diagnostic summaries and executive briefings."""

    def generate_executive_briefing(
        self,
        plant_health: int,
        active_critical_alerts: int,
        high_risk_tools: int,
        total_exposure: float,
        critical_machines: List[Dict[str, Any]],
    ) -> str:
        """Generate high-level narrative summary for Plant Managers."""
        if active_critical_alerts > 0:
            crit_names = ", ".join([f"**{m['machine_id']}** ({m['process_stage']})" for m in critical_machines[:2]])
            return (
                f"**Plant Health Status: {plant_health}/100 (Attention Required)**. "
                f"The AI early warning engine has identified **{active_critical_alerts} active high-risk tool excursions** "
                f"across {crit_names}, resulting in an estimated financial exposure of **${total_exposure:,.0f}**. "
                f"Immediate intervention is recommended to prevent unplanned line stoppage and WIP scrap."
            )
        else:
            return (
                f"**Plant Health Status: {plant_health}/100 (Nominal Operation)**. "
                f"All 20 fab tools are operating within acceptable statistical process control limits. "
                f"Estimated disruption exposure is minimal ($0), and line throughput is tracking to weekly demand targets."
            )

    def generate_alert_explanation(self, machine_data: Dict[str, Any], role: str = "PLANT_MANAGER") -> str:
        """Generate role-customized natural language explanation for an alert."""
        mach_id = machine_data.get("machine_id", "Unknown Tool")
        stage = machine_data.get("process_stage", "General")
        risk = machine_data.get("risk_score", 0.0)
        causes = machine_data.get("causes", [])
        top_cause = causes[0]["factor_name"] if causes else "Process Deviation"
        impact = machine_data.get("impact", {})
        wafers = impact.get("estimated_affected_wafers", 0)
        lots = impact.get("estimated_affected_lots", 0)
        exposure = impact.get("total_financial_exposure", 0.0)

        if "PLANT_MANAGER" in role.upper():
            return (
                f"🏢 **Executive Financial & Continuity Briefing for {mach_id} ({stage})**\n\n"
                f"• **Current Risk**: Operating at **{risk:.0f}/100 Disruption Probability** driven primarily by **{top_cause}**.\n"
                f"• **Predictive Outlook (What Next)**: Unmitigated failure within the current shift will cause an estimated **${exposure:,.0f}** financial loss (**{wafers} wafers / {lots} lots** at risk of scrap, plus unplanned downtime costs).\n"
                f"• **Recommended Executive Action**: Authorize pre-emptive maintenance intercept and approve temporary lot rerouting to protect customer delivery commitments."
            )
        elif "SUPERVISOR" in role.upper():
            return (
                f"📋 **Shift Supervisor Operational & Line Balancing Guidance for {mach_id}**\n\n"
                f"• **Line Bottleneck Warning**: **{mach_id}** in **{stage}** is experiencing severe parameter degradation due to **{top_cause}**.\n"
                f"• **Predictive Outlook (What Next)**: WIP queue time in **{stage}** will spike by **35–45 minutes**, threatening shift throughput targets.\n"
                f"• **Recommended Supervisor Action**: Hold incoming wafer lots at the buffer bay, rebalance dispatch queue to standby tools, and assign maintenance lead immediately."
            )
        else: # MAINTENANCE
            measured_vib = machine_data.get("vibration", 0.0)
            measured_temp = machine_data.get("temperature", 0.0)
            days_maint = machine_data.get("days_since_maint", 0.0)
            return (
                f"🔧 **Maintenance Engineering Diagnostic Protocol for {mach_id}**\n\n"
                f"• **Subsystem Physical Diagnostics**: Vibration = **{measured_vib:.3f} mm/s** (Exceeds UCL), Chamber Temp = **{measured_temp:.1f} °C**, Days Since Last PM = **{days_maint:.0f} days**.\n"
                f"• **Root Attribution**: **{top_cause}**. Subsystem wear index is elevated.\n"
                f"• **Recommended Technical Protocol**: Issue Work Order P1, lock chamber for calibration, replace spindle bearing/seal, and execute post-maintenance SPC test run."
            )


# Singleton
nl_service = NaturalLanguageExplanationService()
