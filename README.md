# Semiconductor AI Production Disruption Early Warning & Decision Support System

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.37%2B-FF4B4B.svg)](https://streamlit.io)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red.svg)](https://www.sqlalchemy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade AI-powered Early Warning and Decision Support Control Tower engineered for semiconductor wafer fabs. The platform transforms raw manufacturing process signals, tool telemetry, quality inspections, and material flows into actionable early warning disruption alerts, root-cause attributions (SHAP), business impact evaluations, and guided mitigation workflows.

---

## 🏛 System Architecture Overview

```
semiconductor-early-warning/
├── app/                        # FastAPI Backend Service
│   ├── api/v1/                 # Versioned REST API Endpoints
│   ├── config.py               # Pydantic Settings & Environment Management
│   ├── database.py             # SQLAlchemy ORM & Connection Engine
│   ├── models/                 # Database Entity Models
│   ├── schemas/                # Pydantic Request/Response DTOs
│   ├── services/               # Core Business Logic & Orchestration
│   ├── ml/                     # ML Training, Inference & Calibration Pipelines
│   ├── security/               # JWT Authentication & RBAC Authorization
│   ├── notifications/          # SMTP Email Alert Engine & Throttling
│   └── utils/                  # Statistical & Data Formatting Helpers
├── dashboard/                  # Streamlit Enterprise Industrial Control Tower
│   ├── app.py                  # Main Dashboard Entrypoint
│   ├── styles/custom.css       # Industrial Dark Theme Styling
│   ├── components/             # Reusable UI & Metric Cards
│   └── pages/                  # Specialized Role-Based Views
├── data/                       # Data Pipeline Storage (Raw, Processed, Synthetic)
├── models/                     # Model Registry (Trained Artifacts & Pipelines)
├── tests/                      # Automated Pytest Suite (Unit, Integration, API)
└── scripts/                    # Pipeline & Training Automation Scripts
```

---

## 🚀 Quick Start Guide

### 1. Clone & Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd "manfacture early detection"

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and adjust configuration if needed:
```bash
cp .env.example .env
```

### 3. Run FastAPI Backend
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 4. Run Streamlit Control Tower
In a separate terminal:
```bash
python -m streamlit run dashboard/control_tower.py --server.port 8501
```
- Dashboard Access: [http://localhost:8501](http://localhost:8501)

---

## 🧪 Automated Testing
Run the comprehensive Pytest test suite:
```bash
pytest -v tests/
```

---

## 📋 Implementation Roadmap

- [x] **Phase 1**: Architecture setup, dependencies, configuration, SQLAlchemy DB layer, FastAPI health endpoints, Streamlit Control Tower skeleton.
- [ ] **Phase 2**: Dataset acquisition (UCI SECOM, WM-811K), schema normalization, automated data quality & drift checks.
- [ ] **Phase 3**: Feature engineering, high-dimensional variance filtering, leakage-free cross-validation baseline.
- [ ] **Phase 4**: Multi-model ML architecture (Isolation Forest anomaly engine, Random Forest / HistGradientBoosting yield risk, probability calibration).
- [ ] **Phase 5**: Early warning prioritization, SHAP root cause attribution, business impact financial estimator, decision support recommendation engine.
- [ ] **Phase 6**: Complete FastAPI REST API endpoints.
- [ ] **Phase 7**: JWT authentication, role-based access control (RBAC), and session security.
- [ ] **Phase 8**: Full multi-page Streamlit Industrial Control Tower.
- [ ] **Phase 9**: SMTP email alerting with alert throttling and cooldown protection.
- [ ] **Phase 10**: Live simulation & what-if disruption engine.
- [ ] **Phase 11**: Automated PDF/CSV reports, audit logging, model performance monitoring.
- [ ] **Phase 12**: Docker containerization, end-to-end testing, and deployment verification.
