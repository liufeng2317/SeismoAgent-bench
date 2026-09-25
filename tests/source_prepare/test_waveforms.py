"""Prevent channel-wide skip errors and admission of unrelated waveform payloads."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from obspy import Stream, Trace, UTCDateTime

SCRIPTS = Path(__file__).resolve().parents[2] / 'benchmark_source/2019_ridgecrest_california/scripts/observations'
spec = importlib.util.spec_from_file_location('waveform_download', SCRIPTS/'download_observations.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class WaveformDownloadTests(unittest.TestCase):
    def test_stationxml_fractional_seconds_on_python310(self):
        spec = importlib.util.spec_from_file_location('station_metadata', SCRIPTS/'prepare_station_metadata.py')
        metadata = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(metadata)
        for suffix in ('.1234', '.123400Z', '.1234+00:00'):
            with self.subTest(suffix=suffix):
                value = metadata.utc('2019-01-01T00:00:00' + suffix)
                self.assertEqual(value.microsecond, 123400)
                self.assertEqual(value.utcoffset().total_seconds(), 0)

    def test_existing_scope_keeps_sensor_family_selection(self):
        inventory={'files':[{'streams':[
            {'network':'CI','station':'APL','channel':'HNE','candidate_npts':10},
            {'network':'CI','station':'EDW2','channel':'HHZ','candidate_npts':10}]}]}
        self.assertEqual(mod.station_ids(None,inventory,'existing',None,{'EH','HH'}),{'CI.EDW2'})
        self.assertEqual(mod.station_ids(None,inventory,'existing',None,{'HN'}),{'CI.APL'})

    def test_missing_channel_is_not_skipped_and_epoch_clips_requests(self):
        epochs = [dict(network='XX', station='TEST', location='', channel=ch,
                       sample_rate_hz=100, effective_start='2019-07-04T12:00:00Z',
                       effective_end='2019-07-06T00:00:00Z') for ch in ('HHE','HHN')]
        a, b = float(UTCDateTime('2019-07-04')), float(UTCDateTime('2019-07-07'))
        selected = mod.targets(epochs, {'XX.TEST'}, {'HH'}, None, a, b)
        rows = mod.waveform_plan(selected, {('XX.TEST..HHE',100):[(a,b)]}, 1)
        self.assertEqual(len(rows), 2)
        self.assertEqual({r['seed_id'] for r in rows}, {'XX.TEST..HHN'})
        self.assertEqual(UTCDateTime(rows[0]['start_utc']), UTCDateTime('2019-07-04T12:00:00'))
        self.assertEqual(UTCDateTime(rows[-1]['end_utc']), UTCDateTime('2019-07-06'))

    def test_cross_file_overlap_does_not_create_false_gaps(self):
        self.assertEqual(mod.missing(0,30,[(0,10),(2,5),(9,15),(20,30)],1),[(15,20)])
        self.assertEqual(mod.missing(0,10,[(.0083,10.0083)],1),[])
        self.assertEqual(mod.missing(0,10,[],1),[(0,10)])
        rows=mod.waveform_plan({('XX.TEST..HHZ',100):[(0,86401)]}, {('XX.TEST..HHZ',100):[(86400.0083,86401)]}, 1)
        self.assertEqual(len(rows),1)
        self.assertEqual(float(UTCDateTime(rows[0]['end_utc'])),86400)

    def test_conflicting_rates_require_a_decision(self):
        base=dict(network='XX',station='TEST',location='',channel='HHZ',effective_start=None,effective_end=None)
        with self.assertRaises(ValueError):
            mod.targets([dict(base,sample_rate_hz=r) for r in (100,200)],{'XX.TEST'},{'HH'},None,0,10)

    def test_response_is_decoded_and_rejects_wrong_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'waveform.mseed'
            tr=Trace(np.arange(100,dtype=np.int32),header=dict(network='XX',station='TEST',channel='HHZ',sampling_rate=10,starttime=UTCDateTime(0)))
            Stream([tr]).write(str(path),format='MSEED')
            row=dict(seed_id='XX.TEST..HHZ',sample_rate_hz=10,start_utc=str(UTCDateTime(0)),end_utc=str(UTCDateTime(10)))
            self.assertEqual(mod.validate_waveform(path,row),10)
            with self.assertRaises(ValueError):
                mod.validate_waveform(path,dict(row,seed_id='XX.TEST..HHN'))
            with self.assertRaises(ValueError):
                mod.validate_waveform(path,dict(row,end_utc=str(UTCDateTime(1))))

    def test_header_coverage_keeps_channels_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);directory=root/'data/XX.TEST';directory.mkdir(parents=True)
            Stream([Trace(np.arange(10,dtype=np.int32),header=dict(network='XX',station='TEST',channel='HHZ',sampling_rate=1,starttime=UTCDateTime(0)))]).write(str(directory/'arbitrary.mseed'),format='MSEED')
            coverage=mod.local_coverage(root,{'XX.TEST'},0,20)
            rows=mod.waveform_plan({('XX.TEST..HHN',1):[(0,20)],('XX.TEST..HHZ',1):[(0,20)]},coverage,1)
            self.assertEqual([(r['seed_id'],float(UTCDateTime(r['start_utc']))) for r in rows],[('XX.TEST..HHN',0),('XX.TEST..HHZ',10)])


    def test_acquisition_rejects_bad_payload_and_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fixture=root/'fixture.mseed'
            Stream([Trace(np.arange(10,dtype=np.int32),header=dict(network='XX',station='TEST',channel='HHZ',sampling_rate=1,starttime=UTCDateTime(0)))]).write(str(fixture),format='MSEED')
            payload=fixture.read_bytes()
            row=dict(seed_id='XX.TEST..HHZ',sample_rate_hz=1,start_utc=str(UTCDateTime(0)),end_utc=str(UTCDateTime(10)))
            def fetch(session,url,params,path,retries,timeout):
                path.write_bytes(b'not a waveform' if 'scedc' in url else payload)
                return True
            with patch.object(mod,'download_response',side_effect=fetch):
                result=mod.acquire(row,'waveforms',root,None,['SCEDC','EARTHSCOPE'],1,1)
                self.assertEqual(result['provider'],'EARTHSCOPE')
                self.assertEqual(result['attempts'][0]['status'],'failed')
                self.assertEqual(result['attempts'][0]['phase'],'response_validation')
                self.assertTrue(result['attempts'][0]['message'])
                self.assertIn('location',result['attempts'][0])
                target=root/result['path'];before=target.stat().st_mtime_ns
                second=mod.acquire(row,'waveforms',root,None,['EARTHSCOPE'],1,1)
                self.assertEqual(second['status'],'already_saved')
                self.assertEqual(target.stat().st_mtime_ns,before)
                self.assertEqual(target.read_bytes(),payload)
                self.assertEqual(list(root.rglob('*.part')),[])

    def test_daily_file_fills_only_missing_samples_and_stays_single(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            row=dict(seed_id='XX.TEST..HHZ',sample_rate_hz=1,start_utc=str(UTCDateTime(0)),end_utc=str(UTCDateTime(10)))
            def write(name,offset,values):
                path=root/name
                Stream([Trace(np.array(values,dtype=np.int32),header=dict(network='XX',station='TEST',channel='HHZ',sampling_rate=1,starttime=UTCDateTime(offset)))]).write(str(path),format='MSEED')
                return path
            first=write('first.part',0,[0,1,2])
            dest,status,_,n=mod.save_daily(first,row,root)
            self.assertEqual(dest.name,'XX.TEST..HHZ__19700101T000000Z__19700102T000000Z.mseed')
            other=write('other.part',5,[5,6,7,8,9])
            mod.save_daily(other,row,root)
            from obspy import read
            self.assertEqual(sum(t.stats.npts for t in read(str(dest))),8)
            fill=write('fill.part',2,[2,3,4,5])
            _,status,previous,n=mod.save_daily(fill,row,root)
            self.assertEqual((status,n),('updated',2))
            self.assertIsNotNone(previous)
            result=read(str(dest));result.merge(method=-1)
            np.testing.assert_array_equal(result[0].data,np.arange(10))
            self.assertEqual(len(list(root.glob('*.mseed'))),1)

    def test_conflicting_overlap_leaves_original_bytes_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);incoming=root/'in.part'
            tr=Trace(np.arange(10,dtype=np.int32),header=dict(network='XX',station='TEST',channel='HHZ',sampling_rate=1,starttime=UTCDateTime(0)))
            row=dict(seed_id=tr.id,start_utc=str(UTCDateTime(0)),end_utc=str(UTCDateTime(10)),sample_rate_hz=1)
            Stream([tr]).write(str(incoming),format='MSEED')
            dest,*_=mod.save_daily(incoming,row,root);original=dest.read_bytes()
            tr.data[4]=999;Stream([tr]).write(str(incoming),format='MSEED')
            with self.assertRaises(mod.WaveformConflict):mod.save_daily(incoming,row,root)
            self.assertEqual(dest.read_bytes(),original)

    def test_midnight_sample_is_not_written_to_previous_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);incoming=root/'in.part'
            tr=Trace(np.array([1,2,3],dtype=np.int32),header=dict(network='XX',station='TEST',channel='HHZ',sampling_rate=1,starttime=UTCDateTime(86398)))
            Stream([tr]).write(str(incoming),format='MSEED')
            row=dict(seed_id=tr.id,start_utc=str(UTCDateTime(86398)),end_utc=str(UTCDateTime(86400)),sample_rate_hz=1)
            dest,*_=mod.save_daily(incoming,row,root)
            from obspy import read
            np.testing.assert_array_equal(read(str(dest))[0].data,[1,2])


if __name__=='__main__':
    unittest.main()
