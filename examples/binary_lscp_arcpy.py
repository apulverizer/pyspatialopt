# -*- coding: UTF-8 -*-
import logging
import sys
import arcpy
import pulp
import os
from pyspatialopt.analysis import arcpy_analysis
from pyspatialopt.models import utilities
from pyspatialopt.models import covering


if __name__ == "__main__":
    # Initialize a logger so we get formatted output
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    # setup stream handler to console output
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # Read the demand polygon layer
    # Demand point shapefile has 212 points (centroids) each where each feature has a
    # demand (population) and unique identifier (GEOID10)
    demand_point_fl = arcpy.MakeFeatureLayer_management(os.path.join(scriptDir, r"../sample_data/demand_point.shp")).getOutput(0)
    # Read the facility service area layer
    # Facility service area polygon layer has 8 polygons, where each feature has a unique identifier (ORIG_ID)
    facility_service_areas_fl = arcpy.MakeFeatureLayer_management(os.path.join(scriptDir,
        r"../sample_data/facility_service_areas.shp")).getOutput(0)
    # Facility service area polygon layer has 23 polygons, where each feature has a unique identifier (ORIG_ID)
    facility2_service_areas_fl = arcpy.MakeFeatureLayer_management(os.path.join(scriptDir,
        r"../sample_data/facility2_service_areas.shp")).getOutput(0)

    # Create binary coverage (point) dictionary structure for each set of facilities since
    # LSCP requires complete coverage
    # we need to use both sets of facilities
    # Use population of each polygon as demand,
    # Use GEOID as the unique field
    # Ue ORIG_ID as the unique id for the facilities
    binary_coverage_point1 = arcpy_analysis.generate_binary_coverage(demand_point_fl, facility_service_areas_fl,
                                                                     "Population", "GEOID10", "ORIG_ID")
    binary_coverage_point2 = arcpy_analysis.generate_binary_coverage(demand_point_fl, facility2_service_areas_fl,
                                                                     "Population",
                                                                     "GEOID10", "ORIG_ID")
    # Merge the binary coverages together, serviceable area is auto-updated for binary coverage
    total_binary_coverage = covering.merge_coverages([binary_coverage_point1, binary_coverage_point2])

    # Create the mclp model
    # Maximize the total coverage (binary polygon) using at most 5 out of 8 facilities
    logger.info("Creating LSCP model...")
    lscp = covering.create_lscp_model(total_binary_coverage)
    # Solve the model using GLPK
    logger.info("Solving LSCP...")
    lscp.solve(pulp.GLPK())
    # Get the unique ids of the facilities chosen
    logger.info("Extracting results")
    ids = utilities.get_ids(lscp, "facility_service_areas")

    # how many ids selected?
    logger.info("How many facilities are selected? {}".format(len(ids) - 1))
    ids2 = utilities.get_ids(lscp, "facility2_service_areas")
    # Generate a query that could be used as a definition query or selection in arcpy
    select_query = arcpy_analysis.generate_query(ids, unique_field_name="ORIG_ID")
    # Generate a second query for the other layer
    select_query2 = arcpy_analysis.generate_query(ids2, unique_field_name="ORIG_ID")
    logger.info("Output query to use to generate maps is: {}".format(select_query))
    logger.info("Output query to use to generate maps is: {}".format(select_query2))
    # Determine how much demand is covered by the results
    facility_service_areas_fl.definitionQuery = select_query
    facility2_service_areas_fl.defintionQuery = select_query2
    total_coverage = arcpy_analysis.get_covered_demand(demand_point_fl, "Population", "binary",
                                                       facility_service_areas_fl, facility2_service_areas_fl)
    logger.info("{0:.2f}% of demand is covered".format((100 * total_coverage) / total_binary_coverage["totalDemand"]))
