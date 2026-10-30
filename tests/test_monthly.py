import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from meteo_audit.monthly import months

class LocalCalendarTests(unittest.TestCase):
    def test_month_boundaries_follow_local_dst(self):
        tz = ZoneInfo('Europe/Prague')
        starts = list(months(2010, 2010))
        march_start, march_stop = starts[2]
        self.assertEqual(march_start, datetime(2010, 3, 1, tzinfo=tz))
        self.assertEqual(march_stop, datetime(2010, 4, 1, tzinfo=tz))
        self.assertEqual(int(march_stop.timestamp() - march_start.timestamp()), 31 * 86400 - 3600)

if __name__ == '__main__':
    unittest.main()
