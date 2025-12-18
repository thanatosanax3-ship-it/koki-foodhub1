from datetime import date, timedelta
from collections import defaultdict
import os
import logging
from ..models import Sale, Product
from django.db.models import Sum
from datetime import datetime
from dateutil.relativedelta import relativedelta

# NOTE: numpy, pandas and scikit-learn are optional runtime dependencies used
# for CSV-based helpers and linear-regression forecasts. Importing them at
# module import time caused some deployed instances to raise ImportError and
# produce a Server Error (500) when those packages weren't available. To be
# resilient we import heavy numeric libs only inside the functions that need
# them and provide safe fallbacks when they're missing.
logger = logging.getLogger(__name__)

# Cap per-sale units so single bad rows don't dominate forecasts
MAX_UNITS_PER_SALE = 100

def load_csv_data(csv_path=None):
    """Load sales data from CSV file"""
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), '../../pizzaplace.csv')
    
    if not os.path.exists(csv_path):
        return None
    
    try:
        # Import pandas only when CSV helpers are invoked
        import pandas as pd
    except Exception as exc:  # pragma: no cover - environment-dependent
        logger.exception('Pandas unavailable; CSV helpers disabled: %s', exc)
        return None

    try:
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        logger.exception('Error loading CSV: %s', e)
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
    # Try to import numeric libs lazily; if they're not present return empty results
    try:
        import numpy as np
        from sklearn.linear_model import LinearRegression
    except Exception as exc:  # pragma: no cover - only triggers when libs absent
        logger.exception('Numeric libs unavailable for CSV forecasting: %s', exc)
        return {}

    for product_name, group in df.groupby('name'):
        # Count units sold per day
        daily_sales = group.groupby('date').size().reset_index(name='units')
        
        if len(daily_sales) < 3:
            continue
        
        # Prepare training data
        X = np.arange(len(daily_sales)).reshape(-1, 1)
        y = daily_sales['units'].values

        # Train linear regression model
        model = LinearRegression()
        model.fit(X, y)

        # Get forecast for next day
        next_day = np.array([[len(daily_sales)]])
        forecast = max(1, int(model.predict(next_day)[0]))
        
        # Calculate trend
        slope = model.coef_[0]
        if slope > 0.5:
            trend = "increasing"
        elif slope < -0.5:
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Calculate confidence (R² score as percentage, with minimum threshold)
        r_squared = model.score(X, y)
        
        # Convert R² to percentage (0-100)
        # If R² is negative, it means the model is worse than a simple mean, so set to 0
        if r_squared < 0:
            confidence = 0.0
        else:
            confidence = round(r_squared * 100, 2)
        
        # Ensure confidence is never 0 if we have some data (minimum 10% if model performs reasonably)
        if confidence == 0 and len(daily_sales) >= 3:
            # Calculate consistency score based on variance
            variance = float(y.var())
            mean = float(y.mean())
            if mean > 0:
                coefficient_of_variation = variance / (mean ** 2)
                # Lower CV means more consistent = higher confidence
                consistency_score = max(10.0, 100.0 - (coefficient_of_variation * 50))
                confidence = min(85.0, consistency_score)
            else:
                confidence = 10.0
        
        # Get recent history
        history = daily_sales.tail(7).values.tolist()
        # Derive accuracy label
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

def moving_average_forecast(window=3, lookback_days=21):
    """
    Returns dict: product_id -> { 'history': [(date, units)], 'forecast': int, 'avg': float }
    Simple moving average over last `window` sales entries within `lookback_days`.
    Outlier protection: cap per-sale units at `MAX_UNITS_PER_SALE` before averaging so a
    single large sale doesn't dominate the forecast.
    """
    start = date.today() - timedelta(days=lookback_days)
    sales = Sale.objects.filter(date__gte=start).order_by("product_id", "date")
    series = defaultdict(list)

    for s in sales:
        series[s.product_id].append((s.date, s.units_sold))

    results = {}
    for pid, hist in series.items():
        # preserve raw history in results but compute forecast from robust values
        raw_units = [u for _, u in hist]
        if not raw_units:
            continue

        # take the last `window` points (or fewer if not available)
        recent = raw_units[-window:] if len(raw_units) >= window else raw_units

        # Adaptive outlier handling: only apply a cap when there are clear extreme
        # outliers relative to the typical scale for this product. This avoids
        # forcing small-series forecasts up to a fixed value like 100.
        # Use numpy when available for robust stats, otherwise fallback to Python stdlib
        try:
            import numpy as np
            med = float(np.median(raw_units))
            mx = float(max(raw_units))
        except Exception:
            import statistics as stats
            med = float(stats.median(raw_units))
            mx = float(max(raw_units))

        cap = None
        # If the maximum is much larger than the median (suggesting a spike),
        # compute a conservative cap using a high percentile of historical data.
        if med > 0 and mx > med * 10 and mx > MAX_UNITS_PER_SALE:
            try:
                import numpy as np
                p95 = float(np.percentile(raw_units, 95))
                cap = int(max(MAX_UNITS_PER_SALE, round(p95)))
            except Exception:
                # Fallback percentile implementation (approximate using sorted values)
                try:
                    sorted_vals = sorted(raw_units)
                    idx = int(round(0.95 * (len(sorted_vals) - 1)))
                    p95 = float(sorted_vals[idx])
                    cap = int(max(MAX_UNITS_PER_SALE, round(p95)))
                except Exception:
                    cap = MAX_UNITS_PER_SALE

        # Apply cap if determined, otherwise use raw values
        if cap:
            capped = [min(int(u), cap) for u in recent]
        else:
            capped = [int(u) for u in recent]

        # Use trimmed mean when there are at least 3 points for robustness
        if len(capped) >= 3:
            sorted_cap = sorted(capped)
            trimmed = sorted_cap[1:-1]
            avg = sum(trimmed) / len(trimmed) if trimmed else (sum(capped) / len(capped))
        else:
            avg = sum(capped) / len(capped)

        forecast = max(0, int(round(avg)))

        # Estimate simple trend and confidence per-product for richer payloads
        trend = 'stable'
        if len(raw_units) >= 2 and raw_units[-1] > raw_units[0]:
            trend = 'increasing'
        elif len(raw_units) >= 2 and raw_units[-1] < raw_units[0]:
            trend = 'decreasing'

        # Confidence: inverse of dispersion
        try:
            try:
                import numpy as np
                variance = float(np.var(capped))
            except Exception:
                import statistics as stats
                variance = float(stats.pvariance(capped)) if len(capped) > 1 else 0.0
            mean = float(avg) if avg else 0.0
            if mean <= 0:
                confidence = 0.0
            else:
                rel_disp = (variance ** 0.5) / mean
                confidence = max(0.0, min(100.0, (1.0 - rel_disp) * 100.0))
        except Exception:
            confidence = 0.0

        if confidence >= 70:
            accuracy = 'High'
        elif confidence >= 40:
            accuracy = 'Medium'
        else:
            accuracy = 'Low'

        results[pid] = {"history": hist, "forecast": forecast, "avg": avg, "trend": trend, "confidence": round(confidence, 2), "accuracy": accuracy}
    
    return {
        'db_forecasts': results
    }


def aggregate_sales(period='daily', lookback=90):
    """
    Aggregate sales into time series.
    period: 'daily', 'weekly', or 'monthly'
    lookback: number of days (for daily), weeks (for weekly), months (for monthly)
    Returns list of (label, units) ordered chronologically.
    """
    today = date.today()
    series = []

    # Cap suspiciously large per-sale unit counts to avoid single bad rows
    # from skewing aggregated charts (e.g. mis-imported rows with units_sold >> typical values).
    # This caps each *individual* Sale.units_sold at MAX_UNITS_PER_SALE before summing.
    MAX_UNITS_PER_SALE = 100
    from django.db.models import Case, When, Value, IntegerField

    if period == 'daily':
        start = today - timedelta(days=lookback - 1)
        # Initialize dict with zeros
        counts = { (start + timedelta(days=i)): 0 for i in range(lookback) }
        # Annotate using a capped per-row value so extreme outliers don't dominate totals
        qs = Sale.objects.filter(date__gte=start).values('date').annotate(
            total=Sum(Case(
                When(units_sold__gt=MAX_UNITS_PER_SALE, then=Value(MAX_UNITS_PER_SALE)),
                default='units_sold',
                output_field=IntegerField()
            ))
        )
        for row in qs:
            d = row['date']
            counts[d] = counts.get(d, 0) + int(row['total'] or 0)
        for d in sorted(counts.keys()):
            series.append((d.isoformat(), counts[d]))

    elif period == 'weekly':
        # Weeks ending on Sunday (use ISO week numbers)
        start = today - timedelta(weeks=lookback - 1)
        # create week start dates
        weeks = []
        for i in range(lookback):
            wk_start = (start + timedelta(weeks=i))
            # normalize to Monday
            wk_start = wk_start - timedelta(days=wk_start.weekday())
            weeks.append(wk_start)
        counts = { w: 0 for w in weeks }
        qs = Sale.objects.filter(date__gte=weeks[0]).values('date').annotate(
            total=Sum(Case(
                When(units_sold__gt=MAX_UNITS_PER_SALE, then=Value(MAX_UNITS_PER_SALE)),
                default='units_sold',
                output_field=IntegerField()
            ))
        )
        for row in qs:
            d = row['date']
            wk_start = d - timedelta(days=d.weekday())
            if wk_start in counts:
                counts[wk_start] += int(row['total'] or 0)
        for w in sorted(counts.keys()):
            label = w.isoformat()
            series.append((label, counts[w]))

    elif period == 'monthly':
        start = today - relativedelta(months=lookback - 1)
        months = []
        cur = start.replace(day=1)
        for i in range(lookback):
            months.append(cur)
            cur = (cur + relativedelta(months=1)).replace(day=1)
        counts = { m: 0 for m in months }
        qs = Sale.objects.filter(date__gte=months[0]).values('date').annotate(
            total=Sum(Case(
                When(units_sold__gt=MAX_UNITS_PER_SALE, then=Value(MAX_UNITS_PER_SALE)),
                default='units_sold',
                output_field=IntegerField()
            ))
        )
        for row in qs:
            d = row['date']
            m = d.replace(day=1)
            if m in counts:
                counts[m] += int(row['total'] or 0)
        for m in sorted(counts.keys()):
            label = m.strftime('%Y-%m')
            series.append((label, counts[m]))

    return series


def forecast_time_series(series, horizon=7, method='auto', window=3):
    """
    Given a time series list of (label, value), produce a forecast for `horizon` steps ahead.

    Methods:
      - 'auto' (default): select best method via backtest among linear/holt/ma
      - 'linear': fit a linear regression to capture trends
      - 'holt': Holt's linear exponential smoothing (captures trend)
      - 'ma': moving-average style (robust to outliers)

    Returns dict with keys: 'forecast' (list), 'upper', 'lower', 'confidence', 'accuracy'
    """
    # Import numeric libs lazily and tolerate their absence
    try:
        import numpy as np
    except Exception:
        np = None
    try:
        from sklearn.linear_model import LinearRegression
    except Exception:
        LinearRegression = None

    values = [v for _, v in series]
    n = len(values)
    if n == 0:
        return {'forecast': [0] * horizon, 'upper': [0] * horizon, 'lower': [0] * horizon, 'confidence': 0}

    # If the caller asked for 'auto', perform a lightweight model selection
    if method == 'auto':
        try:
            chosen, params, diag = select_best_forecasting_method(values, horizon=horizon)
            method = chosen
        except Exception:
            method = 'ma'

    # If we have very few data points (less than 2), use MA for stability
    if n < 2:
        method = 'ma'

    # Linear regression approach
    if method == 'linear':
        if (np is None) or (LinearRegression is None):
            method = 'ma'
        else:
            try:
                X = np.arange(n).reshape(-1, 1)
                y = np.array(values, dtype=float)
                model = LinearRegression()
                model.fit(X, y)
                r2 = model.score(X, y)

                future_X = np.arange(n, n + horizon).reshape(-1, 1)
                preds = model.predict(future_X)
                preds = [max(0, int(round(float(p)))) for p in preds]

                resid = y - model.predict(X)
                std = float(resid.std()) if len(resid) > 1 else max(1.0, float(y.std() if y.size else 1.0))
                upper = [int(round(p + 1.5 * std)) for p in preds]
                lower = [max(0, int(round(p - 1.5 * std))) for p in preds]

                confidence = max(0.0, min(100.0, r2 * 100))
                if confidence >= 70:
                    accuracy = 'High'
                elif confidence >= 40:
                    accuracy = 'Medium'
                else:
                    accuracy = 'Low'

                return {'forecast': preds, 'upper': upper, 'lower': lower, 'confidence': confidence, 'accuracy': accuracy}
            except Exception:
                method = 'ma'

    # Holt's method
    if method == 'holt':
        try:
            # Allow params from selection by re-running a short grid if desired
            preds, residuals = _holt_linear_forecast(values, horizon=horizon, alpha=0.6, beta=0.1)
            std = (sum([r * r for r in residuals]) / len(residuals)) ** 0.5 if residuals else 0.0
            upper = [int(round(p + 1.5 * std)) for p in preds]
            lower = [max(0, int(round(p - 1.5 * std))) for p in preds]
            # Confidence: inverse of normalized std relative to average
            avg = (sum(values) / len(values)) if len(values) else 0.0
            if avg <= 0:
                confidence = 0.0
            else:
                rel = std / (avg + 1e-9)
                confidence = max(0.0, min(100.0, (1.0 - rel) * 100.0))
            if confidence >= 70:
                accuracy = 'High'
            elif confidence >= 40:
                accuracy = 'Medium'
            else:
                accuracy = 'Low'
            return {'forecast': preds, 'upper': upper, 'lower': lower, 'confidence': round(confidence, 2), 'accuracy': accuracy}
        except Exception:
            method = 'ma'

    # Default / Moving Average fallback
    try:
        # Use median of recent values and estimate a simple slope if possible
        recent = values[-window:] if window and len(values) >= 1 else values
        if recent and len(recent) >= 2:
            # try a small trend estimate
            try:
                if np is not None and LinearRegression is not None:
                    rx = np.arange(len(recent)).reshape(-1, 1)
                    ry = np.array(recent, dtype=float)
                    tm = LinearRegression(); tm.fit(rx, ry)
                    slope = float(tm.coef_[0])
                    base = float(np.median(recent)) if np is not None else (sum(recent) / len(recent))
                    preds = [max(0, int(round(base + slope * (i + 1)))) for i in range(horizon)]
                    residuals = (ry - tm.predict(rx)).tolist()
                else:
                    # fallback simple slope estimate
                    slope = float(recent[-1] - recent[0]) / (len(recent) - 1)
                    base = sum(recent) / len(recent)
                    preds = [max(0, int(round(base + slope * (i + 1)))) for i in range(horizon)]
                    residuals = [float(v - base) for v in recent]
            except Exception:
                base = sum(recent) / len(recent)
                preds = [max(0, int(round(base))) for _ in range(horizon)]
                residuals = [float(v - base) for v in recent]
        else:
            base = sum(values) / len(values)
            preds = [max(0, int(round(base))) for _ in range(horizon)]
            residuals = [float(v - base) for v in values]

        std = (sum([r * r for r in residuals]) / len(residuals)) ** 0.5 if residuals else 0.0
        upper = [int(round(p + 1.5 * std)) for p in preds]
        lower = [max(0, int(round(p - 1.5 * std))) for p in preds]

        avg = (sum(values) / len(values)) if len(values) else 0.0
        if avg <= 0:
            confidence = 0.0
        else:
            rel_disp = std / (avg + 1e-9)
            confidence = max(0.0, min(100.0, (1.0 - rel_disp) * 100.0))

        if confidence >= 70:
            accuracy = 'High'
        elif confidence >= 40:
            accuracy = 'Medium'
        else:
            accuracy = 'Low'

        return {'forecast': preds, 'upper': upper, 'lower': lower, 'confidence': round(confidence, 2), 'accuracy': accuracy}
    except Exception:
        return {'forecast': [0] * horizon, 'upper': [0] * horizon, 'lower': [0] * horizon, 'confidence': 0}


def compute_period_overview(series):
    """Given a time series list of (label, units) ordered chronologically,
    return a summary dict with total (most recent), previous total, pct_change and arrow.
    """
    if not series:
        return {'total': 0, 'previous': 0, 'pct_change': 0.0, 'arrow': 'same'}
    # last value is current period
    cur_label, cur_val = series[-1]
    prev_val = series[-2][1] if len(series) >= 2 else 0
    total = int(cur_val)
    previous = int(prev_val)
    if previous == 0:
        pct = 100.0 if total > 0 else 0.0
    else:
        pct = round(((total - previous) / float(previous)) * 100.0, 2)
    if pct > 0:
        arrow = 'up'
    elif pct < 0:
        arrow = 'down'
    else:
        arrow = 'same'
    return {'total': total, 'previous': previous, 'pct_change': pct, 'arrow': arrow}


def generate_insight(period_name, series, forecast_payload):
    """Generate a short insight string for the period based on recent trend and forecast confidence."""
    # Basic heuristics: use last 3 points to detect trend and use forecast_payload['confidence']
    try:
        vals = [v for _, v in series]
        if not vals:
            return ''
        recent = vals[-3:]
        avg_recent = sum(recent) / len(recent)
        forecast_conf = float(forecast_payload.get('confidence', 0))
        # trend check
        if len(vals) >= 3 and vals[-1] > vals[-2] > vals[-3]:
            trend_text = 'increasing'
        elif len(vals) >= 3 and vals[-1] < vals[-2] < vals[-3]:
            trend_text = 'decreasing'
        else:
            trend_text = 'stable'

        if trend_text == 'increasing' and forecast_conf >= 60:
            return f"{period_name.capitalize()} sales show an increasing trend; expected to continue (confidence: {int(forecast_conf)}%)."
        if trend_text == 'decreasing' and forecast_conf >= 60:
            return f"{period_name.capitalize()} sales are decreasing; consider promotions (confidence: {int(forecast_conf)}%)."
        if trend_text == 'stable' and forecast_conf >= 70:
            return f"{period_name.capitalize()} sales are steady; no major changes expected (confidence: {int(forecast_conf)}%)."
        # Low confidence fallback
        if forecast_conf < 40:
            return f"{period_name.capitalize()} forecast has low confidence ({int(forecast_conf)}%). Review recent data for anomalies."
        # General mild insight
        return f"{period_name.capitalize()} sales show {trend_text} behaviour (confidence: {int(forecast_conf)}%)."
    except Exception:
        return ''


def product_daily_series(product_id, lookback_days=90):
    """Return a daily aggregated series for a product as list of (iso_date, units).
    Fills missing days with zeros for the requested lookback window.
    """
    from datetime import date, timedelta
    from django.db.models import Sum, Case, When, Value, IntegerField

    end = date.today()
    start = end - timedelta(days=lookback_days - 1)

    # Initialize all days to zero
    counts = { (start + timedelta(days=i)): 0 for i in range(lookback_days) }

    qs = Sale.objects.filter(product_id=product_id, date__gte=start).values('date').annotate(
        total=Sum(Case(
            When(units_sold__gt=MAX_UNITS_PER_SALE, then=Value(MAX_UNITS_PER_SALE)),
            default='units_sold',
            output_field=IntegerField()
        ))
    )
    for row in qs:
        d = row['date']
        if d >= start and d <= end:
            counts[d] = counts.get(d, 0) + int(row.get('total') or 0)
    series = [(d.isoformat(), counts[d]) for d in sorted(counts.keys())]
    return series


def product_forecast_summary(product_id, horizons=(1, 7, 30), lookback_days=90):
    """Compute forecasts for a single product for multiple horizons.
    Returns dict with per-horizon forecasts and summary info.
    """
    try:
        series = product_daily_series(product_id, lookback_days=lookback_days)
    except Exception:
        series = []

    # Build a simple summary using the existing forecast_time_series helper
    payload = {}
    for h in horizons:
        try:
            fore = forecast_time_series(series, horizon=h)
            payload[f'h_{h}'] = {
                'forecast': fore.get('forecast', [0])[-1] if fore.get('forecast') else 0,
                'upper': fore.get('upper', [0])[-1] if fore.get('upper') else 0,
                'lower': fore.get('lower', [0])[-1] if fore.get('lower') else 0,
                'confidence': fore.get('confidence', 0),
                'accuracy': fore.get('accuracy', 'Low')
            }
        except Exception:
            payload[f'h_{h}'] = {'forecast': 0, 'upper': 0, 'lower': 0, 'confidence': 0, 'accuracy': 'Low'}

    # Additional summary metrics
    vals = [v for _, v in series]
    last_7 = int(sum(vals[-7:])) if vals else 0
    avg = float(sum(vals) / len(vals)) if vals else 0.0
    # crude trend estimate
    trend = 'stable'
    if len(vals) >= 2 and vals[-1] > vals[0]:
        trend = 'increasing'
    elif len(vals) >= 2 and vals[-1] < vals[0]:
        trend = 'decreasing'

    return {
        'product_id': product_id,
        'series': series,
        'last_7_days': last_7,
        'avg': avg,
        'trend': trend,
        'horizons': payload
    }


# ------------------------
# Forecasting helpers
# ------------------------

def _mape(actual, predicted):
    """Mean absolute percentage error, robust to zero actual values (uses 1 as denom when actual == 0)."""
    if not actual or not predicted:
        return float('inf')
    acc = []
    for a, p in zip(actual, predicted):
        denom = a if a and a > 0 else 1.0
        acc.append(abs((a - p) / float(denom)))
    return (sum(acc) / len(acc)) * 100.0


def _holt_linear_forecast(values, horizon=7, alpha=0.8, beta=0.2):
    """Simple implementation of Holt's linear method (level + trend) without external deps.
    Returns list of integer forecasts of length `horizon` and residuals list for the training fit.
    """
    if not values:
        return [0] * horizon, []
    # initialize
    l = float(values[0])
    b = (float(values[1]) - float(values[0])) if len(values) >= 2 else 0.0
    fitted = [l]
    for t in range(1, len(values)):
        prev_l = l
        prev_b = b
        obs = float(values[t])
        l = alpha * obs + (1 - alpha) * (prev_l + prev_b)
        b = beta * (l - prev_l) + (1 - beta) * prev_b
        fitted.append(l)
    # Forecast
    preds = [max(0, int(round(l + b * (i + 1)))) for i in range(horizon)]
    # residuals: observed - fitted (aligned)
    residuals = []
    for obs, fit in zip(values, fitted):
        residuals.append(float(obs) - float(fit))
    return preds, residuals


def _moving_average_forecast_simple(values, horizon=7, window=3):
    if not values:
        return [0] * horizon, []
    recent = values[-window:] if len(values) >= 1 else values
    avg = sum(recent) / len(recent)
    preds = [max(0, int(round(avg))) for _ in range(horizon)]
    residuals = [float(v) - float(avg) for v in recent]
    return preds, residuals


def select_best_forecasting_method(values, horizon=7):
    """Simple backtest to select among ['linear', 'holt', 'ma'] using MAPE on a holdout.
    Returns tuple (best_method_name, best_params_dict, diagnostics)
    """
    # require at least 4 points to meaningfully evaluate; otherwise prefer MA
    n = len(values)
    if n < 4:
        return 'ma', {'window': 3}, {'reason': 'too short, using MA'}

    # holdout size: min( max(1, int(20% of n)), 7 )
    holdout = min(max(1, int(round(n * 0.2))), 7)
    train = values[:-holdout]
    test = values[-holdout:]

    results = {}

    # Try linear regression if available
    try:
        import numpy as _np  # noqa: N813 - local import
        from sklearn.linear_model import LinearRegression as _LR
        X_train = _np.arange(len(train)).reshape(-1, 1)
        y_train = _np.array(train, dtype=float)
        model = _LR()
        model.fit(X_train, y_train)
        X_test = _np.arange(len(train), len(train) + holdout).reshape(-1, 1)
        preds = model.predict(X_test).tolist()
        preds = [max(0, int(round(float(p)))) for p in preds]
        results['linear'] = _mape(test, preds)
    except Exception:
        results['linear'] = float('inf')

    # Try Holt's linear with small grid search
    best_holt_mape = float('inf')
    best_holt_params = None
    for alpha in (0.2, 0.4, 0.6, 0.8):
        for beta in (0.05, 0.1, 0.2):
            try:
                preds, _ = _holt_linear_forecast(train, horizon=holdout, alpha=alpha, beta=beta)
                m = _mape(test, preds)
                if m < best_holt_mape:
                    best_holt_mape = m
                    best_holt_params = {'alpha': alpha, 'beta': beta}
            except Exception:
                continue
    results['holt'] = best_holt_mape if best_holt_params is not None else float('inf')

    # Try simple moving average
    try:
        preds, _ = _moving_average_forecast_simple(train, horizon=holdout, window=3)
        results['ma'] = _mape(test, preds)
    except Exception:
        results['ma'] = float('inf')

    # pick best
    best = min(results.items(), key=lambda x: x[1])  # (method, mape)
    method = best[0]
    diagnostics = {'scores': results}
    params = {}
    if method == 'holt':
        params = best_holt_params or {'alpha': 0.8, 'beta': 0.1}
    elif method == 'linear':
        params = {}
    else:
        params = {'window': 3}

    return method, params, diagnostics

