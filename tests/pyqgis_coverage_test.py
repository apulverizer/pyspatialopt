# -*- coding: UTF-8 -*-
import json
import os
import qgis
import sys
import unittest
from processing.core.Processing import Processing
from pyspatialopt.analysis import pyqgis_analysis


class PyQGISCoverageTest(unittest.TestCase):
    def setUp(self):
        # setup Qgis
        qgs = qgis.core.QgsApplication(sys.argv, True)
        qgs.setPrefixPath(os.path.expandvars(r"$QGIS_PATH"), True)
        qgs.initQgis()
        Processing.initialize()
        Processing.updateAlgsList()

        # Load layers
        self.demand_polygon_fl = qgis.core.QgsVectorLayer(r"../sample_data/demand_polygon.shp", "demand_polygon_fl",
                                                          "ogr")
        self.facility_service_areas_fl = qgis.core.QgsVectorLayer(r"../sample_data/facility_service_areas.shp",
                                                                  "facility_service_areas_fl", "ogr")
        self.demand_point_fl = qgis.core.QgsVectorLayer(r"../sample_data/demand_point.shp", "demand_point_fl", "ogr")
        self.facility2_service_areas_fl = qgis.core.QgsVectorLayer(r"../sample_data/facility2_service_areas.shp",
                                                                   "facility2_service_areas_fl", "ogr")
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
        partial_coverage = pyqgis_analysis.generate_partial_coverage(self.demand_polygon_fl,
                                                                     self.facility_service_areas_fl,
                                                                     "Population",
                                                                     "GEOID10", "ORIG_ID")
        partial_coverage2 = pyqgis_analysis.generate_partial_coverage(self.demand_polygon_fl,
                                                                      self.facility2_service_areas_fl,
                                                                      "Population",
                                                                      "GEOID10", "ORIG_ID")
        self.assertEqual(self.partial_coverage, partial_coverage)
        self.assertEqual(self.partial_coverage2, partial_coverage2)

    def test_binary_polygon_coverage(self):
        binary_coverage_polygon = pyqgis_analysis.generate_binary_coverage(self.demand_polygon_fl,
                                                                           self.facility_service_areas_fl,
                                                                           "Population",
                                                                           "GEOID10", "ORIG_ID")
        binary_coverage_polygon2 = pyqgis_analysis.generate_binary_coverage(self.demand_polygon_fl,
                                                                            self.facility2_service_areas_fl,
                                                                            "Population",
                                                                            "GEOID10", "ORIG_ID")
        self.assertEqual(self.binary_coverage_polygon, binary_coverage_polygon)
        self.assertEqual(self.binary_coverage_polygon2, binary_coverage_polygon2)

    def test_binary_point_coverage(self):
        binary_coverage_point = pyqgis_analysis.generate_binary_coverage(self.demand_point_fl,
                                                                         self.facility_service_areas_fl,
                                                                         "Population",
                                                                         "GEOID10", "ORIG_ID")
        binary_coverage_point2 = pyqgis_analysis.generate_binary_coverage(self.demand_point_fl,
                                                                          self.facility2_service_areas_fl,
                                                                          "Population",
                                                                          "GEOID10", "ORIG_ID")
        self.assertEqual(self.binary_coverage_point, binary_coverage_point)
        self.assertEqual(self.binary_coverage_point2, binary_coverage_point2)

    def test_serviceable_demand(self):
        serviceable_demand_polygon = pyqgis_analysis.generate_serviceable_demand(self.demand_polygon_fl, "Population",
                                                                                 "GEOID10",
                                                                                 self.facility2_service_areas_fl,
                                                                                 self.facility_service_areas_fl)

        serviceable_demand_point = pyqgis_analysis.generate_serviceable_demand(self.demand_point_fl, "Population",
                                                                               "GEOID10",
                                                                               self.facility2_service_areas_fl,
                                                                               self.facility_service_areas_fl)
        self.assertEqual(self.serviceable_demand_point, serviceable_demand_point)
        self.assertEqual(self.serviceable_demand_polygon, serviceable_demand_polygon)


if __name__ == '__main__':
    unittest.main()
