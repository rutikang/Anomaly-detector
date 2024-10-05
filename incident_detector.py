import time
from prometheus_client import start_http_server, Gauge
from datetime import datetime
import requests

# Prometheus metrics
start_http_server(8110)  
temperature_metric = Gauge('incident_temperature', 'Current sum of accumulators for energy metrics')
sev1_metric = Gauge('incident_sev1', 'Sev 1 Incident - Both metrics')
sev2_metric = Gauge('incident_sev2', 'Sev 2 Incident - One metric')

# Accumulator thresholds and decay
threshold = 10  # Threshold for triggering severe incidents
decay_value = 5  # Decay value for reducing accumulators

# Initial accumulators for energy consumption and energy price
accumulator_energy_consumption = 0
accumulator_energy_price = 0

# Prometheus query URLs
prometheus_url = "http://localhost:9090"  
energy_consumption_query = "energy_consumption_anomaly_count"  
energy_price_query = "energy_price_anomaly_count"  

# Initialize Sev 1 and Sev 2 metrics to 0
sev1_metric.set(0)
sev2_metric.set(0)

while True:
    try:
        # Fetch anomaly count data from Prometheus for energy consumption
        energy_consumption_anomaly_count = float(
            requests.get(f"{prometheus_url}/api/v1/query?query={energy_consumption_query}").json()['data']['result'][0]['value'][1]
        )
        
        # Fetch anomaly count data from Prometheus for energy price
        energy_price_anomaly_count = float(
            requests.get(f"{prometheus_url}/api/v1/query?query={energy_price_query}").json()['data']['result'][0]['value'][1]
        )

        # Add anomalies to accumulators
        accumulator_energy_consumption += energy_consumption_anomaly_count
        accumulator_energy_price += energy_price_anomaly_count

        # Decay accumulators if no anomalies detected
        if energy_consumption_anomaly_count == 0:
            accumulator_energy_consumption = max(0, accumulator_energy_consumption - decay_value)
        if energy_price_anomaly_count == 0:
            accumulator_energy_price = max(0, accumulator_energy_price - decay_value)

        # Calculate the sum of accumulators (Temperature) with an upper limit of 20
        incident_temperature = min(accumulator_energy_consumption + accumulator_energy_price, 20)

        # Set Prometheus metrics
        temperature_metric.set(incident_temperature)

        # Check for incidents and trigger alerts
        if incident_temperature >= threshold:
            if accumulator_energy_consumption > 0 and accumulator_energy_price > 0:
                sev1_metric.set(1)
                sev2_metric.set(0)  # Reset Sev 2
                print(f"{datetime.now()} - Sev 1 Incident - Both metrics have anomalies", flush=True)
            elif accumulator_energy_consumption > 0 or accumulator_energy_price > 0:
                sev1_metric.set(0)  # Reset Sev 1
                sev2_metric.set(1)
                print(f"{datetime.now()} - Sev 2 Incident - One metric has anomalies", flush=True)
        else:
            # Reset Sev 1 and Sev 2 if below the threshold
            sev1_metric.set(0)
            sev2_metric.set(0)

        # Print information for debugging
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("\n")
        print(f"{timestamp} - Energy Consumption Anomaly: {energy_consumption_anomaly_count}, Energy Price Anomaly: {energy_price_anomaly_count}")

        print(f"{timestamp} - Temperature: {incident_temperature}, Sev 1: {sev1_metric._value.get()}, Sev 2: {sev2_metric._value.get()}", flush=True)
    
    except Exception as e:
        print(f'Error: {str(e)}')

    # Sleep for 5 seconds before the next iteration
    time.sleep(5)
