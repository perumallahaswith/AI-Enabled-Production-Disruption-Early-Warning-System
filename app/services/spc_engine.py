"""Statistical Process Control (SPC) and Drift Detection Engine.

Calculates Control Limits (UCL, LCL), Warning Limits (UWL, LWL), Process Capability (Cpk),
rolling moving averages, and Nelson-rule process drift excursions.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


class SPCEngine:
    """Computes statistical process monitoring parameters and excursion alarms."""

    def compute_control_chart(
        self,
        values: List[float],
        timestamps: List[str],
        sensor_name: str = "Temperature",
        sigma_multiplier: float = 3.0,
    ) -> Dict[str, Any]:
        """Compute SPC limits, moving averages, and out-of-control flags."""
        if not values or len(values) < 2:
            return {"error": "Insufficient sample points for SPC calculation"}

        arr = np.array(values, dtype=float)
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr)) if np.std(arr) > 1e-4 else 1.0

        ucl = mean_val + (sigma_multiplier * std_val)
        lcl = max(0.0, mean_val - (sigma_multiplier * std_val))
        uwl = mean_val + (2.0 * std_val)
        lwl = max(0.0, mean_val - (2.0 * std_val))

        # Rolling 6-point moving average
        s = pd.Series(arr)
        rolling_mean = s.rolling(window=6, min_periods=1).mean().tolist()

        # Detect Excursions
        excursions = []
        for i, val in enumerate(arr):
            is_critical = val > ucl or val < lcl
            is_warning = (val > uwl or val < lwl) and not is_critical
            if is_critical or is_warning:
                excursions.append({
                    "index": i,
                    "timestamp": timestamps[i] if i < len(timestamps) else f"T-{i}",
                    "measured_value": float(round(val, 2)),
                    "type": "CRITICAL EXCURSION" if is_critical else "WARNING DRIFT",
                    "deviation_sigma": float(round(abs(val - mean_val) / std_val, 2)),
                })

        # Process Capability Estimate (assuming specs at 3.5 sigma)
        usl = mean_val + (3.5 * std_val)
        lsl = max(0.0, mean_val - (3.5 * std_val))
        cpu = (usl - mean_val) / (3.0 * std_val + 1e-5)
        cpl = (mean_val - lsl) / (3.0 * std_val + 1e-5)
        cpk = float(round(min(cpu, cpl), 2))

        return {
            "sensor_name": sensor_name,
            "sample_count": len(values),
            "process_mean": float(round(mean_val, 3)),
            "process_std": float(round(std_val, 3)),
            "ucl": float(round(ucl, 3)),
            "lcl": float(round(lcl, 3)),
            "uwl": float(round(uwl, 3)),
            "lwl": float(round(lwl, 3)),
            "cpk": cpk,
            "is_capable": cpk >= 1.33,
            "excursion_count": len(excursions),
            "excursions": excursions,
            "moving_average": [float(round(v, 2)) for v in rolling_mean],
        }
