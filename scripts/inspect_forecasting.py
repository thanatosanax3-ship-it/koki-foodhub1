import importlib
try:
    m = importlib.import_module('core.services.forecasting')
    print('loaded forecasting module')
    print('forecast_time_series' in dir(m))
    print('moving_average_forecast' in dir(m))
    print('product_forecast_summary' in dir(m))
except Exception as e:
    import traceback
    traceback.print_exc()