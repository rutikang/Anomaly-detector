import sys
import json
import pandas as pd
import requests
import time
from prophet import Prophet
from datetime import datetime
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from prometheus_client import start_http_server, Gauge

# Get command-line arguments using sys.argv
if len(sys.argv) < 4:
    print("Usage: python monitor.py <metric_type> <train_data_path> <port>")
    sys.exit(1)

metric_type = sys.argv[1]  # First argument is the metric type (e.g., energy_consumption or energy_price)
train_data_path = sys.argv[2]  # Second argument is the path to the training data file
port = int(sys.argv[3])  # Third argument is the port for Prometheus metrics


# Start Prometheus metrics server
start_http_server(port)

# Dynamically create Prometheus metrics based on the metric type
anomaly_count = Gauge(f'{metric_type}_anomaly_count', f'Number of anomalies detected in {metric_type}')
mae_metric = Gauge(f'{metric_type}_mae', f'Mean Absolute Error in {metric_type}')
mape_metric = Gauge(f'{metric_type}_mape', f'Mean Absolute Percentage Error in {metric_type}')

y_min_metric = Gauge(f'{metric_type}_y_min', f'Minimum value of the current {metric_type} datapoint')
y_metric = Gauge(f'{metric_type}_y', f'Observed value of the current {metric_type} datapoint')
y_max_metric = Gauge(f'{metric_type}_y_max', f'Maximum value of the current {metric_type} datapoint')

# Load training data
with open(train_data_path, "r") as f:
    train_data = json.load(f)

df_train = pd.DataFrame(train_data['data']['result'][0]['values'])
df_train.columns = ['ds', 'y']
df_train['ds'] = df_train['ds'] - df_train['ds'].iloc[0]
df_train['ds'] = df_train['ds'].apply(lambda sec: datetime.fromtimestamp(sec))
df_train['y'] = df_train['y'].astype(float)

# Initialize and train the Prophet model
model = Prophet(interval_width=0.99, yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False, growth='flat')
model.add_seasonality(name='hourly', period=1/24, fourier_order=5)
model.fit(df_train)

# Prometheus query URL
prometheus_url = "http://localhost:9090/api/v1/query"

# Set the Prometheus metric name dynamically based on metric type
metric_name = f"{metric_type}_metric"

def get_test_data():
    """Fetches the test data from Prometheus."""
    query = f"{metric_name}[1m]"  
    query_url = f"{prometheus_url}?query={query}"
    
    response = requests.get(query_url)
    result = response.json()
    
    try:
        values = result['data']['result'][0]['values']  # This will return a list of [timestamp, value]
        return values
    except (KeyError, IndexError):
        print("No data found for the metric.")
        return []

test_start_time = time.time()

print("Timestamp                  Anomalies  MAE                 MAPE")

while True:
    try:
        # Get the test data from Prometheus
        test_values = get_test_data()
        
        if test_values:
            # Convert Prometheus response into a DataFrame
            df_test = pd.DataFrame(test_values, columns=['ds', 'y'])
            df_test['ds'] = df_test['ds'].astype(float) - test_start_time  # Reset to 0 origin
            df_test['ds'] = df_test['ds'].apply(lambda sec: datetime.fromtimestamp(sec))
            df_test['y'] = df_test['y'].astype(float)

            # Make predictions using the Prophet model
            forecast = model.predict(df_test)

            # Merge actual and predicted values
            performance = pd.merge(df_test, forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], on='ds')

            # Capture y_min, y, and y_max values for the most recent datapoint
            y_min = performance['yhat_lower'].iloc[-1]
            y = performance['y'].iloc[-1]
            y_max = performance['yhat_upper'].iloc[-1]

            # Set Prometheus metrics for y_min, y, and y_max
            y_min_metric.set(y_min)
            y_metric.set(y)
            y_max_metric.set(y_max)

            # Calculate MAE and MAPE
            performance_MAE = mean_absolute_error(performance['y'], performance['yhat'])
            performance_MAPE = mean_absolute_percentage_error(performance['y'], performance['yhat'])

            # Set the Prometheus Gauge metrics for MAE and MAPE
            mae_metric.set(performance_MAE)
            mape_metric.set(performance_MAPE)

            # Create an anomaly indicator
            performance['anomaly'] = performance.apply(lambda row: 1 if (row['y'] < row['yhat_lower'] or row['y'] > row['yhat_upper']) else 0, axis=1)

            # Check the number of anomalies
            anomaly_count.set(performance['anomaly'].sum())  # Set the Prometheus gauge metric

            # Print results in the desired format
            print(f"{datetime.now()}    {performance['anomaly'].sum()}     {performance_MAE}   {performance_MAPE}")

    except Exception as e:
        print(f'Error:: {str(e)}')

    # Sleep for 10 seconds before the next iteration
    time.sleep(10)
