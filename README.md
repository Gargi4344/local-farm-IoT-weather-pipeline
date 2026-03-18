# Local Farm IoT and Weather Pipeline

This project simulates a farm sensor, ingests MQTT readings into SQLite, and presents a polished Streamlit control center for live monitoring.

## Files

- `sensor.py`: publishes simulated soil moisture and temperature readings to MQTT
- `ingest.py`: subscribes to MQTT, enriches readings with outdoor weather, and stores them in `farm.db`
- `dashboard.py`: Streamlit dashboard for live operations, alerts, and trend analysis
- `farm.db`: local SQLite database created by the ingestion service

## Run Order

1. Start the Mosquitto broker
   - `mosquitto -v`
2. Start ingestion
   - `python ingest.py`
3. Start the simulator
   - `python sensor.py`
4. Launch the dashboard
   - `streamlit run dashboard.py`

## Optional Sensor Arguments

- `python sensor.py --interval 2`
- `python sensor.py --host localhost --port 1883 --topic farm/sensor`

## Notes

- The ingestion service uses Open-Meteo for current outdoor weather and falls back gracefully if the lookup fails.
- The dashboard auto-refreshes its data cache every 15 seconds.
