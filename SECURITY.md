# 🔐 Security Policy

This document describes the security practices, supported versions, and how to report security issues for the **Meal Tracker** application.

---

## 📦 Supported Versions

Only the latest version of the application is actively supported with security updates.

| Version | Supported |
|--------|-----------|
| Latest | ✅ Yes |
| Older | ❌ No |

Always use the most recent release to receive fixes and improvements.

---

## 🔒 Security Practices

### 1️⃣ Secrets Management
- Sensitive credentials **must not** be hard-coded.
- The application uses `.streamlit/secrets.toml` for:
  - `MONGO_URI`
  - `ADMIN_PASSWORD`
- This file **must be excluded** from version control.

Recommended `.gitignore` entry:
```gitignore
.streamlit/secrets.toml
