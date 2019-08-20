# -*- coding: UTF-8 -*-
import logging
import pulp
import csv
import os
from pyspatialopt.models import utilities
from pyspatialopt.models import covering


def generate_binary_coverage_from_dist_matrix(
    list_dict_facility_demand_distance, dist_threshold,
    dl_id_field="demand_id", fl_id_field="facility_id",
    demand_field="demand", distance_field="distance", fl_variable_name=None):
    """
    Generates a dictionary representing the binary coverage of a facility to demand points
    :param list_dict_facility_demand_distance: (string) A dictionary containing pairwise distance and demand
    :param dist_threshold：(numeric) The distance threshold
    :param dl_id_field: (string) The name of the demand point id field in the list_dict_facility_demand_distance object
    :param fl_id_field: (string) The name of the facility id field in the list_dict_facility_demand_distance object AND fl
    :param demand_field: (string) The name of demand weight field in the list_dict_facility_demand_distance object
    :param distance_field: (string) The name of distance in metres field in the list_dict_facility_demand_distance object
    :param fl_variable_name: (string) The name to use to represent the facility variable
    :return: (dictionary) A nested dictionary storing the coverage relationships
    """

    if fl_variable_name is None:
        fl_variable_name = "facility"

    output = {
        "version": "1",
        "type": {
            "mode": "coverage",
            "type": "binary",
        },
        "demand": {},
        "totalDemand": 0.0,
        "totalServiceableDemand": 0.0,
        "facilities": {fl_variable_name: []}
    }

    set_facility_id = set()
    set_demand_id = set()
    for row in list_dict_facility_demand_distance:
        set_facility_id.add(str(row[fl_id_field]))
        # test if this demand id is contained
        new_demand_id = str(row[dl_id_field])
        if new_demand_id not in set_demand_id:
            output["demand"][new_demand_id] = {
                "area": 0,
                "demand": float(row[demand_field]),
                "serviceableDemand": 0.0,
                "coverage": {fl_variable_name: {}}
            }
            set_demand_id.add(new_demand_id)

    # add facility IDs to facilities
    for facility_id in set_facility_id:
        output["facilities"][fl_variable_name].append(facility_id)

    # Determining binary coverage for each demand unit
    for row in list_dict_facility_demand_distance:
        if float(row[distance_field]) <= dist_threshold:
            output["demand"][str(row[dl_id_field])]["serviceableDemand"] = \
                output["demand"][str(row[dl_id_field])]["demand"]
            output["demand"][str(row[dl_id_field])]["coverage"][fl_variable_name][str(row[fl_id_field])] = 1

    # summary
    for row in output["demand"].values():
        output["totalServiceableDemand"] += row["serviceableDemand"]
        output["totalDemand"] += row["demand"]
    logging.getLogger().info("Binary coverage successfully generated.")
    return output


def binary_mclp_distance_matrix(file_distance_matrix, service_dist, num_facility, list_field_req=None, facility_variable_name="facility", workspace_path="."):
    """
    Solve a binary and point-based MCLP based on a distance matrix
    :param file_distance_matrix: (string) file name of a distance matrix. CSV format.
    :param service_dist: (numeric) maximum service distance
    :param num_facility: (integer) number of facilities to locate
    :param list_field_req: (list of string) a list of fields in the file_distance_matrix
    :param facility_variable_name: (string) facility variable name in the coverage object
    :param workspace_path: (string) the folder path of file_distance_matrix
    :return: (dictionary) A dictionary storing the coverage result
    """

    if list_field_req is None:
        list_field_req = ["facility_id", "demand_id", "demand", "distance"]
    # read the distance matrix
    with open(os.path.join(workspace_path, file_distance_matrix)) as csvfile:
        dict_pairwise_distance = [
            {k: v for k, v in row.items()}
            for row in csv.DictReader(csvfile, skipinitialspace=True)
            ]

    # The file should contain the required fields. If not, exit
    item_pairwise_distance = dict_pairwise_distance[1]

    for field in list_field_req:
        if field not in item_pairwise_distance.keys():
            print("Error: this field {} not found in the distance csv".format(field))
            sys.exit(0)

    # creat a coverage object. Need to write a new function
    dict_coverage = generate_binary_coverage_from_dist_matrix(
        list_dict_facility_demand_distance=dict_pairwise_distance,
        dl_id_field="demand_id", fl_id_field="facility_id",
        dist_threshold=service_dist, demand_field="demand",
        distance_field="distance", fl_variable_name=facility_variable_name
        )

    # formulate model
    mclp = covering.create_mclp_model(dict_coverage, {"total": num_facility})

    # solve
    mclp.solve(pulp.GLPK())

    # Get the id set of facilities chosen
    set_facility_id_chosen = set(utilities.get_ids(mclp, facility_variable_name))

    # Query the demand covered from the dict_coverage
    total_demand_covered = 0.0

    for demand_id, demand_obj in dict_coverage["demand"].items():
        # if this demand_id is covered by any facility in ids
        if not set_facility_id_chosen.isdisjoint(demand_obj["coverage"]["facility"].keys()):
            total_demand_covered += demand_obj["demand"]

    result_coverage = {
        "number_facility": num_facility,
        "number_facility_chosen": len(set_facility_id_chosen),
        "set_facility_id_chosen": set_facility_id_chosen,
        "total_demand": dict_coverage["totalDemand"],
        "percent_demand_coverage": (100 * total_demand_covered) /
        dict_coverage["totalDemand"],
        }
    return result_coverage
