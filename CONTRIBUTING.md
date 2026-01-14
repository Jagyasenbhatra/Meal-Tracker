# 🤝 Contributing to Meal Tracker

Thank you for your interest in contributing to **Meal Tracker**!  
We welcome contributions that improve features, fix bugs, enhance performance, or improve documentation.

Please take a moment to read this guide before contributing.

---

## 📌 Step 1: Fork the Repository

1. Go to the GitHub repository
2. Click the **Fork** button (top-right)
3. Clone your fork locally:

```bash
git clone https://github.com/Jagyasenbhatra/Meal-Tracker.git
cd Meal-Tracker
````

---

## 🛠 Step 2: Set Up the Project Locally

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure secrets

Create `.streamlit/secrets.toml`:

```toml
MONGO_URI = ""
ADMIN_PASSWORD = ""
```

> ⚠️ Never commit secrets to the repository.

### Run the application

```bash
streamlit run app.py
```

Verify:

* App loads successfully
* MongoDB connection works
* Records can be saved and viewed

---

## 🌱 Step 3: Create a Feature Branch

Always create a new branch before making changes.

```bash
git checkout -b feature/your-feature-name
```

Branch naming examples:

* `feature/monthly-report`
* `bugfix/export-error`
* `docs/security-update`

---

## ✍️ Step 4: Make Your Changes

While coding, ensure:

* Code is clean and readable
* Functions are small and well-structured
* Logging is added for major actions
* No credentials or secrets are added
* MongoDB operations are scoped and safe

If adding a feature:

* Keep UI simple and intuitive
* Reuse existing logic where possible
* Update documentation if needed

---

## 🧪 Step 5: Test Your Changes

Before committing:

* Test create, edit, and delete flows
* Verify CSV / Excel export
* Check monthly filtering
* Ensure logs don’t expose sensitive data

Manual testing is required for all changes.

---

## 📝 Step 6: Commit Your Work

Write clear and meaningful commit messages:

```bash
git commit -m "Add month-wise meal summary report"
```

Avoid:

* `fix bug`
* `update code`
* `changes made`

---

## 🔀 Step 7: Push & Create a Pull Request

Push your branch:

```bash
git push origin feature/your-feature-name
```

Then:

1. Open a Pull Request (PR)
2. Target the `main` branch
3. Clearly describe:

   * What you changed
   * Why it’s needed
   * Screenshots (if UI-related)

---

## 🔒 Security Reporting

If you find a security issue:

* ❌ Do NOT open a public issue
* ✅ Follow instructions in `SECURITY.md`

---

## 📜 Code Style Guidelines

* Follow PEP8 standards
* Use meaningful variable and function names
* Avoid deeply nested logic
* Add comments where logic is complex

---

## 🙌 Code of Conduct

All contributors must follow the **Code of Conduct**.
See `CODE_OF_CONDUCT.md` for details.

---

Thank you for contributing to **Meal Tracker** 🚀
Your help makes the project better for everyone.
