# 📦 Changelog

All notable changes to this project will be documented in this file.

This project follows semantic versioning.

---

## [1.0.0] – 2026-01-14

### 🎉 Initial Stable Release

### ✨ Features
- Person-wise meal tracking
- Daily meal entry with Auto (Lunch + Dinner) and Manual modes
- Automatic meal cost calculation
- MongoDB-based persistent storage (local & Atlas support)
- Monthly filtering and reporting
- Meal vs Date chart visualization
- CSV and Excel export support
- User feedback system with ratings
- Password-protected admin feedback panel
- Safe edit and delete operations using ObjectId
- Reset form without deleting stored data

### 🪵 Logging
- Centralized logging using `logger.py`
- Logged actions:
  - Record create, update, and delete
  - Data export (CSV, Excel, monthly reports)
  - Feedback submission and deletion
  - Admin login and logout

### 🔐 Security
- Secrets managed via `.streamlit/secrets.toml`
- MongoDB URI and admin password not hard-coded
- Admin access protected by password
- Person-wise data isolation

### 🛠 Tech Stack
- Streamlit for UI
- MongoDB with PyMongo
- Pandas for data processing
- openpyxl for Excel exports
- Python logging module

---

## [Unreleased]
- Date range filtering
- Advanced charting (bar / pie)
- PDF bill or invoice generation
- User authentication and role-based access
- Email notifications for feedback
- MongoDB aggregation-based analytics
- Cloud-based centralized logging (ELK / CloudWatch)

---
