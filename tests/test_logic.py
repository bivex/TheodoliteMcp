import unittest
from theodolite_mcp.domain.models import Point, Observation, TraverseData
from theodolite_mcp.domain.logic import calculate_traverse

class TestTraverseLogic(unittest.TestCase):
    def test_simple_open_traverse(self):
        # Starting at (0,0), looking North (Azimuth 0)
        # Move 100 units North
        # At (0, 100), turn 90 degrees Right, move 100 units
        
        start_point = Point(name="A", x=0.0, y=0.0)
        obs1 = Observation(point_name="B", horizontal_angle=180.0, distance=100.0) # 180 means keep going straight
        obs2 = Observation(point_name="C", horizontal_angle=90.0, distance=100.0)  # 90 means turn right
        
        # Alpha_next = Alpha_prev + Beta - 180
        # leg 1: 0 + 180 - 180 = 0. Azimuth 0. (dN=100, dE=0) -> (100, 0) in North-East coords
        # NOTE: My logic uses math.cos(radians(azimuth)) for DX and sin for DY.
        # If Azimuth 0: cos(0)=1, sin(0)=0. So X increases (North).
        
        data = TraverseData(
            start_point=start_point,
            start_azimuth=0.0,
            observations=[obs1, obs2],
            is_closed=False
        )
        
        result = calculate_traverse(data)
        
        self.assertEqual(len(result.points), 3)
        self.assertAlmostEqual(result.points[1].x, 100.0)
        self.assertAlmostEqual(result.points[1].y, 0.0)
        
        # leg 2: Azimuth_prev=0, Beta=90. Azimuth_next = 0 + 90 - 180 = -90 = 270.
        # cos(270)=0, sin(270)=-1. So X=100+0=100, Y=0-100=-100.
        self.assertAlmostEqual(result.points[2].x, 100.0)
        self.assertAlmostEqual(result.points[2].y, -100.0)

    def test_closed_traverse_adjustment(self):
        # Square 100x100
        # Theoretical sum of interior angles for 4 points is (4-2)*180 = 360
        # Let's say we have 4 observations with 91 degrees each (error)
        start_point = Point(name="P1", x=0.0, y=0.0)
        obs = [
            Observation(point_name="P2", horizontal_angle=90.1, distance=100.0),
            Observation(point_name="P3", horizontal_angle=90.1, distance=100.0),
            Observation(point_name="P4", horizontal_angle=90.1, distance=100.0),
            Observation(point_name="P1_back", horizontal_angle=90.1, distance=100.0),
        ]
        
        data = TraverseData(
            start_point=start_point,
            start_azimuth=0.0,
            observations=obs,
            is_closed=True
        )
        
        result = calculate_traverse(data)
        # Misclosure should be 4 * 0.1 = 0.4
        self.assertAlmostEqual(result.angular_misclosure, 0.4)
        # End point should be back at (0,0) after adjustment
        self.assertAlmostEqual(result.points[-1].x, 0.0)
        self.assertAlmostEqual(result.points[-1].y, 0.0)

if __name__ == "__main__":
    unittest.main()
