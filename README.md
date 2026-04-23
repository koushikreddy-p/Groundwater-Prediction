# AquaWatch AI — Groundwater Monitoring System

AquaWatch AI is a real-time groundwater monitoring dashboard built using Python, Tkinter, and Matplotlib. It simulates an IoT-based sensor network and uses AI-driven predictions to monitor and forecast water conditions.

---

## Features

- **Live Dashboard**
  - Real-time monitoring of water level, pH, turbidity, and temperature
  - Dynamic charts with rolling data updates

- **Sensor Simulation**
  - Multiple virtual sensors across different locations
  - Continuous data updates every few seconds

- **AI Forecasting**
  - Predicts future water levels using linear regression
  - Displays confidence band for predictions

- **Alert System**
  - Detects critical and low water conditions
  - Maintains real-time alert logs with timestamps

- **Data Visualization**
  - Interactive charts using Matplotlib
  - Multi-metric comparison and trend analysis

- **Modern UI**
  - Clean dark-themed interface
  - Tab-based navigation for better user experience

---

## Tech Stack

- **Python**
- **Tkinter (GUI)**
- **Matplotlib (Visualization)**
- **NumPy (Data Processing)**

---

## Project Structure

AquaWatch-AI/

│── main.py # Main application

│── data.xlsx # Sample dataset (optional)

│── README.md # Documentation


---

## Installation & Setup

bash
git clone https://github.com/koushikreddy-p/Groundwater-Prediction.git
cd AquaWatch-AI
pip install -r requirements.txt
python main.py


## How It Works

- Sensors generate simulated groundwater data
- Data is stored in rolling history buffers
- AI model predicts future values based on trends
- Alerts are triggered for abnormal conditions
- Dashboard updates automatically every 3 seconds


## Use Cases

- Smart water resource monitoring
- Environmental data analysis systems
- IoT + AI demonstration projects
- Final-year engineering projects


## Future Improvements

- Integration with real IoT devices (Arduino, Raspberry Pi)
- Advanced machine learning models (LSTM, ARIMA)
- Cloud-based storage (Firebase, AWS)
- Web version using React + APIs

## Contributing

Contributions are welcome! Feel free to fork the repo and submit a pull request.

## License

This project is open-source and available under the MIT License.
