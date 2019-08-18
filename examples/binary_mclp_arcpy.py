# -*- coding: UTF-8 -*-
import logging
import sys
import arcpy
import pulp
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

    # Read the demand polygon layer
    # Demand polygon shapefile has 212 polygons each where each feature has a demand (population) and unique identifier (GEOID10)
    demand_polygon_fl = arcpy.MakeFeatureLayer_management(r"../sample_data/demand_polygon.shp").getOutput(0)
    # Read the facility service area layer
    # Facility service area polygon layer has 8 polygons, where each feature has a unique identifier (ORIG_ID)
    facility_service_areas_fl = arcpy.MakeFeatureLayer_management(
        r"../sample_data/facility_service_areas.shp").getOutput(0)

    # Create binary coverage (polygon) dictionary structure
    # Use population of each polygon as demand,
    # Use GEOID as the unique field
    # Ue ORIG_ID as the unique id for the facilities
    binary_coverage_polygon = arcpy_analysis.generate_binary_coverage(demand_polygon_fl, facility_service_areas_fl,
                                                                      "Population",
                                                                      "GEOID10", "ORIG_ID")

    # Create the mclp model
    # Maximize the total coverage (binary polygon) using at most 5 out of 8 facilities
    logger.info("Creating MCLP model...")
    mclp = covering.create_mclp_model(binary_coverage_polygon, {"total": 5})
    # Solve the model using GLPK
    logger.info("Solving MCLP...")
    mclp.solve(pulp.GLPK())
    # Get the unique ids of the 5 facilities chosen
    logger.info("Extracting results")
    ids = utilities.get_ids(mclp, "facility_service_areas")
    # Generate a query that could be used as a definition query or selection in arcpy
    select_query = arcpy_analysis.generate_query(ids, unique_field_name="ORIG_ID")
    logger.info("Output query to use to generate maps is: {}".format(select_query))
    # Determine how much demand is covered by the results
    facility_service_areas_fl.definitionQuery = select_query
    total_coverage = arcpy_analysis.get_covered_demand(demand_polygon_fl, "Population", "binary",
                                                       facility_service_areas_fl)
    logger.info("{0:.2f}% of demand is covered".format((100 * total_coverage) / binary_coverage_polygon["totalDemand"]))
    