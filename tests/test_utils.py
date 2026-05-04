import unittest
import math
from theodolite_mcp.domain.logic import dms_to_decimal, decimal_to_dms, normalize_angle

class TestUtils(unittest.TestCase):
    def test_dms_conversions(self):
        # 30 deg 15 min 45 sec
        decimal = dms_to_decimal(30, 15, 45)
        self.assertAlmostEqual(decimal, 30.2625)
        
        d, m, s = decimal_to_dms(30.2625)
        self.assertEqual(d, 30)
        self.assertEqual(m, 15)
        self.assertAlmostEqual(s, 45.0)

    def test_normalize_angle(self):
        self.assertEqual(normalize_angle(370), 10)
        self.assertEqual(normalize_angle(-10), 350)
        self.assertEqual(normalize_angle(360), 0)

    def test_azimuth_calculation_logic(self):
        # Test basic quadrants
        # dx=1, dy=0 -> Azimuth 0 (North/X-axis)
        def calc_az(x1, y1, x2, y2):
            dx = x2 - x1
            dy = y2 - y1
            return normalize_angle(math.degrees(math.atan2(dy, dx)))

        self.assertAlmostEqual(calc_az(0,0, 1,0), 0.0)   # North
        self.assertAlmostEqual(calc_az(0,0, 0,1), 90.0)  # East
        self.assertAlmostEqual(calc_az(0,0, -1,0), 180.0) # South
        self.assertAlmostEqual(calc_az(0,0, 0,-1), 270.0) # West

if __name__ == "__main__":
    unittest.main()
