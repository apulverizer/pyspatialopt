# -*- coding: UTF-8 -*-
import json
import unittest
import arcpy

from pyspatialopt.analysis import arcpy_analysis


class ArcpyCoverageTest(unittest.TestCase):
    def setUp(self):
        # Load layers
        self.demand_polygon_fl = arcpy.MakeFeatureLayer_management(r"../sample_data/demand_polygon.shp").getOutput(0)
        self.facility_service_areas_fl = arcpy.MakeFeatureLayer_management(
            r"../sample_data/facility_service_areas.shp").getOutput(0)
        self.demand_point_fl = arcpy.MakeFeatureLayer_management(r"../sample_data/demand_point.shp").getOutput(0)
        self.facility2_service_areas_fl = arcpy.MakeFeatureLayer_management(
            r"../sample_data/facility2_service_areas.shp").getOutput(0)

        # Load 'golden' coverages
        # Read the coverages
        with open("valid_coverages/partial_coverage1.json", "r") as f:
            self.partial_coverage = json.load(f)
        with open("valid_coverages/binary_coverage_polygon1.json", "r") as f:
            self.binary_coverage_polygon = json.load(f)
        with open("valid_coverages/binary_coverage_point1.json", "r") as f:
            self.binary_coverage_point = json.load(f)

        with open("valid_coverages/partial_coverage2.json", "r") as f:
            self.partial_coverage2 = json.load(f)
        with open("valid_coverages/binary_coverage_polygon2.json", "r") as f:
            self.binary_coverage_polygon2 = json.load(f)
        with open("valid_coverages/binary_coverage_point2.json", "r") as f:
            self.binary_coverage_point2 = json.load(f)

        with open("valid_coverages/serviceable_demand_polygon.json", "r") as f:
            self.serviceable_demand_polygon = json.load(f)
        with open("valid_coverages/serviceable_demand_point.json", "r") as f:
            self.serviceable_demand_point = json.load(f)

    def test_partial_coverage(self):
        partial_coverage = arcpy_analysis.generate_partial_coverage(self.demand_polygon_fl,
                                                                    self.facility_service_areas_fl,
                                                                    "Population",
                                                                    "GEOID10", "ORIG_ID")
        partial_coverage2 = arcpy_analysis.generate_partial_coverage(self.demand_polygon_fl,
                                                                     self.facility2_service_areas_fl,
                                                                     "Population",
                                                                     "GEOID10", "ORIG_ID")
        self.assertEqual(self.partial_coverage, partial_coverage)
        self.assertEqual(self.partial_coverage2, partial_coverage2)

    def test_binary_polygon_coverage(self):
        binary_coverage_polygon = arcpy_analysis.generate_binary_coverage(self.demand_polygon_fl,
                                                                          self.facility_service_areas_fl,
                                                                          "Population",
                                                                          "GEOID10", "ORIG_ID")
        binary_coverage_polygon2 = arcpy_analysis.generate_binary_coverage(self.demand_polygon_fl,
                                                                           self.facility2_service_areas_fl,
                                                                           "Population",
                                                                           "GEOID10", "ORIG_ID")
        self.assertEqual(self.binary_coverage_polygon, binary_coverage_polygon)
        self.assertEqual(self.binary_coverage_polygon2, binary_coverage_polygon2)

    def test_binary_point_coverage(self):
        binary_coverage_point = arcpy_analysis.generate_binary_coverage(self.demand_point_fl,
                                                                        self.facility_service_areas_fl,
                                                                        "Population",
                                                                        "GEOID10", "ORIG_ID")
        binary_coverage_point2 = arcpy_analysis.generate_binary_coverage(self.demand_point_fl,
                                                                         self.facility2_service_areas_fl,
                                                                         "Population",
                                                                         "GEOID10", "ORIG_ID")
        self.assertEqual(self.binary_coverage_point, binary_coverage_point)
        self.assertEqual(self.binary_coverage_point2, binary_coverage_point2)

    def test_serviceable_demand(self):
        serviceable_demand_polygon = arcpy_analysis.generate_serviceable_demand(self.demand_polygon_fl, "Population",
                                                                                "GEOID10",
                                                                                self.facility2_service_areas_fl,
                                                                                self.facility_service_areas_fl)

        serviceable_demand_point = arcpy_analysis.generate_serviceable_demand(self.demand_point_fl, "Population",
                                                                              "GEOID10",
                                                                              self.facility2_service_areas_fl,
                                                                              self.facility_service_areas_fl)
        self.assertEqual(self.serviceable_demand_point, serviceable_demand_point)
        self.assertEqual(self.serviceable_demand_polygon, serviceable_demand_polygon)


if __name__ == '__main__':
    unittest.main()
