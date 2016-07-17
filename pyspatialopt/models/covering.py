# -*- coding: UTF-8 -*-
import copy
import pulp


def update_serviceable_demand(coverage, sd):
    """
    Updates a coverage with new values from a serviceable demand dict

    :param coverage: (dict) The coverage to update
    :param sd: (dict) The corresponding serviceable demand to use as update
    :return: (dict) The coverage with the updated serviceable demands
    """
    total_serviceable_demand = 0.0
    for demand in coverage["demand"].keys():
        coverage["demand"][demand]["serviceableDemand"] = sd["demand"][demand]["serviceableDemand"]
        total_serviceable_demand += sd["demand"][demand]["serviceableDemand"]
    coverage["totalServiceableDemand"] = total_serviceable_demand
    return coverage


def validate_coverage(coverage_dict, modes, types):
    """
    Validates a coverage. Only certain coverages work in certain models
    :param coverage_dict: (dictionary) The coverage dictionary to validate
    :param modes: (list) A list of acceptable modes
    :param types: (list) A list of acceptable types
    :return:
    """
    if "type" not in coverage_dict:
        raise KeyError("'type' not found in coverage_dict")
    if "type" not in coverage_dict["type"]:
        raise KeyError("'type' not found in coverage_dict['type']")
    if coverage_dict["type"]["type"] not in types:
        raise ValueError("Expected types: '{}' got type '{}'".format(types, coverage_dict["type"]["type"]))
    if "mode" not in coverage_dict["type"]:
        raise KeyError("'mode' not found in coverage_dict['type']")
    if coverage_dict["type"]["mode"] not in modes:
        raise ValueError("Expected modes: '{}' got mode '{}'".format(modes, coverage_dict["type"]["mode"]))


def merge_coverages(coverages):
    """

    Combines multiple coverage dictionaries to form a 'master' coverage. Generally used if siting
    multiple types of facilities. Does NOT update serviceable area for partial coverage! Need to merge & dissolve all facility layers

    :param coverages: (list of dicts) The coverage dictionaries to combine
    :return: (dict) A nested dictionary storing the coverage relationships
    """
    facility_types = []
    demand_keys = []
    coverage_type = None
    for coverage in coverages:
        # make sure all coverages are of the same type (binary, partial)
        if coverage_type is None:
            coverage_type = coverage["type"]["type"]
        validate_coverage(coverage, ["coverage"], [coverage_type])
        # make sure all coverages contain unique facility types
        for facility_type in coverage["facilities"].items():
            if facility_type not in facility_types:
                facility_types.append(facility_type)
            else:
                raise ValueError("Conflicting facility types")
        demand_keys.append(set(coverage["demand"].keys()))
    # Check to make sure all demand indicies are present in all coverages
    for keys in demand_keys:
        for keys2 in demand_keys:
            if keys != keys2:
                raise ValueError("Demand Keys Invalid")

    master_coverage = copy.deepcopy(coverages[0])
    for c in coverages[1:]:
        coverage = copy.deepcopy(c)
        for facility_type in coverage["facilities"].keys():
            if facility_type not in master_coverage["facilities"]:
                master_coverage["facilities"][facility_type] = {}
            master_coverage["facilities"][facility_type] = coverage["facilities"][facility_type]

        for demand in coverage["demand"].keys():
            for facility_type in coverage["demand"][demand]["coverage"].keys():
                if facility_type not in master_coverage["demand"][demand]["coverage"]:
                    master_coverage["demand"][demand]["coverage"][facility_type] = {}
                for fac in coverage["demand"][demand]["coverage"][facility_type].keys():
                    master_coverage["demand"][demand]["coverage"][facility_type][fac] = \
                        coverage["demand"][demand]["coverage"][facility_type][fac]
                    # Update serviceable demand for binary coverage
                    if coverage_type == "Binary" and coverage["demand"][demand]["coverage"][facility_type][fac] == 1:
                        master_coverage["demand"][demand]["serviceableDemand"] = coverage["demand"][demand]["coverage"][
                            "demand"]
    return master_coverage


def create_mclp_model(coverage_dict, num_fac, model_file, delineator="$", use_serviceable_demand=False):
    """

    Creates an MCLP model using the provided coverage and parameters
    Writes a .lp file which can be solved with Gurobi

    Church, Richard, and Charles R Velle. 1974. The maximal covering location problem.
    Papers in regional science 32 (1):101-118.

    :param coverage_dict: (dictionary) The coverage to use to generate the model
    :param num_fac: (dictionary) The dictionary of number of facilities to use
    :param model_file: (string) The model file to output
    :param delineator: (string) The character/symbol used to delineate facility and id
    :param use_serviceable_demand: (bool) Should we use the serviceable demand rather than demand
    :return: (Pulp problem) The problem to solve
    """
    if use_serviceable_demand:
        demand_var = "serviceableDemand"
    else:
        demand_var = "demand"
    if not isinstance(coverage_dict, dict):
        raise TypeError("coverage_dict is not a dictionary")
    if not (isinstance(model_file, str)):
        raise TypeError("model_file is not a string")
    if not isinstance(num_fac, dict):
        raise TypeError("num_fac is not a dictionary")
    if not isinstance(delineator, str):
        raise TypeError("delineator is not a string")
    validate_coverage(coverage_dict, ["coverage"], ["binary"])
    # create the variables
    demand_vars = {}
    for demand_id in coverage_dict["demand"]:
        demand_vars[demand_id] = pulp.LpVariable("Y{}{}".format(delineator, demand_id), 0, 1, pulp.LpInteger)
    facility_vars = {}
    for facility_type in coverage_dict["facilities"]:
        facility_vars[facility_type] = {}
        for facility_id in coverage_dict["facilities"][facility_type]:
            facility_vars[facility_type][facility_id] = \
                pulp.LpVariable("{}{}{}".format(facility_type, delineator, facility_id), 0, 1, pulp.LpInteger)
    # create the problem
    prob = pulp.LpProblem("MCLP", pulp.LpMaximize)
    # add objective
    prob += pulp.lpSum([coverage_dict["demand"][demand_id][demand_var] * demand_vars[demand_id] for demand_id in
                        coverage_dict["demand"]])
    # add coverage constraints
    for demand_id in coverage_dict["demand"]:
        to_sum = []
        for facility_type in coverage_dict["demand"][demand_id]["coverage"]:
            for facility_id in coverage_dict["demand"][demand_id]["coverage"][facility_type]:
                to_sum.append(facility_vars[facility_type][facility_id])
        prob += pulp.lpSum(to_sum) - demand_vars[demand_id] >= 0, "D{}".format(demand_id)
    # Number of total facilities
    to_sum = []
    for facility_type in coverage_dict["facilities"]:
        for facility_id in coverage_dict["facilities"][facility_type]:
            to_sum.append(facility_vars[facility_type][facility_id])
    prob += pulp.lpSum(to_sum) <= num_fac["total"], "NumTotalFacilities"
    # Number of other facility types
    for facility_type in coverage_dict["facilities"].keys():
        if facility_type in num_fac and facility_type != "total":
            to_sum = []
            for facility_id in coverage_dict["facilities"][facility_type]:
                to_sum.append(facility_vars[facility_type][facility_id])
            prob += pulp.lpSum(to_sum) <= num_fac[facility_type], "Num{}".format(facility_type)
    prob.writeLP(model_file)
    return prob


def create_mclp_cc_model(coverage_dict, num_fac, model_file, delineator="$", use_serviceable_demand=False):
    """

        Creates an MCLPCC model using the provided coverage and parameters
        Writes a .lp file which can be solved with Gurobi

        Tong, Daoqin. 2012. Regional coverage maximization: a new model to account implicitly
        for complementary coverage. Geographical Analysis 44 (1):1-14.

        :param coverage_dict: (dictionary) The coverage to use to generate the model
        :param num_fac: (dictionary) The dictionary of number of facilities to use
        :param model_file: (string) The model file to output
        :param delineator: (string) The character/symbol used to delineate facility and id
        :param use_serviceable_demand: (bool) Should we use the serviceable demand rather than demand
        :return: (Pulp problem) The problem to solve
        """
    if use_serviceable_demand:
        demand_var = "serviceableDemand"
    else:
        demand_var = "demand"
    if not isinstance(coverage_dict, dict):
        raise TypeError("coverage_dict is not a dictionary")
    if not (isinstance(model_file, str)):
        raise TypeError("model_file is not a string")
    if not isinstance(num_fac, dict):
        raise TypeError("num_fac is not a dictionary")
    if not isinstance(delineator, str):
        raise TypeError("delineator is not a string")
    validate_coverage(coverage_dict, ["coverage"], ["partial"])
    # create the variables
    demand_vars = {}
    for demand_id in coverage_dict["demand"]:
        demand_vars[demand_id] = pulp.LpVariable("Y{}{}".format(delineator, demand_id), 0, None, pulp.LpContinuous)
    facility_vars = {}
    for facility_type in coverage_dict["facilities"]:
        facility_vars[facility_type] = {}
        for facility_id in coverage_dict["facilities"][facility_type]:
            facility_vars[facility_type][facility_id] = \
                pulp.LpVariable("{}{}{}".format(facility_type, delineator, facility_id), 0, 1, pulp.LpInteger)
    # create the problem
    prob = pulp.LpProblem("MCLP", pulp.LpMaximize)
    # add objective
    prob += pulp.lpSum([coverage_dict["demand"][demand_id][demand_var] * demand_vars[demand_id] for demand_id in
                        coverage_dict["demand"]])
    # add coverage constraints
    for demand_id in coverage_dict["demand"]:
        to_sum = []
        for facility_type in coverage_dict["demand"][demand_id]["coverage"]:
            for facility_id in coverage_dict["demand"][demand_id]["coverage"][facility_type]:
                to_sum.append(coverage_dict["demand"][demand_id]["coverage"][facility_type][facility_id] *
                              facility_vars[facility_type][facility_id])
        prob += pulp.lpSum(to_sum) - 1 * demand_vars[demand_id] >= 0, "D{}".format(demand_id)
        prob += demand_vars[demand_id] <= coverage_dict["demand"][demand_id][demand_var]
    # Number of total facilities
    to_sum = []
    for facility_type in coverage_dict["facilities"]:
        for facility_id in coverage_dict["facilities"][facility_type]:
            to_sum.append(facility_vars[facility_type][facility_id])
    prob += pulp.lpSum(to_sum) <= num_fac["total"], "NumTotalFacilities"
    # Number of other facility types
    for facility_type in coverage_dict["facilities"].keys():
        if facility_type in num_fac and facility_type != "total":
            to_sum = []
            for facility_id in coverage_dict["facilities"][facility_type]:
                to_sum.append(facility_vars[facility_type][facility_id])
            prob += pulp.lpSum(to_sum) <= num_fac[facility_type], "Num{}".format(facility_type)
    prob.writeLP(model_file)
    return prob


def create_threshold_model(coverage_dict, psi, model_file, delineator="$", use_serviceable_demand=False):
    """
    Creates a threshold model using the provided coverage and parameters
    Writes a .lp file which can be solved with Gurobi

    Murray, A. T., & Tong, D. (2009). GIS and spatial analysis in the
    media. Applied geography, 29(2), 250-259.

    :param coverage_dict: (dictionary) The coverage to use to generate the model
    :param psi: (float or int) The required threshold to cover (0-100%)
    :param model_file: (string) The model file to output
    :param delineator: (string) The character/symbol used to delineate facility and ids
    :param use_serviceable_demand: (bool) Should we use the serviceable demand rather than demand
    :return: (Pulp problem) The problem to solve
    """
    if use_serviceable_demand:
        demand_var = "serviceableDemand"
    else:
        demand_var = "demand"
    validate_coverage(coverage_dict, ["coverage"], ["binary"])
    # Check parameters
    if not isinstance(coverage_dict, dict):
        raise TypeError("coverage_dict is not a dictionary")
    if not (isinstance(psi, float) or isinstance(psi, int)):
        raise TypeError("backup weight is not float or int")
    if psi > 100.0 or psi < 0.0:
        raise ValueError("psi weight must be between 100 and 0")
    if not (isinstance(model_file, str)):
        raise TypeError("model_file is not a string")
    if not isinstance(delineator, str):
        raise TypeError("delineator is not a string")

    # create the variables
    demand_vars = {}
    for demand_id in coverage_dict["demand"]:
        demand_vars[demand_id] = pulp.LpVariable("Y{}{}".format(delineator, demand_id), 0, 1, pulp.LpInteger)
    facility_vars = {}
    for facility_type in coverage_dict["facilities"]:
        facility_vars[facility_type] = {}
        for facility_id in coverage_dict["facilities"][facility_type]:
            facility_vars[facility_type][facility_id] = pulp.LpVariable(
                "{}{}{}".format(facility_type, delineator, facility_id), 0, 1, pulp.LpInteger)
    # create the problem
    prob = pulp.LpProblem("ThresholdModel", pulp.LpMinimize)
    # Create objective, minimize number of facilities
    to_sum = []
    for facility_type in coverage_dict["facilities"]:
        for facility_id in coverage_dict["facilities"][facility_type]:
            to_sum.append(facility_vars[facility_type][facility_id])
    prob += pulp.lpSum(to_sum)
    # add coverage constraints
    for demand_id in coverage_dict["demand"]:
        to_sum = []
        for facility_type in coverage_dict["demand"][demand_id]["coverage"]:
            for facility_id in coverage_dict["demand"][demand_id]["coverage"][facility_type]:
                to_sum.append(facility_vars[facility_type][facility_id])
        prob += pulp.lpSum(to_sum) - 1 * demand_vars[demand_id] >= 0, "D{}".format(demand_id)
    # threshold constraint
    sum_demand = 0
    for demand_id in coverage_dict["demand"]:
        sum_demand += coverage_dict["demand"][demand_id][demand_var]
    to_sum = []
    for demand_id in coverage_dict["demand"]:
        # divide the demand by total demand to get percentage
        scaled_demand = float(100 / sum_demand) * coverage_dict["demand"][demand_id][demand_var]
        to_sum.append(scaled_demand * demand_vars[demand_id])
    prob += pulp.lpSum(to_sum) >= psi
    prob.writeLP(model_file)
    return prob


def create_cc_threshold_model(coverage_dict, psi, model_file, delineator="$", use_serviceable_demand=False):
    """

    Creates a complementary coverage threshold model using the provided coverage and parameters
    Writes a .lp file which can be solved with Gurobi

    Tong, D. (2012). Regional coverage maximization: a new model to account implicitly
    for complementary coverage. Geographical Analysis, 44(1), 1-14.

    :param coverage_dict: (dictionary) The coverage to use to generate the model
    :param psi: (float or int) The required threshold to cover (0-100%)
    :param model_file: (string) The model file to output
    :param delineator: (string) The character/symbol used to delineate facility and ids
    :param use_serviceable_demand: (bool) Should we use the serviceable demand rather than demand
    :return: (Pulp problem) The generated problem to solve
    """
    if use_serviceable_demand:
        demand_var = "serviceableDemand"
    else:
        demand_var = "demand"
    validate_coverage(coverage_dict, ["coverage"], ["partial"])
    # Check parameters
    if not isinstance(coverage_dict, dict):
        raise TypeError("coverage_dict is not a dictionary")
    if not (isinstance(psi, float) or isinstance(psi, int)):
        raise TypeError("backup weight is not float or int")
    if psi > 100.0 or psi < 0.0:
        raise ValueError("psi weight must be between 100 and 0")
    if not (isinstance(model_file, str)):
        raise TypeError("model_file is not a string")
    if not isinstance(delineator, str):
        raise TypeError("delineator is not a string")
    # create the variables
    demand_vars = {}
    for demand_id in coverage_dict["demand"]:
        demand_vars[demand_id] = pulp.LpVariable("Y{}{}".format(delineator, demand_id), 0, None, pulp.LpContinuous)
    facility_vars = {}
    for facility_type in coverage_dict["facilities"]:
        facility_vars[facility_type] = {}
        for facility_id in coverage_dict["facilities"][facility_type]:
            facility_vars[facility_type][facility_id] = pulp.LpVariable(
                "{}{}{}".format(facility_type, delineator, facility_id), 0, 1, pulp.LpInteger)
    # create the problem
    prob = pulp.LpProblem("ThresholdModel", pulp.LpMinimize)
    # Create objective, minimize number of facilities
    to_sum = []
    for facility_type in coverage_dict["facilities"]:
        for facility_id in coverage_dict["facilities"][facility_type]:
            to_sum.append(facility_vars[facility_type][facility_id])
    prob += pulp.lpSum(to_sum)
    # add coverage constraints
    for demand_id in coverage_dict["demand"]:
        to_sum = []
        for facility_type in coverage_dict["demand"][demand_id]["coverage"]:
            for facility_id in coverage_dict["demand"][demand_id]["coverage"][facility_type]:
                to_sum.append(coverage_dict["demand"][demand_id]["coverage"][facility_type][facility_id] *
                              facility_vars[facility_type][facility_id])
        prob += pulp.lpSum(to_sum) - 1 * demand_vars[demand_id] >= 0, "D{}".format(demand_id)
        prob += demand_vars[demand_id] <= coverage_dict["demand"][demand_id][demand_var]
    # add threshold constraint
    sum_demand = 0
    for demand_id in coverage_dict["demand"]:
        sum_demand += coverage_dict["demand"][demand_id][demand_var]
    to_sum = []
    for demand_id in coverage_dict["demand"]:
        # divide the demand by total demand to get percentage
        scaled_demand = float(100 / sum_demand)
        to_sum.append(scaled_demand * demand_vars[demand_id])
    prob += pulp.lpSum(to_sum) >= psi, "Threshold"
    prob.writeLP(model_file)
    return prob


def create_backup_model(coverage_dict, num_fac, model_file, delineator="$", use_serviceable_demand=False):
    """
    Creates a backup coverage model using the provided coverage and parameters
    Writes a .lp file which can be solved with Gurobi

    Church, R., & Murray, A. (2009). Coverage Business Site Selection, Location
    Analysis, and GIS (pp. 209-233). Hoboken, New Jersey: Wiley.

    Hogan, Kathleen, and Charles Revelle. 1986. Concepts and Applications of Backup Coverage.
    Management Science 32 (11):1434-1444.

    :param coverage_dict: (dictionary) The coverage to use to generate the model
    :param num_fac: (dictionary) The dictionary of number of facilities to use
    :param model_file: (string) The model file to output
    :param delineator: (string) The character/symbol used to delineate facility and ids
    :param use_serviceable_demand: (bool) Should we use the serviceable demand rather than demand
    :return: (Pulp problem) The generated problem to solve
    """
    if use_serviceable_demand:
        demand_var = "serviceableDemand"
    else:
        demand_var = "demand"
    validate_coverage(coverage_dict, ["coverage"], ["binary"])
    # Check parameters
    if not isinstance(coverage_dict, dict):
        raise TypeError("coverage_dict is not a dictionary")
    if not isinstance(num_fac, dict):
        raise TypeError("num_fac is not a dictionary")
    if not (isinstance(model_file, str)):
        raise TypeError("model_file is not a string")
    if not isinstance(delineator, str):
        raise TypeError("delineator is not a string")

    # create the variables
    demand_vars = {}
    for demand_id in coverage_dict["demand"]:
        demand_vars[demand_id] = pulp.LpVariable("U{}{}".format(delineator, demand_id), 0, 1, pulp.LpInteger)
    facility_vars = {}
    for facility_type in coverage_dict["facilities"]:
        facility_vars[facility_type] = {}
        for facility_id in coverage_dict["facilities"][facility_type]:
            facility_vars[facility_type][facility_id] = pulp.LpVariable(
                "{}{}{}".format(facility_type, delineator, facility_id), 0, None, pulp.LpInteger)
    # create the problem
    prob = pulp.LpProblem("BCLP", pulp.LpMaximize)
    # add objective
    prob += pulp.lpSum([coverage_dict["demand"][demand_id][demand_var] * demand_vars[demand_id] for demand_id in
                        coverage_dict["demand"]])
    # add coverage constraints
    for demand_id in coverage_dict["demand"]:
        to_sum = []
        for facility_type in coverage_dict["demand"][demand_id]["coverage"]:
            for facility_id in coverage_dict["demand"][demand_id]["coverage"][facility_type]:
                to_sum.append(facility_vars[facility_type][facility_id])
        prob += pulp.lpSum(to_sum) - 1 * demand_vars[demand_id] >= 1, "D{}".format(demand_id)
    # Number of total facilities
    to_sum = []
    for facility_type in coverage_dict["facilities"]:
        for facility_id in coverage_dict["facilities"][facility_type]:
            to_sum.append(facility_vars[facility_type][facility_id])
    prob += pulp.lpSum(to_sum) <= num_fac["total"], "NumTotalFacilities"
    # Number of other facility types
    for facility_type in coverage_dict["facilities"].keys():
        if facility_type in num_fac and facility_type != "total":
            to_sum = []
            for facility_id in coverage_dict["facilities"][facility_type]:
                to_sum.append(facility_vars[facility_type][facility_id])
            prob += pulp.lpSum(to_sum) <= num_fac[facility_type], "Num{}".format(facility_type)
    prob.writeLP(model_file)
    return prob


def create_lscp_model(coverage_dict, model_file, delineator="$", ):
    """
    Creates a LSCP (Location set covering problem) using the provided coverage and
    parameters. Writes a .lp file which can be solved with Gurobi

    Church, R., & Murray, A. (2009). Coverage Business Site Selection, Location
    Analysis, and GIS (pp. 209-233). Hoboken, New Jersey: Wiley.

    :param coverage_dict: (dictionary) The coverage to use to generate the model
    :param model_file: (string) The model file to output
    :param delineator: (string) The character(s) to use to delineate the layer from the ids
    :return: (Pulp problem) The generated problem to solve
    """
    validate_coverage(coverage_dict, ["coverage"], ["binary"])
    if not isinstance(coverage_dict, dict):
        raise TypeError("coverage_dict is not a dictionary")
    if not (isinstance(model_file, str)):
        raise TypeError("model_file is not a string")
    if not isinstance(delineator, str):
        raise TypeError("delineator is not a string")
        # create the variables
    demand_vars = {}
    for demand_id in coverage_dict["demand"]:
        demand_vars[demand_id] = pulp.LpVariable("Y{}{}".format(delineator, demand_id), 0, 1, pulp.LpInteger)
    facility_vars = {}
    for facility_type in coverage_dict["facilities"]:
        facility_vars[facility_type] = {}
        for facility_id in coverage_dict["facilities"][facility_type]:
            facility_vars[facility_type][facility_id] = pulp.LpVariable(
                "{}{}{}".format(facility_type, delineator, facility_id), 0, 1, pulp.LpInteger)
    # create the problem
    prob = pulp.LpProblem("LSCP", pulp.LpMinimize)
    # Create objective, minimize number of facilities
    to_sum = []
    for facility_type in coverage_dict["facilities"]:
        for facility_id in coverage_dict["facilities"][facility_type]:
            to_sum.append(facility_vars[facility_type][facility_id])
    prob += pulp.lpSum(to_sum)
    # add coverage constraints
    for demand_id in coverage_dict["demand"]:
        to_sum = []
        for facility_type in coverage_dict["demand"][demand_id]["coverage"]:
            for facility_id in coverage_dict["demand"][demand_id]["coverage"][facility_type]:
                to_sum.append(facility_vars[facility_type][facility_id])
        prob += pulp.lpSum(to_sum) >= 1, "D{}".format(demand_id)
    prob.writeLP(model_file)
    return prob
