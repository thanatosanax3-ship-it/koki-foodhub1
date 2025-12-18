from datetime import date, timedelta
import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

"""Legacy CSV-based forecasting helpers.
These are kept separate from `forecasting.py` so the main forecasting
pipeline can rely only on DB historical sales. Management commands and
ad hoc tools that still need CSV processing can import from here.
"""


def load_csv_data(csv_path=None):
    """Load sales data from CSV file"""
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), '../../pizzaplace.csv')
    if not os.path.exists(csv_path):
        return None
    try:
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None


def csv_aggregate_series(limit=100):
    """Return aggregated series (daily, weekly, monthly) computed from the CSV.
    Limit to the most recent `limit` rows in the CSV to keep processing bounded.
    Returns dict with keys 'daily', 'weekly', 'monthly' where each value is a list of
    (label, units) tuples ordered chronologically (oldest -> newest).
    """
    df = load_csv_data()
    if df is None or df.empty:
        return {'daily': [], 'weekly': [], 'monthly': []}

    # Ensure date column is datetime and sort by date
    df = df.sort_values('date')

    # Limit to `limit` most recent rows
    if limit is not None:
        df = df.tail(limit)

    # DAILY: count rows per date
    daily = df.groupby(df['date'].dt.date).size().reset_index(name='units')
    # Fill missing days between min and max date with zeros for nicer charts
    min_d = daily['date'].min()
    max_d = daily['date'].max()
    all_dates = pd.date_range(start=min_d, end=max_d, freq='D')
    daily = daily.set_index('date').reindex(all_dates, fill_value=0).rename_axis('date').reset_index()
    daily_series = [(row['date'].date().isoformat(), int(row['units'])) for _, row in daily.iterrows()]

    # WEEKLY: group by week starting Monday
    df_week = df.copy()
    df_week['week_start'] = df_week['date'].dt.to_period('W').apply(lambda r: r.start_time.date())
    weekly = df_week.groupby('week_start').size().reset_index(name='units')
    weekly_series = [(row['week_start'].isoformat(), int(row['units'])) for _, row in weekly.iterrows()]

    # MONTHLY: group by year-month
    df_month = df.copy()
    df_month['month'] = df_month['date'].dt.to_period('M').apply(lambda r: r.start_time.date())
    monthly = df_month.groupby('month').size().reset_index(name='units')
    monthly_series = [(row['month'].strftime('%Y-%m'), int(row['units'])) for _, row in monthly.iterrows()]

    return {'daily': daily_series, 'weekly': weekly_series, 'monthly': monthly_series}


def get_csv_forecast(csv_path=None, limit=100):
    """
    Train ML model on CSV data and return forecasts for each product.

    By default this function limits processing to the most recent 100 rows of the CSV
    (to keep production CPU/memory bounded). Pass a different `limit` to override.

    Returns dict: product_name -> { 'forecast': units, 'trend': str, 'confidence': float, 'history': [...] }
    """
    df = load_csv_data(csv_path)
    if df is None:
        return {}
    # Limit to most recent `limit` rows to keep processing bounded
    if limit is not None:
        try:
            df = df.sort_values('date').tail(limit)
        except Exception:
            pass

    results = {}

    # Group by product name
    for product_name, group in df.groupby('name'):
        # Count units sold per day
        daily_sales = group.groupby('date').size().reset_index(name='units')
        if len(daily_sales) < 3:
            continue
        X = np.arange(len(daily_sales)).reshape(-1, 1)
        y = daily_sales['units'].values
        model = LinearRegression()
        model.fit(X, y)
        next_day = np.array([[len(daily_sales)]])
        forecast = max(1, int(model.predict(next_day)[0]))
        slope = model.coef_[0]
        if slope > 0.5:
            trend = "increasing"
        elif slope < -0.5:
            trend = "decreasing"
        else:
            trend = "stable"
        r_squared = model.score(X, y)
        confidence = 0.0 if r_squared < 0 else round(r_squared * 100, 2)
        if confidence == 0 and len(daily_sales) >= 3:
            variance = float(y.var())
            mean = float(y.mean())
            if mean > 0:
                coefficient_of_variation = variance / (mean ** 2)
                consistency_score = max(10.0, 100.0 - (coefficient_of_variation * 50))
                confidence = min(85.0, consistency_score)
            else:
                confidence = 10.0
        history = daily_sales.tail(7).values.tolist()
        if confidence >= 70:
            accuracy = 'High'
        elif confidence >= 40:
            accuracy = 'Medium'
        else:
            accuracy = 'Low'

        results[product_name] = {
            'forecast': forecast,
            'trend': trend,
            'confidence': confidence,
            'accuracy': accuracy,
            'history': history,
            'avg': float(y.mean()),
            'last_7_days': int(y[-7:].sum())
        }

    return results
