"""Scientific-boundary regressions for the Ridgecrest reference audit."""
from datetime import timedelta
from pathlib import Path
import tempfile
import unittest

from audit_references import event, origin, overlap, phase_summary, read_events, utc, within


class ReferenceAuditTests(unittest.TestCase):
    def row(self, seconds=0, latitude=35.7, longitude=-117.5, depth=5):
        return event(utc('2019-07-04T00:00:00Z')+timedelta(seconds=seconds),
                     latitude, longitude, depth, 1, 'local', 1)

    def test_window_is_half_open_and_mask_is_inclusive(self):
        start=utc('2019-07-04T00:00:00Z');end=start+timedelta(seconds=1)
        bounds={'latitude':[35.7,36.0],'longitude':[-117.5,-117.0],'depth_km':[0,5]}
        self.assertTrue(within(self.row(),start,end,bounds))
        self.assertFalse(within(self.row(1),start,end,bounds))
        self.assertFalse(within(self.row(depth=5.001),start,end,bounds))

    def test_ambiguous_matches_are_not_arbitrarily_assigned(self):
        result=overlap([self.row(),self.row(.2)],[self.row(.1)],1,5)
        self.assertEqual(result['candidate_edges'],2)
        self.assertEqual(result['reciprocal_unique_pairs'],0)
        self.assertEqual(result['left_with_candidate_but_unresolved'],2)
        self.assertEqual(result['right_multiple_candidates'],1)

    def test_depth_datum_does_not_reject_horizontal_time_match(self):
        result=overlap([self.row(depth=5.7)],[self.row(1,depth=5)],1,2)
        self.assertEqual(result['reciprocal_unique_pairs'],1)
        self.assertAlmostEqual(result['native_depth_difference_left_minus_right_km']['p50'],.7)

    def test_horizontal_outlier_does_not_match_on_time_alone(self):
        result=overlap([self.row()],[self.row(latitude=36.7)],1,5)
        self.assertEqual(result['candidate_edges'],0)
        self.assertEqual(result['left_without_candidate'],1)

    def test_noncanonical_seconds_are_not_silently_normalized(self):
        with self.assertRaises(ValueError):origin(['2019','7','4','0','0','60.1'])
        with self.assertRaises(ValueError):origin(['2019','7','4','0','0','nan'])

    def test_malformed_rows_are_recorded_and_liu_has_no_invented_id(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'liu.txt'
            p.write_text('yr mo day hr min sec lat lon dep mag\n2019 7 4 0 0 1.0 35.7 -117.5 5 1\n2019 7 broken\n')
            rows,errors=read_events(p,'liu')
            self.assertEqual(len(rows),1)
            self.assertIsNone(rows[0]['native_id'])
            self.assertEqual(errors[0]['source_row'],3)

    def test_phase_arrivals_use_unix_seconds_and_are_not_events(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'phase.csv'
            start=utc('2019-07-04T00:00:00Z')
            p.write_text('arrival,phase,network,station,template_id,match_id\n'
                         f'{start.timestamp()},P,CI,A,1,2\n'
                         f'{start.timestamp()+1},S,CI,A,1,2\n')
            result=phase_summary(p,start,start+timedelta(seconds=1))
            self.assertEqual(result['row_count'],2)
            self.assertEqual(result['arrival_time_only_rows'],1)
            self.assertEqual(result['match_ids'],1)
            self.assertTrue(result['origin_time_not_supplied'])


if __name__=='__main__':unittest.main()
