"""Decision Support Action Recommendation Engine.

Generates structured, actionable mitigation procedures with priority, owner,
and expected yield recovery benefit based on early warning signals.
"""

from typing import Dict, Any, List


class RecommendationService:
    """Generates decision-support corrective action plans for fab engineers."""

    def generate_recommendations(
        self,
        machine_id: str,
        risk_score: float,
        top_cause: str,
        telemetry: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate structured recommendation items."""
        actions = []

        if risk_score >= 80.0:
            actions.append({
                "action": f"Initiate Immediate Tool Intercept on {machine_id}",
                "reason": f"Disruption risk is CRITICAL ({risk_score:.0f}/100) driven by {top_cause}.",
                "priority": "P1 - CRITICAL",
                "urgency": "Immediate (< 15 mins)",
                "owner": "Shift Maintenance Lead & Process Supervisor",
                "expected_benefit": "Averts catastrophic wafer scrap and unplanned chamber lockup.",
            })
            actions.append({
                "action": "Reroute Incoming Wafers to Standby Bay Tool",
                "reason": "Prevents WIP backlog and queue time violations.",
                "priority": "P1 - HIGH",
                "urgency": "Within 30 mins",
                "owner": "Manufacturing Execution System (MES) Operator",
                "expected_benefit": "Preserves lot throughput and due-date delivery schedule.",
            })
            actions.append({
                "action": "Perform Calibration and Subsystem Diagnostic Check",
                "reason": f"Verify sensor calibration and mechanical couplings for {top_cause}.",
                "priority": "P2 - MEDIUM",
                "urgency": "Before lot release",
                "owner": "Equipment Maintenance Technician",
                "expected_benefit": "Restores process Cpk and tool reliability index.",
            })
        elif risk_score >= 50.0:
            actions.append({
                "action": f"Schedule Pre-Emptive Inspection on {machine_id}",
                "reason": f"Early warning elevated risk ({risk_score:.0f}/100) indicates developing excursion in {top_cause}.",
                "priority": "P2 - MEDIUM",
                "urgency": "Within current shift (4 hours)",
                "owner": "Process Engineer",
                "expected_benefit": "Prevents escalation to unplanned tool shutdown.",
            })
            actions.append({
                "action": "Tighten In-Line SPC Control Limits & Increase Metrology Sampling",
                "reason": "Detect early micro-drifts before wafer yield degradation occurs.",
                "priority": "P3 - LOW",
                "urgency": "Next lot run",
                "owner": "Quality Engineer",
                "expected_benefit": "Ensures zero defective die escape to downstream packaging.",
            })
        else:
            actions.append({
                "action": f"Maintain Standard In-Line Monitoring for {machine_id}",
                "reason": f"Operating within nominal parameters ({risk_score:.0f}/100).",
                "priority": "P4 - ROUTINE",
                "urgency": "Next scheduled PM",
                "owner": "Area Technician",
                "expected_benefit": "Optimal tool utilization and stable wafer yield.",
            })

        return actions
