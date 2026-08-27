"""Alert and Escalation Management Endpoints."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.data_ingestion import get_fused_data
from app.services.early_warning import get_early_warning_engine
from app.services.root_cause import RootCauseService
from app.services.business_impact import BusinessImpactService
from app.services.recommendation import RecommendationService

router = APIRouter()

# In-memory alert state storage (persisted alongside session)
ALERT_STORE: Dict[str, Dict[str, Any]] = {}


def generate_initial_alerts() -> List[Dict[str, Any]]:
    """Generate live alert list based on latest machine states."""
    global ALERT_STORE
    df = get_fused_data()
    engine = get_early_warning_engine()
    rc_service = RootCauseService()
    bi_service = BusinessImpactService()
    rec_service = RecommendationService()

    latest_df = df.sort_values(by="Timestamp").groupby("Machine_ID").last().reset_index()
    
    alerts = []
    for _, row in latest_df.iterrows():
        row_dict = row.to_dict()
        eval_res = engine.evaluate_telemetry(row_dict)
        risk = eval_res["composite_risk_score"]
        
        # Only create alerts for MEDIUM, HIGH, or CRITICAL
        if risk >= 35.0:
            mach_id = str(row["Machine_ID"])
            alert_id = f"ALT-{mach_id}-{str(row['Timestamp'])[:10]}"
            
            causes = rc_service.attribute_causes(row_dict, top_n=1)
            top_cause = causes[0]["factor_name"] if causes else "Sensor Excursion"
            
            impact = bi_service.estimate_impact(risk, row_dict)
            recs = rec_service.generate_recommendations(mach_id, risk, top_cause, row_dict)
            top_action = recs[0]["action"] if recs else "Inspect tool parameters"

            # Check existing store status
            existing = ALERT_STORE.get(alert_id, {})
            status = existing.get("status", "NEW" if risk >= 75.0 else "UNACKNOWLEDGED")
            owner = existing.get("owner", "Unassigned")
            escalated_to = existing.get("escalated_to", None)

            alert_obj = {
                "alert_id": alert_id,
                "machine_id": mach_id,
                "machine_name": str(row.get("Machine_Name", f"Tool {mach_id}")),
                "process_stage": str(row.get("Process_Stage", "General")),
                "risk_score": risk,
                "severity": eval_res["severity"],
                "severity_color": eval_res["severity_color"],
                "predicted_issue": f"High Disruption Risk ({eval_res['ml_disruption_probability']}%)",
                "top_cause": top_cause,
                "estimated_financial_impact": f"${impact['total_financial_exposure']:,.2f}",
                "affected_wafers": impact["estimated_affected_wafers"],
                "recommended_action": top_action,
                "owner": owner,
                "status": status,
                "escalated_to": escalated_to,
                "created_at": str(row["Timestamp"]),
            }
            ALERT_STORE[alert_id] = alert_obj
            alerts.append(alert_obj)

    # Sort critical first
    alerts.sort(key=lambda x: x["risk_score"], reverse=True)
    return alerts


@router.get("/", summary="List all Active Fab Alerts")
def get_alerts() -> List[Dict[str, Any]]:
    """Retrieve all current early warning disruption alerts."""
    return generate_initial_alerts()


class AlertActionRequest(BaseModel):
    user_name: str = "Operator"
    note: Optional[str] = None
    assignee: Optional[str] = None


@router.post("/{alert_id}/acknowledge", summary="Acknowledge Alert")
def acknowledge_alert(alert_id: str, req: AlertActionRequest) -> Dict[str, Any]:
    """Mark an alert as acknowledged by an engineer."""
    generate_initial_alerts()
    if alert_id not in ALERT_STORE:
        raise HTTPException(status_code=404, detail="Alert not found.")
    
    ALERT_STORE[alert_id]["status"] = "ACKNOWLEDGED"
    ALERT_STORE[alert_id]["owner"] = req.user_name
    ALERT_STORE[alert_id]["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
    return {"message": "Alert acknowledged successfully", "alert": ALERT_STORE[alert_id]}


@router.post("/{alert_id}/escalate", summary="Escalate Alert to Plant Manager")
def escalate_alert(alert_id: str, req: AlertActionRequest) -> Dict[str, Any]:
    """Escalate a critical disruption alert to leadership."""
    generate_initial_alerts()
    if alert_id not in ALERT_STORE:
        raise HTTPException(status_code=404, detail="Alert not found.")
    
    ALERT_STORE[alert_id]["status"] = "ESCALATED"
    ALERT_STORE[alert_id]["escalated_to"] = req.assignee or "Plant Manager & Equipment Director"
    ALERT_STORE[alert_id]["escalated_at"] = datetime.now(timezone.utc).isoformat()
    return {"message": "Alert escalated successfully", "alert": ALERT_STORE[alert_id]}


@router.post("/{alert_id}/resolve", summary="Resolve Alert")
def resolve_alert(alert_id: str, req: AlertActionRequest) -> Dict[str, Any]:
    """Mark an alert as resolved following maintenance."""
    generate_initial_alerts()
    if alert_id not in ALERT_STORE:
        raise HTTPException(status_code=404, detail="Alert not found.")
    
    ALERT_STORE[alert_id]["status"] = "RESOLVED"
    ALERT_STORE[alert_id]["resolved_by"] = req.user_name
    ALERT_STORE[alert_id]["resolved_at"] = datetime.now(timezone.utc).isoformat()
    return {"message": "Alert resolved successfully", "alert": ALERT_STORE[alert_id]}


class SendAlertRequest(BaseModel):
    alert_id: str
    target_role: str = Field("SUPERVISOR", json_schema_extra={"example": "SUPERVISOR"}) # PLANT_MANAGER, SUPERVISOR, MAINTENANCE
    recipient_email: Optional[str] = "supervisor@plant.local"
    custom_message: Optional[str] = "Urgent: Elevated disruption risk detected on fab tool."
    sender_name: str = "Control Tower Dispatcher"


@router.post("/send", summary="Send Alert Notification to End Users")
def send_alert_notification(req: SendAlertRequest) -> Dict[str, Any]:
    """Send alert notification directly to target end users (Plant Manager, Supervisor, Maintenance)."""
    generate_initial_alerts()
    if req.alert_id not in ALERT_STORE:
        mach_id = req.alert_id.split("-")[1] if "-" in req.alert_id else "M03"
        ALERT_STORE[req.alert_id] = {
            "alert_id": req.alert_id,
            "machine_id": mach_id,
            "severity": "CRITICAL",
            "predicted_issue": "Early Disruption Warning",
            "status": "ALERT_SENT",
            "owner": req.sender_name,
        }
    
    alert = ALERT_STORE[req.alert_id]
    alert["status"] = "ALERT_SENT"
    alert["sent_to_role"] = req.target_role
    alert["recipient_email"] = req.recipient_email
    alert["dispatch_notes"] = req.custom_message
    alert["sent_at"] = datetime.now(timezone.utc).isoformat()
    return {
        "message": f"Alert successfully dispatched to {req.target_role} ({req.recipient_email})",
        "alert": alert,
    }


class DispatchWorkOrderRequest(BaseModel):
    alert_id: str
    machine_id: str
    work_order_priority: str = "P1 - CRITICAL"
    assigned_technician: str = "Maintenance Tech Lead"
    procedure: str = "Inspect mechanical spindle bearings and recalibrate thermal chamber."


@router.post("/work-order", summary="Dispatch Maintenance Work Order")
def dispatch_work_order(req: DispatchWorkOrderRequest) -> Dict[str, Any]:
    """Dispatch formal maintenance work order for high-risk equipment."""
    generate_initial_alerts()
    wo_id = f"WO-{req.machine_id}-{datetime.now(timezone.utc).strftime('%H%M%S')}"
    if req.alert_id in ALERT_STORE:
        alert = ALERT_STORE[req.alert_id]
        alert["status"] = "WORK_ORDER_DISPATCHED"
        alert["work_order_id"] = wo_id
        alert["assigned_technician"] = req.assigned_technician
        alert["work_order_dispatched_at"] = datetime.now(timezone.utc).isoformat()
    
    return {
        "message": f"Work Order {wo_id} successfully created and dispatched to {req.assigned_technician}.",
        "work_order_id": wo_id,
        "machine_id": req.machine_id,
        "priority": req.work_order_priority,
        "assigned_technician": req.assigned_technician,
        "procedure": req.procedure,
        "status": "DISPATCHED",
    }
