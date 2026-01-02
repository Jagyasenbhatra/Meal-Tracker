# 🍽️ Meal-Tracker

A simple **Streamlit-based Meal Tracking application** that helps you record daily meals, calculate costs, and manage records easily.
All data is stored locally using **SQLite**, so no external database setup is required.

---

## ✨ Features

* 📅 Track meals **per day**
* 🔄 Two meal entry modes:

  * **Auto**: Lunch + Dinner
  * **Manual**: Total meals directly
* 💰 Automatic meal cost calculation
* 💾 Save records to a local database (`meals.db`)
* ✏️ Edit existing records
* 🗑 Delete records by date
* 🔄 Reset input form without deleting data
* 📊 View all saved records in a table
* ⚡ No external DB, works offline

---

## 🛠️ Tech Stack

* **Python 3.9+**
* **Streamlit** – UI framework
* **SQLite** – Local database
* **Pandas** – Data handling

---

## 📂 Project Structure

```
Meal-Tracker/
│── app.py
│── meals.db          # Auto-created SQLite database
│── requirements.txt
│── README.md
```

---

## 🚀 Installation & Run

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Jagyasenbhatra/Meal-Tracker.git
cd Meal-Tracker
```

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

1. Select a **date**
2. Choose meal mode:

   * **Auto** → Enter Lunch & Dinner counts
   * **Manual** → Enter total meals directly
3. Enter **price per meal**
4. Click **Save Record**
5. View, **edit**, or **delete** records anytime
6. Use **Reset** to clear inputs (data remains safe)

---

## 🧠 Database Details

* Uses **SQLite**
* Stored as a single file: `meals.db`
* Automatically created on first run
* Easy to back up or move (just copy the file)

---

## 📦 Requirements

```txt
streamlit>=1.31.0
pandas>=1.5.0
```

> `sqlite3` and `datetime` are included with Python by default.

---

## 🔒 Notes

* Deleting a record is **per-day**, not the entire database
* Reset button does **not** delete saved data
* No internet connection required after installation

---

## 🔮 Future Enhancements (Optional)

* 📆 Monthly summary & reports
* 📤 Export to Excel / CSV
* 👥 Multi-user or person-wise tracking
* 🔐 Authentication
* ☁️ Cloud database support

---

## 👨‍💻 Author

Built with ❤️ using Streamlit
Feel free to extend or customize as needed.

