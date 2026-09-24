"""Source-neutral catalog diagnostics; these comparisons are not formal scoring."""
from bisect import bisect_left, bisect_right
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import math

UTC = timezone.utc

def utc(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def origin(columns):
    seconds = float(columns[5])
    if not math.isfinite(seconds) or not 0 <= seconds < 60:
        raise ValueError('seconds outside [0, 60)')
    return datetime(*map(int, columns[:5]), tzinfo=UTC) + timedelta(seconds=seconds)


def finite(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('non-finite number')
    return number


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def event(time, lat, lon, depth, magnitude, native_id, line, **extra):
    lat, lon, depth = map(finite, (lat, lon, depth))
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError('invalid geographical coordinates')
    return dict(time=time, timestamp=time.timestamp(), latitude=lat, longitude=lon,
                depth_km=depth, magnitude=finite(magnitude) if magnitude not in ('', None) else None,
                native_id=native_id, source_row=line, **extra)


def within(row, start, end, bounds=None):
    if not start <= row['time'] < end:
        return False
    return bounds is None or all(bounds[key][0] <= row[key] <= bounds[key][1]
                                 for key in ('latitude', 'longitude', 'depth_km'))


def quantiles(values):
    values = sorted(values)
    if not values:
        return None
    def q(p):
        i = (len(values) - 1) * p
        lo = int(i)
        return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (i - lo)
    return {'min': values[0], 'p50': q(.5), 'p90': q(.9), 'max': values[-1]}


def horizontal_km(a, b):
    lat1, lat2 = math.radians(a['latitude']), math.radians(b['latitude'])
    dlat = lat2 - lat1
    dlon = math.radians(b['longitude'] - a['longitude'])
    v = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(min(1.0, max(0.0, v))))


def overlap(left, right, time_seconds, distance_km):
    """Accept only reciprocal degree-one edges; ambiguous components stay unresolved."""
    right = sorted(right, key=lambda r: r['timestamp'])
    times = [r['timestamp'] for r in right]
    candidates = []
    degrees = Counter()
    for a in left:
        js = []
        for j in range(bisect_left(times, a['timestamp'] - time_seconds),
                       bisect_right(times, a['timestamp'] + time_seconds)):
            if horizontal_km(a, right[j]) <= distance_km:
                js.append(j)
                degrees[j] += 1
        candidates.append(js)
    pairs = [(a, right[js[0]]) for a, js in zip(left, candidates)
             if len(js) == 1 and degrees[js[0]] == 1]
    return {
        'time_tolerance_s': time_seconds, 'horizontal_tolerance_km': distance_km,
        'left_rows': len(left), 'right_rows': len(right), 'candidate_edges': sum(map(len, candidates)),
        'reciprocal_unique_pairs': len(pairs),
        'left_without_candidate': sum(not js for js in candidates),
        'right_without_candidate': len(right) - len(degrees),
        'left_multiple_candidates': sum(len(js) > 1 for js in candidates),
        'right_multiple_candidates': sum(n > 1 for n in degrees.values()),
        'left_with_candidate_but_unresolved': sum(bool(js) for js in candidates) - len(pairs),
        'right_with_candidate_but_unresolved': len(degrees) - len(pairs),
        'absolute_origin_time_difference_s': quantiles([abs(a['timestamp']-b['timestamp']) for a,b in pairs]),
        'horizontal_difference_km': quantiles([horizontal_km(a,b) for a,b in pairs]),
        'native_depth_difference_left_minus_right_km': quantiles([a['depth_km']-b['depth_km'] for a,b in pairs]),
        'interpretation': 'Reference overlap diagnostic, not precision/recall or truth error; native depth datums are not harmonized.',
    }


def summary(rows):
    ids = [r['native_id'] for r in rows if r['native_id'] is not None]
    times = [r['time'].isoformat() for r in rows]
    tuples = [(r['timestamp'], r['latitude'], r['longitude'], r['depth_km'], r['magnitude']) for r in rows]
    return {
        'row_count': len(rows), 'rows_without_native_id': len(rows)-len(ids),
        'duplicate_native_id_rows': len(ids)-len(set(ids)),
        'duplicate_origin_time_rows': len(times)-len(set(times)),
        'duplicate_time_location_magnitude_rows': len(tuples)-len(set(tuples)),
        'observed_time_range_utc': [min(times), max(times)] if times else None,
        'ranges': {key: [min(v),max(v)] if v else None
                   for key in ('latitude','longitude','depth_km','magnitude')
                   for v in [[r[key] for r in rows if r[key] is not None]]},
        'event_types': dict(sorted(Counter(r.get('event_type','not_supplied') for r in rows).items())),
    }
