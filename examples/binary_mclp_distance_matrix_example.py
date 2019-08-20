# -*- coding: UTF-8 -*-

import logging
import sys
import arcpy
import pulp
import csv
import sys
import os
from pyspatialopt.analysis import arcpy_analysis
from pyspatialopt.models import utilities
from pyspatialopt.models import covering
from pyspatialopt.models import binary_mclp_distance_matrix

if __name__ == "__main__":
    # Initialize a logger so we get formatted output
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    # setup stream handler to console output
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    import os
    scriptDir = os.path.dirname(os.path.realpath(__file__))

    # a distance matrix file (format of csv)

    workspace_path = r"../sample_data"
    file_distance_matrix = r'service_area_demand_point_distance_matrix.csv'
    service_dist = 5000
    num_facility = 5

    # This file should contain the following fields: facility_id, demand_id, demand, distance
    list_field_req = ["facility_id", "demand_id", "demand", "distance"]

    # do not change this variable unless you understand what it is
    facility_variable_name = "facility"
    # read the distance matrix
    with open(os.path.join(workspace_path, file_distance_matrix)) as csvfile:
        dict_pairwise_distance = [
            {k: v for k, v in row.items()}
            for row in csv.DictReader(csvfile, skipinitialspace=True)
            ]

    # test if it contains the required field
    item_pairwise_distance = dict_pairwise_distance[1]

    for field in list_field_req:
        if field not in item_pairwise_distance.keys():
            logger.info("Error: this field {} not found in the distance csv".format(field))
            sys.exit(0)
    logger.info(dict_pairwise_distance[1])

    dict_coverage = binary_mclp_distance_matrix.generate_binary_coverage_from_dist_matrix(
        list_dict_facility_demand_distance=dict_pairwise_distance,
        dl_id_field="demand_id", fl_id_field="facility_id",
        dist_threshold=service_dist, demand_field="demand",
        distance_field="distance", fl_variable_name=facility_variable_name
        )

    # formulate model
    logger.info("Creating MCLP model...")
    mclp = covering.create_mclp_model(dict_coverage, {"total": num_facility})

    # solve
    logger.info("Solving MCLP...")
    mclp.solve(pulp.GLPK())

    # Get the unique ids of the facilities chosen
    logger.info("Extracting results")

    # Get the id set of facilities chosen
    set_facility_id_chosen = set(utilities.get_ids(mclp, facility_variable_name))

    logger.info("Set of facility ids: {}".format(set_facility_id_chosen))
    logger.info("Number of facilities selected: {}".format(
        len(set_facility_id_chosen))
        )

    # Query the demand covered from the dict_coverage
    total_demand_covered = 0.0

    for demand_id, demand_obj in dict_coverage["demand"].items():
        # if this demand_id is covered by any facility in ids
        if not set_facility_id_chosen.isdisjoint(demand_obj["coverage"]["facility"].keys()):
            total_demand_covered += demand_obj["demand"]

    logger.info("{0:.2f}% of demand is covered".format((100 * total_demand_covered) / dict_coverage["totalDemand"]))

    # An easy way: use the binary_mclp_distance_matrix function
    result_coverage = binary_mclp_distance_matrix.binary_mclp_distance_matrix(file_distance_matrix=file_distance_matrix, service_dist=service_dist, num_facility=num_facility, workspace_path=workspace_path)
    logger.info(result_coverage)
