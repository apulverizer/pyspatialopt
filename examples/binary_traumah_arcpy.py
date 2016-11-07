# -*- coding: UTF-8 -*-
import logging
import sys

import arcpy
import pulp
from pyspatialopt.analysis import arcpy_analysis
from pyspatialopt.models import covering
from pyspatialopt.models import utilities

if __name__ == "__main__":
    # Initialize a logger so we get formatted output
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    # setup stream handler to console output
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # The derived service areas from the demand points
    dl_service_area = arcpy.MakeFeatureLayer_management(r"../sample_data/demand_polygon.shp").getOutput(0)
    # The demand points
    dl = arcpy.MakeFeatureLayer_management(
        r"../sample_data/demand_point.shp").getOutput(0)
    # The Air Depot points
    ad_layer = arcpy.MakeFeatureLayer_management(
        r"../sample_data/facility.shp").getOutput(0)
    # The Trauma Center points
    tc_layer = arcpy.MakeFeatureLayer_management(
        r"../sample_data/facility2.shp").getOutput(0)

    # Generate the trauma coverage dictionary
    coverage = arcpy_analysis.generate_traumah_coverage(dl,dl_service_area,tc_layer,ad_layer,"Population",
                                                        5000,dl_id_field="GEOID10",tc_layer_id_field="ID",
                                                        ad_layer_id_field="ID")

    # Create the trauma Pulp linear programming problem
    # Use 5 Air Depot (Helicopter launch pads) and 10 Trauma Centers
    traumah = covering.create_traumah_model(coverage,5,10,"traumah.lp")

    # Solve the model using GLPK
    logger.info("Solving TRAUMAH...")
    traumah.solve(pulp.GLPK())

    # Get the unique ids of the 5 facilities chosen
    logger.info("Extracting results")
    ad_ids = utilities.get_ids(traumah, "AirDepot")
    tc_ids = utilities.get_ids(traumah, "TraumaCenter")
    # Generate a query that could be used as a definition query or selection in arcpy
    select_query = arcpy_analysis.generate_query(ad_ids, unique_field_name="ID")
    select_query2 = arcpy_analysis.generate_query(tc_ids, unique_field_name="ID")
    # Print the important results
    logger.info("Output query to use to generate maps (showing selected Air Depots) is: {}".format(select_query))
    logger.info("Output query to use to generate maps (showing selected Trauma Centers) is: {}".format(select_query2))
    logger.info("Total Population Covered: {}".format(pulp.value(traumah.objective)))
