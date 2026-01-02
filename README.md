You’re right — your README is **almost perfect**, it just needs to reflect the **latest features you’ve already implemented** (charts, monthly summary, export, feedback system).

Below is the **clean, updated README**, same tone, no over-engineering, just accurate.

---

```md
# 🍽️ Meal-Tracker

A simple **Streamlit-based Meal Tracking application** that helps you record daily meals, calculate costs, and manage records **per person**.
All data is stored locally using **SQLite**, so no external database setup is required.

---

## ✨ Features

- 👤 **Person-wise meal tracking** (name-based)
- 📅 Track meals **per day**
- 🔄 Two meal entry modes:
  - **Auto**: Lunch + Dinner
  - **Manual**: Total meals directly
- 💰 Automatic meal cost calculation
- 💾 Save records to a local SQLite database (`meals.db`)
- 📊 View all saved records in a table (per person)
- 🧮 **Total meals & total amount summary** from saved records
- ✏️ Edit existing records
- 🗑 Delete records (per day, per person)
- 🔄 Reset input form without deleting saved data
- 📊 **Charts (Meals vs Date)**
- 📆 **Monthly summary & reports (per person)**
- 📤 **Export data to CSV & Excel**
- 📝 **Feedback system** (name-based feedback for feature requests / issues)
- ⚡ No external DB, works fully offline

---

## 🛠️ Tech Stack

- **Python 3.9+**
- **Streamlit** – UI framework
- **SQLite** – Local file-based database
- **Pandas** – Data handling and aggregation
- **openpyxl** – Excel export support

---

## 📂 Project Structure

```

Meal-Tracker/
│── app.py
│── meals.db          # Auto-created SQLite database
│── requirements.txt
│── README.md

````

---

## 🚀 Installation & Run

### 1️⃣ Clone the repository
```bash
git clone https://github.com/Jagyasenbhatra/Meal-Tracker.git
cd Meal-Tracker
````

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the app

```bash
streamlit run app.py
```

---

## 📋 How to Use

1. Enter **Person Name** (required)
2. Select a **date**
3. Choose meal mode:

   * **Auto** → Enter Lunch & Dinner counts
   * **Manual** → Enter total meals directly
4. Enter **price per meal**
5. Click **Save Record**
6. View saved records for that person
7. See **total meals & total amount** summary
8. View **charts** and **monthly reports**
9. **Edit** or **delete** any record as needed
10. Export data to **CSV / Excel**
11. Submit **feedback or feature requests**
12. Use **Reset** to clear the form (saved data remains safe)

---

## 🧠 Database Details

* Uses **SQLite**
* Stored as a single file: `meals.db`
* Automatically created on first run
* Supports schema migration (safe updates)
* Includes separate tables for:

  * Meal records
  * User feedback
* Easy to back up or move (just copy the file)

---

## 📦 Requirements

```txt
streamlit>=1.31.0
pandas>=1.5.0
openpyxl>=3.1.0
```

> `sqlite3`, `datetime`, and `io` are included with Python by default.

---

## 🔒 Notes

* Records are **isolated per person**
* Edit/Delete operations are **safe and ID-based**
* Reset button clears only the input fields
* Feedback is stored separately and can be reviewed by developers
* No internet connection required after installation
* Suitable for personal use or small teams

---

## 🔮 Future Enhancements (Optional)

* 📅 Date-range filtering
* 📊 Additional charts (bar / pie)
* 🧾 Bill / invoice generation (PDF)
* 👥 Person dropdown selection
* 🔐 Authentication / login
* ☁️ Cloud database support
* 📧 Feedback notifications for developers

---

## 👨‍💻 Author

Built with ❤️ using **Streamlit**
Feel free to fork, extend, and customize as needed.

```


