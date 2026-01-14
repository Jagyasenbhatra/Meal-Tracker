# 🔐 Security Policy

This document outlines the security practices, supported versions, and vulnerability
reporting process for the **Meal Tracker** application.

---

## 📦 Supported Versions

Only the **latest version** of the application is actively supported with security updates.

| Version | Supported |
|--------|-----------|
| Latest | ✅ Yes |
| Older | ❌ No |

Always use the most recent version to receive security fixes and improvements.

---

## 🔒 Security Practices

### 1️⃣ Secrets Management
- Sensitive credentials **must not** be hard-coded in the source code.
- The application uses **Streamlit Secrets** via `.streamlit/secrets.toml` for:
  - `MONGO_URI`
  - `ADMIN_PASSWORD`
- This file **must never be committed** to version control.

Recommended `.gitignore` entry:
```gitignore
.streamlit/secrets.toml
