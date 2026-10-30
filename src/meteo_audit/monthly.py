"""Monthly read-only archive summary with Europe/Prague calendar boundaries."""
from __future__ import annotations
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from .db import query

TZ = ZoneInfo('Europe/Prague')

def months(start_year: int, end_year: int):
    now = datetime.now(TZ)
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == end_year and month > 12:
                continue
            start = datetime(year, month, 1, tzinfo=TZ)
            stop = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=TZ)
            if start >= now:
                return
            yield start, min(stop, now)

def audit_month(start: datetime, stop: datetime, first_epoch: int, last_epoch: int, default_interval: int) -> dict[str, object]:
    begin, end = int(start.timestamp()), int(stop.timestamp())
    sql = ("SELECT dateTime,`interval`,usUnits,rain,rainRate "
           "FROM `pocasi-loucka.eu`.archive "
           f"WHERE dateTime >= {begin} AND dateTime < {end} ORDER BY dateTime")
    rows = query(sql, timeout=60)
    interval_counts: Counter[int] = Counter()
    unit_counts: Counter[int] = Counter()
    day_sums: defaultdict[str, float] = defaultdict(float)
    hour_sums: defaultdict[str, float] = defaultdict(float)
    rain_values: list[float] = []
    rate_values: list[float] = []
    rain_null = rate_null = rain_positive_rate_zero = rate_positive_rain_zero = 0
    gaps = 0
    previous: tuple[int, int] | None = None
    for row in rows:
        epoch_s, interval_s, units_s, rain_s, rate_s = row.split('\t')
        epoch, interval, units = int(epoch_s), int(interval_s), int(units_s)
        interval_counts[interval] += 1
        unit_counts[units] += 1
        if previous:
            delta = epoch - previous[0]
            base = previous[1] * 60
            if base > 0 and delta >= 1.5 * base:
                gaps += max(1, round(delta / base) - 1)
        previous = (epoch, interval)
        local = datetime.fromtimestamp(epoch, timezone.utc).astimezone(TZ)
        if rain_s not in (r'\N', 'NULL'):
            rain = float(rain_s)
            rain_values.append(rain)
            day_sums[local.date().isoformat()] += rain
            hour_sums[f'{local.date().isoformat()}T{local.hour:02d}{local.strftime("%z")}'] += rain
            if rate_s not in (r'\N', 'NULL'):
                rain_positive_rate_zero += rain > 0 and float(rate_s) == 0
        else:
            rain_null += 1
        if rate_s not in (r'\N', 'NULL'):
            rate = float(rate_s)
            rate_values.append(rate)
            if rain_s not in (r'\N', 'NULL'):
                rate_positive_rain_zero += rate > 0 and float(rain_s) == 0
        else:
            rate_null += 1
    count = len(rows)
    mode_interval = interval_counts.most_common(1)[0][0] if interval_counts else default_interval
    outside_range = end <= first_epoch or begin > last_epoch
    expected_start = max(begin, first_epoch)
    span_seconds = max(0, end - expected_start)
    expected = 0 if outside_range else round(span_seconds / (mode_interval * 60))
    units = ','.join(f'{k}:{v}' for k,v in sorted(unit_counts.items()))
    to_mm = 10.0 if set(unit_counts) == {16} else None
    max_interval = max(rain_values) if rain_values else None
    max_5min = max((float(parts[3]) for r in rows if int((parts := r.split('\t'))[1]) == 5 and parts[3] not in (r'\N', 'NULL')), default=None)
    max_rate = max(rate_values) if rate_values else None
    result: dict[str, object] = {
        'local_month': start.strftime('%Y-%m'), 'month_complete': stop.day == 1 and stop.hour == 0 and stop.minute == 0,
        'range_status': 'outside_archive_range' if outside_range else ('no_rows_within_archive_range' if count == 0 else 'has_rows'),
        'start_utc_epoch': begin, 'stop_utc_epoch_exclusive': end,
        'rows': count, 'expected_at_modal_interval': expected,
        'coverage_pct_estimated': round(100 * count / expected, 3) if expected else None,
        'missing_rows_estimated': max(0, expected - count), 'observed_timestamp_gaps_estimated': gaps,
        'rain_null': rain_null, 'rainRate_null': rate_null, 'rain_positive_rate_zero': rain_positive_rate_zero,
        'rate_positive_rain_zero': rate_positive_rain_zero, 'interval_counts_min': ';'.join(f'{k}:{v}' for k,v in sorted(interval_counts.items())),
        'usUnits_counts': units, 'rain_sum_stored': round(sum(rain_values), 6) if rain_values else None,
        'rain_sum_mm_if_usUnits16': round(sum(rain_values) * to_mm, 3) if to_mm else None,
        'wet_intervals': sum(v > 0 for v in rain_values),
        'max_interval_rain_stored': max_interval, 'max_5min_rain_stored': max_5min,
        'max_local_day_sum_stored': max(day_sums.values(), default=None),
        'max_local_clock_hour_sum_stored': max(hour_sums.values(), default=None),
        'max_rainRate_stored': max_rate,
    }
    return result

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start-year', type=int, default=2009)
    parser.add_argument('--end-year', type=int, default=2026)
    parser.add_argument('--output', type=Path, default=Path('reports/monthly_rain_coverage.csv'))
    args = parser.parse_args()
    fields = None
    results = []
    range_row = query('SELECT MIN(dateTime),MAX(dateTime) FROM `pocasi-loucka.eu`.archive')[0].split('\t')
    first_epoch, last_epoch = map(int, range_row)
    interval_rows = query('SELECT `interval`,COUNT(*) FROM `pocasi-loucka.eu`.archive GROUP BY `interval` ORDER BY COUNT(*) DESC LIMIT 1')[0].split('\t')
    default_interval = int(interval_rows[0])
    for start, stop in months(args.start_year, args.end_year):
        row = audit_month(start, stop, first_epoch, last_epoch, default_interval)
        fields = fields or list(row)
        results.append(row)
        print(f"{row['local_month']}: {row['rows']} rows", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader(); writer.writerows(results)
    yearly = {}
    for row in results:
        year = row['local_month'][:4]
        y = yearly.setdefault(year, {'year_local': year, 'months_included': 0, 'observed_rows': 0,
            'expected_rows_estimated': 0, 'rain_null': 0, 'rainRate_null': 0, 'wet_intervals': 0,
            'rain_sum_mm_if_usUnits16': 0.0, 'max_local_day_sum_stored': None,
            'max_local_clock_hour_sum_stored': None, 'max_5min_rain_stored': None,
            'max_rainRate_stored': None})
        y['months_included'] += row['range_status'] != 'outside_archive_range'
        y['observed_rows'] += int(row['rows'])
        y['expected_rows_estimated'] += int(row['expected_at_modal_interval'] or 0)
        y['rain_null'] += int(row['rain_null'])
        y['rainRate_null'] += int(row['rainRate_null'])
        y['wet_intervals'] += int(row['wet_intervals'])
        y['rain_sum_mm_if_usUnits16'] += float(row['rain_sum_mm_if_usUnits16'] or 0)
        for key in ('max_local_day_sum_stored', 'max_local_clock_hour_sum_stored', 'max_5min_rain_stored', 'max_rainRate_stored'):
            value = row[key]
            if value is not None and (y[key] is None or float(value) > y[key]):
                y[key] = float(value)
    year_path = args.output.with_name('yearly_rain_coverage.csv')
    with year_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(next(iter(yearly.values())).keys()) + ['coverage_pct_estimated'], lineterminator='\n')
        writer.writeheader()
        for y in yearly.values():
            y['rain_sum_mm_if_usUnits16'] = round(y['rain_sum_mm_if_usUnits16'], 3)
            y['coverage_pct_estimated'] = round(100 * y['observed_rows'] / y['expected_rows_estimated'], 3) if y['expected_rows_estimated'] else None
            writer.writerow(y)
    print(f'Wrote {len(results)} monthly rows to {args.output}')
    print(f'Wrote {len(yearly)} yearly rows to {year_path}')

if __name__ == '__main__':
    main()
