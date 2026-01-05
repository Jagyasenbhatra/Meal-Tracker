# 🍽️ Meal Tracker

A **Streamlit-based Meal Tracking application** that helps you record daily meals, calculate costs, and manage records **per person**.

The app now uses **MongoDB** for storage, making it scalable, schema-flexible, and cloud-ready while keeping the UI simple and fast.

---

## ✨ Features

* 👤 **Person-wise meal tracking** (name-based)
* 📅 Track meals **per day**
* 🔄 Two meal entry modes:

  * **Auto**: Lunch + Dinner
  * **Manual**: Total meals directly
* 💰 Automatic meal cost calculation
* 💾 Store data in **MongoDB** (local or cloud – MongoDB Atlas)
* 📊 View all saved records in a table (per person)
* 🧮 **Total meals & total amount summary**
* 📆 **Month-wise filtering & reports**
* 📊 **Charts (Meals vs Date)**
* ✏️ Edit existing records (ID-based)
* 🗑 Delete records safely
* 📤 **Export data to CSV & Excel**
* 📝 **Feedback system** (user feedback with ratings)
* 🔐 **Admin feedback panel** (password protected)
* 🔄 Reset input form without deleting saved data

---

## 🛠️ Tech Stack

* **Python 3.9+**
* **Streamlit** – UI framework
* **MongoDB** – NoSQL database
* **PyMongo** – MongoDB client
* **Pandas** – Data handling & aggregation
* **openpyxl** – Excel export support

---

## 📂 Project Structure

```
Meal-Tracker/
│── app.py                  # Main Streamlit app
│── db_connection.py        # MongoDB connection
│── requirements.txt
│── README.md
│── .streamlit/
│   └── secrets.toml        # Mongo URI & admin password
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

### 3️⃣ Configure secrets

Create `.streamlit/secrets.toml`:

```toml
MONGO_URI = ""
ADMIN_PASSWORD = ""
```

> You can use **MongoDB Atlas (free tier)** or a local MongoDB instance.

---

### 4️⃣ Run the app

```bash
streamlit run app.py
```

---

## 📋 How to Use

1. Enter **Person Name** (required)
2. Select a **date**
3. Choose meal mode:

   * **Auto** → Enter Lunch & Dinner
   * **Manual** → Enter total meals
4. Enter **price per meal**
5. Click **Save Record**
6. View saved records for that person
7. Check **total meals & total amount**
8. Use **monthly filter** to view reports
9. Edit or delete any record
10. Export data to **CSV / Excel**
11. Submit **feedback**
12. Admin can view/delete feedback via **Admin Panel**

---

## 🧠 Database Details

* Uses **MongoDB**
* Collections:

  * `meals`
  * `feedback`
* No schema migrations required
* Date stored in ISO format
* Fully scalable & cloud-ready
* Works well with multi-user setups

---

## 📦 Requirements

```txt
streamlit>=1.31.0
pandas>=1.5.0
pymongo>=4.6.0
openpyxl>=3.1.0
```

---

## 🔒 Notes

* Records are **isolated per person**
* Edit/Delete operations are **ObjectId-based**
* Reset clears only form inputs
* Feedback is stored separately
* Admin access is password-protected
* Suitable for personal use or small teams
* MongoDB Atlas enables cloud usage

---

## 🔮 Future Enhancements

* 📅 Date-range filtering
* 📊 Advanced charts (bar / pie)
* 🧾 PDF bill / invoice generation
* 👥 Person dropdown selection
* 🔐 User authentication
* ☁️ Role-based access
* 📧 Email notifications for feedback
* 📊 MongoDB aggregation-based analytics


## 👨‍💻 Author

Developed by **Jagyasen**
Backend Engineer | Python | Streamlit | Databases
