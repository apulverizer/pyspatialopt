# -*- coding: UTF-8 -*-


def get_ids(problem, variable_name, threshold=1.0, delineator="$"):
    """
    helper to get the variables
    :param problem: (pulp problem) The solved problem to extract results from
    :param variable_name: (string) The variable name to extract
    :param threshold: (float) The minimum value to use when choosing ids
    :param delineator: (string) The string used to split demand and facilities from ids
    :return: (array) A array of the ids (as strings) that meet or exceed the threshold
    """
    ids = []
    for var in problem.variables():
        if var.name.split(delineator)[0] == variable_name:
            if var.varValue >= threshold:
                ids.append(var.name.split("$")[1])
    return ids
