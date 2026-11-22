#!/usr/bin/env python3
"""Capture a small, sanitized, append-only set of GW3000 GET responses for E4.

Only allowlisted read-only HTTP GET endpoints are called. Network identity,
sensor radio IDs, unrelated sensor values, and secrets are never stored.
The original response hash is retained beside the exact rain/config excerpts.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from urllib.request import Request, build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]
POLLER = Path('/usr/local/libexec/loucka-gw3000-http-pull.py')
ENV_FILE = Path('/etc/loucka-weather/gw3000-pull.env')
OUTDIR = ROOT / 'data' / 'gw3000-current-readonly'
MAX_BYTES = 256 * 1024
USER_AGENT = 'LouckaWeather-Audit-ReadOnly/1.0'


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def load_private_gateway_ip():
    if not POLLER.is_file() or not ENV_FILE.is_file():
        raise RuntimeError('existing read-only gateway poller is unavailable')
    spec = importlib.util.spec_from_file_location('loucka_gw3000_readonly_poller', POLLER)
    if spec is None or spec.loader is None:
        raise RuntimeError('cannot load the installed read-only poller')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
        text = line.strip()
        if text.startswith('LOUCKA_GW3000_HTTP_IP='):
            value = text.split('=', 1)[1].strip().strip('"\'')
            return module.private_ip(value)
    raise RuntimeError('private gateway endpoint is not configured')


def get_json(opener, ip, path):
    started = now()
    request = Request('http://' + ip + '/' + path,
                      headers={'Accept': 'application/json', 'User-Agent': USER_AGENT},
                      method='GET')
    with opener.open(request, timeout=4) as response:
        body = response.read(MAX_BYTES + 1)
        status = response.status
        content_type = response.headers.get_content_type()
    received = now()
    if status != 200 or content_type != 'application/json' or not body or len(body) > MAX_BYTES:
        raise RuntimeError('gateway returned an unexpected response')
    try:
        parsed = json.loads(body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuntimeError('gateway returned invalid JSON') from exc
    return {'request_started_utc': started, 'response_received_utc': received,
            'http_status': status, 'response_bytes': len(body),
            'response_sha256': hashlib.sha256(body).hexdigest(), 'data': parsed}


def allowlisted_fields(obj, names):
    return {k: obj[k] for k in names if isinstance(obj, dict) and k in obj}


def main():
    ip = load_private_gateway_ip()
    # The poller uses a no-proxy, redirect-rejecting opener. Reuse that policy.
    spec = importlib.util.spec_from_file_location('loucka_gw3000_readonly_poller', POLLER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    opener = build_opener(ProxyHandler({}), module.NoRedirect())
    paths = {
        'live': 'get_livedata_info?',
        'version': 'get_version?',
        'device_info': 'get_device_info?',
        'units': 'get_units_info?',
        'rain_totals': 'get_rain_totals?',
        'piezo_rain': 'get_piezo_rain?',
    }
    responses = {name: get_json(opener, ip, path) for name, path in paths.items()}
    sensors = []
    sensor_response_hashes = []
    for page in range(1, 5):
        item = get_json(opener, ip, f'get_sensors_info?page={page}?')
        sensor_response_hashes.append({'page': page, 'request_started_utc': item['request_started_utc'],
                                       'response_received_utc': item['response_received_utc'],
                                       'response_sha256': item['response_sha256']})
        if not isinstance(item['data'], list):
            continue
        for sensor in item['data']:
            if not isinstance(sensor, dict):
                continue
            image = str(sensor.get('img', '')).lower()
            name = str(sensor.get('name', ''))
            if image in {'wh40', 'wh85', 'wh90', 'wh65', 'wh69', 'wn20', 'wn64', 'ws80', 'ws85', 'ws90'} or 'rain' in name.lower():
                sensors.append(allowlisted_fields(sensor, ('img', 'type', 'name', 'version', 'idst')))

    live = responses['live']['data']
    def rain_rows(key):
        value = live.get(key) if isinstance(live, dict) else None
        if not isinstance(value, list):
            return None
        return [allowlisted_fields(row, ('id', 'val', 'unit')) for row in value if isinstance(row, dict)]
    common = live.get('common_list', []) if isinstance(live, dict) else []
    common_rain = [allowlisted_fields(row, ('id', 'val', 'unit')) for row in common
                   if isinstance(row, dict) and str(row.get('id', '')).lower() in
                   {'0x0d', '0x0e', '0x0f', '0x10', '0x11', '0x12', '0x13', '0x14', '0x18'}]

    safe = {
        'schema': 'loucka-gw3000-readonly-live-e4-evidence-v1',
        'capture_started_utc': responses['live']['request_started_utc'],
        'capture_completed_utc': sensor_response_hashes[-1]['response_received_utc'],
        'source': {
            'kind': 'private_LAN_HTTP_read_only_GET',
            'gateway_address': 'redacted_private_ip',
            'installed_helper': str(POLLER),
            'selected_endpoints': list(paths.values()) + [f'get_sensors_info?page={p}?' for p in range(1, 5)],
            'all_requests_http_method': 'GET',
            'redirects_followed': False,
        },
        'response_hashes': {k: {x: v[x] for x in ('request_started_utc', 'response_received_utc', 'response_bytes', 'response_sha256')}
                            for k, v in responses.items()},
        'sensor_page_response_hashes': sensor_response_hashes,
        'gateway': {
            'version': allowlisted_fields(responses['version']['data'], ('version', 'platform')),
            'device_info': allowlisted_fields(responses['device_info']['data'],
                                              ('sensorType', 'rf_freq', 'tz_auto', 'tz_index', 'dst_stat', 'date', 'time', 'curr_msg')),
            'units': allowlisted_fields(responses['units']['data'], ('temperature', 'pressure', 'wind', 'rain', 'light', 'capacity')),
        },
        'rain_configuration': {
            'get_rain_totals': allowlisted_fields(responses['rain_totals']['data'],
                ('rainFallPriority', 'list', 'rainDay', 'rainWeek', 'rainMonth', 'rainYear', 'rainTotal',
                 'rainGain', 'rstRainDay', 'rstRainWeek', 'rstRainYear', 'piezo')),
            'get_piezo_rain': allowlisted_fields(responses['piezo_rain']['data'],
                ('drain_piezo', 'wrain_piezo', 'mrain_piezo', 'yrain_piezo', 'train_piezo',
                 'rain1_gain', 'rain2_gain', 'rain3_gain', 'rain4_gain', 'rain5_gain')),
            'rain_capable_sensor_catalog': sensors,
        },
        'live_raw_rain_field_subset': {
            'completeness': 'sanitized exact rain-field excerpts; full response is not retained',
            'rain': rain_rows('rain'),
            'piezoRain': rain_rows('piezoRain'),
            'common_list_rain_fields': common_rain,
        },
        'limitations': [
            'These are current read-only gateway responses; they do not prove historical configuration or sensor epochs.',
            'The gateway provides no per-field observation timestamp in these responses; capture time is only request time.',
            'Current dry conditions do not validate rain amount/rate semantics in wet or reset episodes.',
            'Rain-capable sensors may be listed simultaneously; priority selection does not prove the WeeWX archive field mapping.',
            'No raw historical SD-card payload was obtained; the WebUI requires authentication and is outside this capture.',
            'No settings, totals, gateway state, database rows, or files on the gateway were changed.',
        ],
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = OUTDIR / f'capture-{stamp}.json'
    if destination.exists():
        raise RuntimeError('refusing to overwrite an existing capture')
    destination.write_text(json.dumps(safe, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'capture': str(destination.relative_to(ROOT)),
                      'capture_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
                      'firmware': safe['gateway']['version'].get('version'),
                      'rain_priority': safe['rain_configuration']['get_rain_totals'].get('rainFallPriority'),
                      'rain_sensor_candidates': len(sensors)}, indent=2))


if __name__ == '__main__':
    main()
