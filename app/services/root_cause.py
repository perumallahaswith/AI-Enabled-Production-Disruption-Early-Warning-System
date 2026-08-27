"""Root Cause and Contributing Factor Attribution Engine.

Analyzes model-attributed feature importance and parameter excursions
to explain why a machine has elevated disruption risk.
"""

from typing import Dict, Any, List
import numpy as np


class RootCauseService:
    """Attributes early warning risk to top contributing physical and operational factors."""

    ATTRIBUTE_LABELS: Dict[str, str] = {
        "Vibration": "Mechanical Vibration Instability",
        "Vibration_RollMean_6h": "6h Elevated Vibration Trend",
        "Vib_Process_Drift": "Vibration Baseline Drift",
        "Temperature": "Thermal Process Excursion",
        "Temperature_RollMean_6h": "6h Thermal Elevation Trend",
        "Temp_Process_Drift": "Chamber Thermal Drift",
        "Machine_Efficiency_Pct": "Degraded Tool Operating Efficiency",
        "Cycle_Time_Sec": "Cycle Time Prolongation / Delay",
        "Days_Since_Maintenance": "Overdue Maintenance Wear Factor",
        "Maintenance_Wear_Index": "Cumulative Tool Age Wear Index",
        "Power_Consumption": "Abnormal Power Surge / Resistance",
        "Pressure": "Vacuum Chamber Pressure Deviation",
        "Particle_Count": "Cleanroom Particle Excursion",
        "Chemical_Flow_Rate": "Chemical Reagent Flow Inconsistency",
    }

    def attribute_causes(self, telemetry: Dict[str, Any], top_n: int = 5) -> List[Dict[str, Any]]:
        """Identify top contributing factors for an elevated risk observation."""
        contributions = []

        # 1. Vibration factor
        vib = float(telemetry.get("Vibration", telemetry.get("vibration", 0.0)))
        vib_weight = min(max((vib - 0.5) * 60.0, 5.0), 95.0)
        contributions.append({
            "factor_name": "Mechanical Vibration Instability",
            "feature_key": "Vibration",
            "contribution_pct": vib_weight,
            "measured_value": f"{vib:.2f} mm/s",
            "baseline_reference": "0.45 mm/s",
            "status": "EXCURSION" if vib > 0.8 else "ELEVATED" if vib > 0.6 else "NOMINAL",
        })

        # 2. Machine Efficiency factor
        eff = float(telemetry.get("Machine_Efficiency_Pct", telemetry.get("machine_efficiency_pct", 92.0)))
        eff_weight = min(max((100.0 - eff) * 3.5, 5.0), 90.0)
        contributions.append({
            "factor_name": "Degraded Tool Operating Efficiency",
            "feature_key": "Machine_Efficiency_Pct",
            "contribution_pct": eff_weight,
            "measured_value": f"{eff:.1f}%",
            "baseline_reference": "> 95.0%",
            "status": "CRITICAL" if eff < 80 else "DEGRADED" if eff < 90 else "NOMINAL",
        })

        # 3. Thermal Stability factor
        temp = float(telemetry.get("Temperature", telemetry.get("temperature", 350.0)))
        temp_diff = abs(temp - 350.0)
        temp_weight = min(max(temp_diff * 4.0, 5.0), 85.0)
        contributions.append({
            "factor_name": "Chamber Thermal Excursion",
            "feature_key": "Temperature",
            "contribution_pct": temp_weight,
            "measured_value": f"{temp:.1f} °C",
            "baseline_reference": "350.0 °C ± 5.0",
            "status": "EXCURSION" if temp_diff > 15 else "WARNING" if temp_diff > 8 else "NOMINAL",
        })

        # 4. Maintenance Wear factor
        days_maint = float(telemetry.get("Days_Since_Maintenance", telemetry.get("days_since_maintenance", 15.0)))
        maint_weight = min(max((days_maint / 30.0) * 45.0, 5.0), 80.0)
        contributions.append({
            "factor_name": "Maintenance Wear Factor",
            "feature_key": "Days_Since_Maintenance",
            "contribution_pct": maint_weight,
            "measured_value": f"{days_maint:.0f} days",
            "baseline_reference": "< 30 days",
            "status": "OVERDUE" if days_maint > 30 else "ELEVATED" if days_maint > 22 else "NOMINAL",
        })

        # 5. Pressure / Gas Stability factor
        press = float(telemetry.get("Pressure", telemetry.get("pressure", 1.0)))
        press_weight = min(max(abs(press - 1.0) * 75.0, 5.0), 75.0)
        contributions.append({
            "factor_name": "Chamber Pressure Stability",
            "feature_key": "Pressure",
            "contribution_pct": press_weight,
            "measured_value": f"{press:.2f} atm",
            "baseline_reference": "1.00 atm ± 0.05",
            "status": "WARNING" if abs(press - 1.0) > 0.15 else "NOMINAL",
        })

        # 6. False Telemetry / Corrupted Sensor Data Disruption factor
        is_false_data = bool(telemetry.get("False_Data_Flag", 0) == 1 or vib > 1.10 or temp > 375.0 or abs(press - 1.0) > 0.35)
        if is_false_data:
            contributions.append({
                "factor_name": "False Telemetry / Sensor Data Disruption",
                "feature_key": "False_Data_Disruption",
                "contribution_pct": 85.0,
                "measured_value": f"Corrupted Signal (Vib: {vib:.2f}, Temp: {temp:.1f}°C)",
                "baseline_reference": "Verified Sensor Telemetry",
                "status": "FALSE_DATA_ALERT",
            })

        # Normalize percentages to sum to 100%
        total_raw = sum(c["contribution_pct"] for c in contributions)
        for c in contributions:
            c["contribution_pct"] = float(round((c["contribution_pct"] / total_raw) * 100.0, 1))

        # Sort descending
        contributions = sorted(contributions, key=lambda x: x["contribution_pct"], reverse=True)
        return contributions[:top_n]
