# -*- coding: UTF-8 -*-
import arcpy
import json
import logging
import sys
from analysis import arcpy_analysis

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # setup stream handler to console output
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Read the layers
    demand_polygon_fl = arcpy.MakeFeatureLayer_management(r"../sample_data/demand_polygon.shp").getOutput(0)
    facility_service_areas_fl = arcpy.MakeFeatureLayer_management(
        r"../sample_data/facility_service_areas.shp").getOutput(0)
    demand_point_fl = arcpy.MakeFeatureLayer_management(r"../sample_data/demand_point.shp").getOutput(0)
    facility2_service_areas_fl = arcpy.MakeFeatureLayer_management(
        r"../sample_data/facility2_service_areas.shp").getOutput(0)

    # Test partial coverage generation
    partial_coverage1 = arcpy_analysis.generate_partial_coverage(demand_polygon_fl, facility_service_areas_fl,
                                                                 "Population",
                                                                 "GEOID10", "ORIG_ID")
    # Test binary coverage (polygon) generation
    binary_coverage_polygon1 = arcpy_analysis.generate_binary_coverage(demand_polygon_fl, facility_service_areas_fl,
                                                                       "Population",
                                                                       "GEOID10", "ORIG_ID")
    # Test binary coverage (point) generation
    binary_coverage_point1 = arcpy_analysis.generate_binary_coverage(demand_point_fl, facility_service_areas_fl,
                                                                     "Population",
                                                                     "GEOID10", "ORIG_ID")
    # Test partial coverage generation
    partial_coverage2 = arcpy_analysis.generate_partial_coverage(demand_polygon_fl, facility2_service_areas_fl,
                                                                 "Population",
                                                                 "GEOID10", "ORIG_ID")
    # Test binary coverage (polygon) generation
    binary_coverage_polygon2 = arcpy_analysis.generate_binary_coverage(demand_polygon_fl, facility2_service_areas_fl,
                                                                       "Population",
                                                                       "GEOID10", "ORIG_ID")
    # Test binary coverage (point) generation
    binary_coverage_point2 = arcpy_analysis.generate_binary_coverage(demand_point_fl, facility2_service_areas_fl,
                                                                     "Population",
                                                                     "GEOID10", "ORIG_ID")

    # Test serviceable demand (polygon) generation
    serviceable_demand_polygon = arcpy_analysis.generate_serviceable_demand(demand_polygon_fl, "Population", "GEOID10",
                                                                            facility2_service_areas_fl,
                                                                            facility_service_areas_fl)
    # Test serviceable demand (point) generation
    serviceable_demand_point = arcpy_analysis.generate_serviceable_demand(demand_point_fl, "Population", "GEOID10",
                                                                          facility2_service_areas_fl,
                                                                          facility_service_areas_fl)

    # Write the results to files
    with open("partial_coverage1.json", "w") as f:
        json.dump(partial_coverage1, f, indent=4, sort_keys=True)
    with open("binary_coverage_polygon1.json", "w") as f:
        json.dump(binary_coverage_polygon1, f, indent=4, sort_keys=True)
    with open("binary_coverage_point1.json", "w") as f:
        json.dump(binary_coverage_point1, f, indent=4, sort_keys=True)

    with open("partial_coverage2.json", "w") as f:
        json.dump(partial_coverage2, f, indent=4, sort_keys=True)
    with open("binary_coverage_polygon2.json", "w") as f:
        json.dump(binary_coverage_polygon2, f, indent=4, sort_keys=True)
    with open("binary_coverage_point2.json", "w") as f:
        json.dump(binary_coverage_point2, f, indent=4, sort_keys=True)

    with open("serviceable_demand_polygon.json", "w") as f:
        json.dump(serviceable_demand_polygon, f, indent=4, sort_keys=True)
    with open("serviceable_demand_point.json", "w") as f:
        json.dump(serviceable_demand_point, f, indent=4, sort_keys=True)
