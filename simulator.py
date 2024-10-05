import random
import time
import threading
from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Gauge

# Initialize the Flask app
app = Flask(__name__)

# Initialize Prometheus metrics for the app
metrics = PrometheusMetrics(app)

# Define custom Prometheus gauges to track energy consumption and energy price
energy_consumption_metric = Gauge('energy_consumption_metric', 'Randomly generated energy consumption point with seasonality')
energy_price_metric = Gauge('energy_price_metric', 'Randomly generated energy price point with seasonality')

# Function to generate energy consumption data with seasonality
def generate_energy_consumption_with_seasonality():
    base_range_min = 1.0
    base_range_max = 10.0
    increment_value = 20.0
    max_value = 500.0  # Max value for energy consumption
    min_value = 0.0    # Min value for energy consumption
    duration_seconds = 60  # 60 seconds for increasing and decreasing phases

    current_value = 0.0  # Start from 0
    increasing = True   # Start with the increasing phase

    while True:
        start_time = time.time()  # Get the start time for the current phase

        while time.time() - start_time < duration_seconds:
            # Generate a random float between the base range
            random_value = random.uniform(base_range_min, base_range_max)

             # ------------------  Adding anomalies -------------------------

            # # Generate a random float between the base range
            
            # anomaly = random.uniform(1000, 2000)
            # energy_consumption_metric.set(anomaly)
            # continue

            # -------------------------------end anomaly---------------------

            if increasing:
                # Increment the current value by random_value + increment_value
                current_value += random_value + increment_value
                
                # Check if the current value exceeds the maximum limit
                if current_value >= max_value:
                    current_value = max_value  # Cap the value to the maximum limit
                    break  # Stop increasing once we hit the max
            else:
                # Decrement the current value by random_value + increment_value
                current_value -= random_value + increment_value
                
                # Ensure the value does not go below the minimum limit
                if current_value <= min_value:
                    current_value = min_value  # Cap the value to the minimum limit
                    break  # Stop decreasing once we hit the minimum

            # Update the Prometheus gauge with the generated data point
            energy_consumption_metric.set(current_value)

            # Wait for 2 seconds before generating the next data point
            time.sleep(2)

        # Switch between increasing and decreasing phases after 60 seconds
        increasing = not increasing

# Function to generate energy price data with similar seasonality logic
def generate_energy_price_with_seasonality():
    base_range_min = 10.0
    base_range_max = 20.0
    increment_value = 50.0
    max_value = 1000.0  # Max value for energy price
    min_value = 10.0    # Min value for energy price
    duration_seconds = 60  # 60 seconds for increasing and decreasing phases

    current_value = 10.0  # Start from 10 (min_value)
    increasing = True     # Start with the increasing phase

    while True:
        start_time = time.time()  # Get the start time for the current phase

        while time.time() - start_time < duration_seconds:
            # Generate a random float between the base range
            random_value = random.uniform(base_range_min, base_range_max)

            # ------------------  Adding anomalies -------------------------

            
            # # Generate a random float between the base range
            # anomaly = random.uniform(2000, 3000)
            # energy_price_metric.set(anomaly)
            # continue

            # -------------------------------end anomaly---------------------
            if increasing:
                # Increment the current value by random_value + increment_value
                current_value += random_value + increment_value
                
                # Check if the current value exceeds the maximum limit
                if current_value >= max_value:
                    current_value = max_value  # Cap the value to the maximum limit
                    break  # Stop increasing once we hit the max
            else:
                # Decrement the current value by random_value + increment_value
                current_value -= random_value + increment_value
                
                # Ensure the value does not go below the minimum limit
                if current_value <= min_value:
                    current_value = min_value  # Cap the value to the minimum limit
                    break  # Stop decreasing once we hit the minimum

            # Update the Prometheus gauge with the generated data point
            energy_price_metric.set(current_value)

            # Wait for 2 seconds before generating the next data point
            time.sleep(2)

        # Switch between increasing and decreasing phases after 60 seconds
        increasing = not increasing

# Function to run the data generation for energy consumption and energy price in the background
def start_data_generation():
    thread_consumption = threading.Thread(target=generate_energy_consumption_with_seasonality)
    thread_price = threading.Thread(target=generate_energy_price_with_seasonality)

    # Daemonize the threads so they exit when the main program does
    thread_consumption.daemon = True
    thread_price.daemon = True

    # Start the threads
    thread_consumption.start()
    thread_price.start()

if __name__ == '__main__':
    # Start generating data in the background
    start_data_generation()
    # Run the Flask app
    app.run( host='0.0.0.0',port=5000)

