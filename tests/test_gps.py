"""Tests for GPS coordinate parsing."""

import unittest

from metochina.core.gps import _dms_to_decimal, _rational_to_float, parse_gps_info


class MockRational:
    """Mock Pillow IFDRational for testing."""

    def __init__(self, numerator: int, denominator: int):
        self.numerator = numerator
        self.denominator = denominator


class TestRationalToFloat(unittest.TestCase):

    def test_plain_float(self):
        self.assertAlmostEqual(_rational_to_float(3.14), 3.14)

    def test_plain_int(self):
        self.assertAlmostEqual(_rational_to_float(42), 42.0)

    def test_ifd_rational(self):
        r = MockRational(1, 2)
        self.assertAlmostEqual(_rational_to_float(r), 0.5)

    def test_tuple_rational(self):
        self.assertAlmostEqual(_rational_to_float((3, 4)), 0.75)

    def test_zero_denominator_ifd(self):
        r = MockRational(1, 0)
        self.assertIsNone(_rational_to_float(r))

    def test_zero_denominator_tuple(self):
        self.assertIsNone(_rational_to_float((5, 0)))

    def test_none_input(self):
        self.assertIsNone(_rational_to_float(None))


class TestDmsToDecimal(unittest.TestCase):

    def test_north_positive(self):
        # 40 deg 25' 0.36"
        dms = (MockRational(40, 1), MockRational(25, 1), MockRational(36, 100))
        result = _dms_to_decimal(dms, "N")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result, 40.4168, places=3)

    def test_south_negative(self):
        dms = (MockRational(33, 1), MockRational(51, 1), MockRational(54, 1))
        result = _dms_to_decimal(dms, "S")
        self.assertIsNotNone(result)
        self.assertLess(result, 0)

    def test_east_positive(self):
        dms = (MockRational(2, 1), MockRational(21, 1), MockRational(7, 1))
        result = _dms_to_decimal(dms, "E")
        self.assertIsNotNone(result)
        self.assertGreater(result, 0)

    def test_west_negative(self):
        dms = (MockRational(3, 1), MockRational(42, 1), MockRational(13, 1))
        result = _dms_to_decimal(dms, "W")
        self.assertIsNotNone(result)
        self.assertLess(result, 0)

    def test_none_input(self):
        self.assertIsNone(_dms_to_decimal(None))

    def test_invalid_tuple_length(self):
        self.assertIsNone(_dms_to_decimal((1, 2)))

    def test_no_ref(self):
        dms = (MockRational(40, 1), MockRational(0, 1), MockRational(0, 1))
        result = _dms_to_decimal(dms)
        self.assertAlmostEqual(result, 40.0, places=4)


class TestParseGpsInfo(unittest.TestCase):

    def test_empty_dict(self):
        gps = parse_gps_info({})
        self.assertFalse(gps.has_coordinates)

    def test_full_gps(self):
        gps_dict = {
            "GPSLatitude": (MockRational(48, 1), MockRational(51, 1), MockRational(24, 1)),
            "GPSLatitudeRef": "N",
            "GPSLongitude": (MockRational(2, 1), MockRational(21, 1), MockRational(7, 1)),
            "GPSLongitudeRef": "E",
            "GPSAltitude": MockRational(35, 1),
            "GPSAltitudeRef": 0,
            "GPSMapDatum": "WGS-84",
        }
        gps = parse_gps_info(gps_dict)
        self.assertTrue(gps.has_coordinates)
        self.assertAlmostEqual(gps.latitude, 48.8567, places=3)
        self.assertAlmostEqual(gps.longitude, 2.3519, places=3)
        self.assertAlmostEqual(gps.altitude, 35.0)
        self.assertEqual(gps.altitude_ref, "Above sea level")
        self.assertEqual(gps.datum, "WGS-84")

    def test_below_sea_level(self):
        gps_dict = {
            "GPSLatitude": (MockRational(31, 1), MockRational(30, 1), MockRational(0, 1)),
            "GPSLatitudeRef": "N",
            "GPSLongitude": (MockRational(35, 1), MockRational(28, 1), MockRational(0, 1)),
            "GPSLongitudeRef": "E",
            "GPSAltitude": MockRational(430, 1),
            "GPSAltitudeRef": 1,
        }
        gps = parse_gps_info(gps_dict)
        self.assertEqual(gps.altitude_ref, "Below sea level")
        self.assertLess(gps.altitude, 0)

    def test_speed_and_direction(self):
        gps_dict = {
            "GPSSpeed": MockRational(60, 1),
            "GPSSpeedRef": "K",
            "GPSImgDirection": MockRational(180, 1),
            "GPSImgDirectionRef": "T",
        }
        gps = parse_gps_info(gps_dict)
        self.assertAlmostEqual(gps.speed, 60.0)
        self.assertEqual(gps.speed_ref, "K")
        self.assertAlmostEqual(gps.direction, 180.0)

    def test_timestamp(self):
        gps_dict = {
            "GPSTimeStamp": (MockRational(12, 1), MockRational(30, 1), MockRational(45, 1)),
            "GPSDateStamp": "2024:06:15",
        }
        gps = parse_gps_info(gps_dict)
        self.assertEqual(gps.timestamp, "2024-06-15T12:30:45Z")


if __name__ == "__main__":
    unittest.main()
