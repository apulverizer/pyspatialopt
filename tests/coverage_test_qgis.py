# -*- coding: UTF-8 -*-
import qgis
import json
import logging
from analysis import pyqgis_analysis
import processing
from processing.core.Processing import Processing
import sys

if __name__ == "__main__":
    # supply path to qgis install location
    qgs = qgis.core.QgsApplication(sys.argv, True)
    qgs.setPrefixPath(r"C:\Program Files (x86)\QGIS Essen\apps\qgis", True)
    qgs.initQgis()
    Processing.initialize()
    Processing.updateAlgsList()

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # setup stream handler to console output
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Read the layers
    demand_polygon_fl = qgis.core.QgsVectorLayer(r"../sample_data/demand_polygon.shp", "demand_polygon_fl", "ogr")
    facility_service_areas_fl = qgis.core.QgsVectorLayer(r"../sample_data/facility_service_areas.shp",
                                                         "facility_service_areas_fl", "ogr")
    demand_point_fl = qgis.core.QgsVectorLayer(r"../sample_data/demand_point.shp", "demand_point_fl", "ogr")
    facility2_service_areas_fl = qgis.core.QgsVectorLayer(r"../sample_data/facility2_service_areas.shp",
                                                          "facility2_service_areas_fl", "ogr")

    # Test partial coverage generation
    partial_coverage1 = pyqgis_analysis.generate_partial_coverage(demand_polygon_fl, facility_service_areas_fl,
                                                                  "Population",
                                                                  "GEOID10", "ORIG_ID")
    # Test binary coverage (polygon) generation
    binary_coverage_polygon1 = pyqgis_analysis.generate_binary_coverage(demand_polygon_fl, facility_service_areas_fl,
                                                                        "Population", "GEOID10", "ORIG_ID")
    # Test binary coverage (point) generation
    binary_coverage_point1 = pyqgis_analysis.generate_binary_coverage(demand_point_fl, facility_service_areas_fl,
                                                                      "Population",
                                                                      "GEOID10", "ORIG_ID")
    # Test partial coverage generation
    partial_coverage2 = pyqgis_analysis.generate_partial_coverage(demand_polygon_fl, facility2_service_areas_fl,
                                                                  "Population",
                                                                  "GEOID10", "ORIG_ID")
    # Test binary coverage (polygon) generation
    binary_coverage_polygon2 = pyqgis_analysis.generate_binary_coverage(demand_polygon_fl, facility2_service_areas_fl,
                                                                        "Population", "GEOID10", "ORIG_ID")
    # Test binary coverage (point) generation
    binary_coverage_point2 = pyqgis_analysis.generate_binary_coverage(demand_point_fl, facility2_service_areas_fl,
                                                                      "Population",
                                                                      "GEOID10", "ORIG_ID")

    # Test serviceable demand (polygon) generation
    serviceable_demand_polygon = pyqgis_analysis.generate_serviceable_demand(demand_polygon_fl, "Population", "GEOID10",
                                                                             facility2_service_areas_fl,
                                                                             facility_service_areas_fl)
    # Test serviceable demand (point) generation
    serviceable_demand_point = pyqgis_analysis.generate_serviceable_demand(demand_point_fl, "Population", "GEOID10",
                                                                           facility2_service_areas_fl,
                                                                           facility_service_areas_fl)

    # Write the results to files
    with open("partial_coverage1_qgis.json", "w") as f:
        json.dump(partial_coverage1, f, indent=4, sort_keys=True)
    with open("binary_coverage_polygon1_qgis.json", "w") as f:
        json.dump(binary_coverage_polygon1, f, indent=4, sort_keys=True)
    with open("binary_coverage_point1_qgis.json", "w") as f:
        json.dump(binary_coverage_point1, f, indent=4, sort_keys=True)

    with open("partial_coverage2_qgis.json", "w") as f:
        json.dump(partial_coverage2, f, indent=4, sort_keys=True)
    with open("binary_coverage_polygon2_qgis.json", "w") as f:
        json.dump(binary_coverage_polygon2, f, indent=4, sort_keys=True)
    with open("binary_coverage_point2_qgis.json", "w") as f:
        json.dump(binary_coverage_point2, f, indent=4, sort_keys=True)

    with open("serviceable_demand_polygon_qgis.json", "w") as f:
        json.dump(serviceable_demand_polygon, f, indent=4, sort_keys=True)
    with open("serviceable_demand_point_qgis.json", "w") as f:
        json.dump(serviceable_demand_point, f, indent=4, sort_keys=True)
