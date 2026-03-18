# 🌾 Smart Farm IoT Data Pipeline

## 🚀 Project Overview

This project simulates a real-time data engineering pipeline for smart farming using IoT data and weather integration.

It demonstrates how data flows from sensors to a dashboard in real time.

---

## 🧱 Architecture

Sensor Data → MQTT → Python → Weather API → SQLite → Streamlit Dashboard

---

## ⚙️ Tech Stack

* Python
* MQTT (Mosquitto)
* SQLite
* Streamlit
* Open-Meteo API

---

## 📊 Features

* Real-time data streaming
* Data ingestion pipeline
* Weather API integration
* Database storage
* Interactive dashboard
* Smart alerts (dry soil, high temperature)
* Data export (CSV)

---

## ▶️ How to Run

1. Start Mosquitto

2. Run sensor:
   python sensor.py

3. Run ingestion:
   python ingest.py

4. Run dashboard:
   streamlit run dashboard.py

---

## 📸 Output

* Live dashboard with charts
* Real-time data updates
* Smart alerts

---

## 💡 Learning Outcome

* Built an end-to-end data pipeline
* Learned real-time data streaming
* Integrated APIs into workflows
* Developed dashboard for data visualization

---

## 🚀 Future Improvements

* Add machine learning predictions
* Deploy on cloud (AWS/Azure)
* Add real IoT devices

---
