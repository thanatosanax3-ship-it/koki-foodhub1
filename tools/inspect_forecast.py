import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','koki_foodhub.settings')
import django
django.setup()
from core.services.forecasting import aggregate_sales, forecast_time_series, moving_average_forecast
from core.services.csv_forecasting import csv_aggregate_series
from pprint import pprint

print('CSV aggregates (daily last 10):')
try:
    c = csv_aggregate_series(limit=100)
    pprint({k:v[-10:] for k,v in c.items()})
except Exception as e:
    print('csv_aggregate_series error:', e)

print('\nDB per-product moving-average forecasts (sample):')
try:
    prod = moving_average_forecast(window=3)
    pprint({k: { 'forecast': v.get('forecast'), 'avg': v.get('avg'), 'history_len': len(v.get('history', [])) } for k,v in list(prod.get('db_forecasts', {}).items())[:6]})
except Exception as e:
    print('moving_average_forecast error:', e)

print('\nDB aggregates (daily last 10):')

print('\nDB daily series (last 10):')
d = aggregate_sales('daily', lookback=10)
print(d)
print('\nForecast (daily -> horizon 7):')
print(forecast_time_series(d, horizon=7))

print('\nDB weekly series (last 6):')
w = aggregate_sales('weekly', lookback=6)
print(w)
print('\nForecast (weekly -> horizon 6):')
print(forecast_time_series(w, horizon=6))

print('\nDB monthly series (last 6):')
m = aggregate_sales('monthly', lookback=6)
print(m)
print('\nForecast (monthly -> horizon 6):')
print(forecast_time_series(m, horizon=6))
