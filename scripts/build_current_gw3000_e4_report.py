#!/usr/bin/env python3
"""Review frozen GW3000 archive evidence and immutable read-only live capture."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / 'data/GW3000_INSERT_ONLY_BACKFILL_PAYLOAD.jsonl'
MANIFEST = ROOT / 'data/GW3000_INSERT_ONLY_BACKFILL_MANIFEST.json'
LIVE_DIR = ROOT / 'data/gw3000-current-readonly'
API_DOC = 'https://oss.ecowitt.net/uploads/20260109/HTTP%20API%20interface%20Protocol%20%28Generic%29-%28V1.0.5-2025-10-08%29%20.pdf'
WEBUI_DOC = 'https://oss.ecowitt.net/uploads/20250408/WS%20View%20Plus%20%26%20Web%20UI%20Manual%20%28Generic%29.pdf'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    rows = [json.loads(line) for line in PAYLOAD.read_text(encoding='utf-8').splitlines() if line.strip()]
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    captures = sorted(LIVE_DIR.glob('capture-*.json'))
    capture = None
    capture_rel = None
    if captures:
        capture_path = captures[-1]
        capture = json.loads(capture_path.read_text(encoding='utf-8'))
        capture_rel = str(capture_path.relative_to(ROOT))

    rain = [r['rain'] for r in rows if r.get('rain') is not None]
    rate = [r['rainRate'] for r in rows if r.get('rainRate') is not None]
    both = [r for r in rows if r.get('rain') is not None and r.get('rainRate') is not None]
    decreases = []
    previous = None
    for row in rows:
        value = row.get('rain')
        if value is None:
            continue
        if previous is not None and (value < previous or value == 0 < previous):
            decreases.append({'timestamp': row['dateTime'], 'previous': previous,
                              'current': value, 'kind': 'decrease_or_zero_after_positive'})
        previous = value

    live_summary = None
    if capture:
        totals = capture['rain_configuration']['get_rain_totals']
        version = capture['gateway']['version'].get('version')
        live_summary = {
            'capture_path': capture_rel,
            'capture_sha256': sha(captures[-1]),
            'capture_started_utc': capture['capture_started_utc'],
            'capture_completed_utc': capture['capture_completed_utc'],
            'firmware': version,
            'gateway_model': 'GW3000A' if version and 'GW3000A' in version else None,
            'unit_settings': capture['gateway']['units'],
            'rain_configuration': totals,
            'rain_capable_sensors': capture['rain_configuration']['rain_capable_sensor_catalog'],
            'live_raw_rain_field_subset': capture['live_raw_rain_field_subset'],
            'response_hashes': capture['response_hashes'],
            'official_protocol': API_DOC,
            'official_webui_manual': WEBUI_DOC,
        }

    unresolved = [
        'exact mapping from the priority-selected traditional rain output to a physical active sensor, sensor resolution, and dated sensor deployment history; WH40 is listed active, along with other rain-capable sensors',
        'deployed WeeWX driver, version, and rain/rainRate configuration tied to the frozen archive window; no matching configuration was found on this audit host',
        'immutable historical raw rain/API or SD-card records for wet, restart, and rollover examples; the live capture is a current dry rain-field excerpt only',
        'explicit rain counter versus interval semantics and reset/rollover rules, including interpretation of the gateway reset flags',
        'rainRate unit is exposed as mm/Hr, but its averaging/derivation window and exact mapping to the archive field remain unverified',
        'exact timestamp/archive-end mapping corroborated against a same-time raw payload; live endpoint responses have request times but no per-field observation time',
        'independent gauge or correctly windowed reference evidence for the current sensor epoch',
    ]
    out = {
        'schema': 'loucka-current-gw3000-e4-review-v2',
        'generated_utc': manifest['source_window']['captured_source_max_utc'],
        'payload_path': str(PAYLOAD.relative_to(ROOT)),
        'payload_sha256': sha(PAYLOAD),
        'manifest_sha256': sha(MANIFEST),
        'source_window': manifest['source_window'],
        'row_count': len(rows),
        'cadence_minutes': sorted(set(r.get('interval') for r in rows)),
        'usUnits': sorted(set(r.get('usUnits') for r in rows)),
        'rain_archive_field': {
            'nonnull': len(rain), 'null': len(rows) - len(rain), 'nonzero': sum(x != 0 for x in rain),
            'minimum': min(rain) if rain else None, 'maximum': max(rain) if rain else None,
            'sum_as_stored_not_interpreted': sum(rain),
        },
        'rainRate_archive_field': {
            'nonnull': len(rate), 'null': len(rows) - len(rate), 'nonzero': sum(x != 0 for x in rate),
            'minimum': min(rate) if rate else None, 'maximum': max(rate) if rate else None,
        },
        'both_fields_present': len(both),
        'archive_rain_decrease_or_reset_candidates': decreases[:100],
        'decrease_or_reset_candidate_count': len(decreases),
        'evidence_classification': (
            'Frozen source archive rows plus a sanitized exact rain-field subset from immutable current '
            'GW3000 HTTP GET responses. The current capture is dry and does not validate wet/reset mapping. '
            'Historical archive decreases/zeros cannot distinguish interval amount, event field, counter reset, '
            'or driver mapping. No reboot/rollover conclusion is made.'
        ),
        'live_gateway_evidence': live_summary,
        'unresolved_requirements': unresolved,
        'decision': 'BLOCKED_E4_CURRENT_GW3000; no totals or rates cleared; no historical correction or write performed',
    }
    (ROOT / 'CURRENT_GW3000_E4_VALIDATION.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    live_text = 'No current read-only gateway capture is available.'
    if live_summary:
        rain_items = {x.get('id'): x.get('val') for x in (live_summary['live_raw_rain_field_subset'].get('rain') or [])}
        rain_items.update({x.get('id'): x.get('val') for x in live_summary['live_raw_rain_field_subset'].get('common_list_rain_fields') or []})
        sensor_labels = ', '.join(f"{x.get('img')} / {x.get('name')} (active flag {x.get('idst')})"
                                  for x in live_summary['rain_capable_sensors'])
        live_text = (
            f"A sanitized current HTTP GET capture at {live_summary['capture_started_utc']}–"
            f"{live_summary['capture_completed_utc']} reports `{live_summary['firmware']}`; rain unit setting "
            f"code `{live_summary['unit_settings'].get('rain')}` and live strings in millimetres. Gateway rain "
            f"priority is `{live_summary['rain_configuration'].get('rainFallPriority')}` (the response labels "
            "value 1 `Traditional rain gauge`); `rainGain` is "
            f"`{live_summary['rain_configuration'].get('rainGain')}`. Sensor inventory includes {sensor_labels}. "
            f"Raw rain-field excerpt: event `0x0D`={rain_items.get('0x0D')}, rate `0x0E`={rain_items.get('0x0E')}, "
            f"day `0x10`={rain_items.get('0x10')}, week `0x11`={rain_items.get('0x11')}, "
            f"month `0x12`={rain_items.get('0x12')}, year `0x13`={rain_items.get('0x13')}, "
            f"total `0x14`={rain_items.get('0x14')}. The official protocol names these IDs Rain Event, Rain Rate, "
            "Rain Day/Week/Month/Year/Totals; this documents gateway fields but not their WeeWX archive mapping. "
            f"Capture file SHA-256: `{live_summary['capture_sha256']}`."
        )
    report = f'''# Current GW3000 E4 validation report

## Frozen archive evidence

Source archive payload window: {out['source_window']['first_source_utc']} to {out['source_window']['captured_source_max_utc']} ({len(rows)} rows). Payload SHA-256: `{out['payload_sha256']}`.

Archive `rain`: non-null {len(rain)}, nonzero {sum(x != 0 for x in rain)}, stored sum {sum(rain):.6f} (not interpreted as a period total). `rainRate`: non-null {len(rate)}, nonzero {sum(x != 0 for x in rate)}, range {min(rate) if rate else 'n/a'}–{max(rate) if rate else 'n/a'}. Cadence metadata: {out['cadence_minutes']} minutes; archive `usUnits`: {out['usUnits']}.

The frozen export has {len(decreases)} decreases or positive-to-zero sequences in `rain`. These are not classified as resets: without contemporaneous raw inputs and the deployed driver contract, they could reflect interval values, event behavior, reset, or mapping.

## Current device read-only evidence

{live_text}

The capture retains hashes for each unmodified HTTP response and exact rain-field excerpts, while omitting network and sensor radio IDs. It is a current dry sample, not an immutable historical raw-device export. The Ecowitt protocol maps `0x0D` to event rain and `0x0E` to rate and names day/week/month/year/total fields [`official HTTP API protocol`]({API_DOC}). The manufacturer’s Web UI manual explains the traditional/piezo priority selection and WH40’s role as a reference for piezo rain calibration [`official Web UI manual`]({WEBUI_DOC}).

## Decision and open evidence

E4 remains blocked for the current GW3000 epoch. The actual gateway firmware, unit setting, selected rain priority, gain, current dry event/rate, and active rain-capable sensor catalog are now recorded. Sensor resolution/deployment, exact sensor-to-archive mapping, deployed WeeWX driver/version/configuration, historical raw wet/reset payloads, rate derivation window, reset/rollover meaning, archive timestamp mapping, and independent gauge evidence remain unresolved. No rainfall total or rate is cleared; no historical values or gateway settings were changed.

Detailed machine-readable evidence: `CURRENT_GW3000_E4_VALIDATION.json`; immutable local capture: `{capture_rel or 'not available'}`.
'''
    (ROOT / 'CURRENT_GW3000_E4_VALIDATION_REPORT.md').write_text(report, encoding='utf-8')
    print(json.dumps({'rows': len(rows), 'rain_nonzero': sum(x != 0 for x in rain),
                      'rainrate_nonzero': sum(x != 0 for x in rate),
                      'decrease_candidates': len(decreases), 'live_capture_available': bool(capture),
                      'decision': out['decision']}, indent=2))


if __name__ == '__main__':
    main()
