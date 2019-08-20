# -*- coding: UTF-8 -*-
from pyspatialopt.models import binary_mclp_distance_matrix
import unittest


class MyTest(unittest.TestCase):
    def test_simple_case(self):
        workspace_path = r"../sample_data"
        file_distance_matrix = "simple_case_distance_matrix.csv"
        service_dist = 10
        dict_num_facility_percent_coverage = {1: 5.0/15*100, 2: 9.0/15*100, 3: 12.0/15*100, 4: 14.0/15*100, 5: 15.0/15*100}
        for num_facility, percent_coverage in dict_num_facility_percent_coverage.items():
            res_coverag = binary_mclp_distance_matrix.binary_mclp_distance_matrix(file_distance_matrix, service_dist, num_facility, workspace_path=workspace_path)
            print("A coverage of {0} is obtained with {1} facilities".format(res_coverag["percent_demand_coverage"], num_facility))
            self.assertAlmostEquals(res_coverag["percent_demand_coverage"], percent_coverage)

    def test_simple_case(self):
        workspace_path = r"../sample_data"
        file_distance_matrix = "service_area_demand_point_distance_matrix.csv"
        service_dist = 5000
        # dict_num_facility_percent_coverage = {1:5.0/15*100, 2:9.0/15*100, 3:12.0/15*100, 4:14.0/15*100, 5:15.0/15*100}
        dict_num_facility_percent_coverage = {5: 52.797393302}
        for num_facility, percent_coverage in dict_num_facility_percent_coverage.items():
            res_coverag = binary_mclp_distance_matrix.binary_mclp_distance_matrix(file_distance_matrix, service_dist, num_facility, workspace_path=workspace_path)
            print("A coverage of {0} is obtained with {1} facilities".format(res_coverag["percent_demand_coverage"], num_facility))
            self.assertAlmostEquals(res_coverag["percent_demand_coverage"], percent_coverage, places=5)


if __name__ == "__main__":
    # test case 1: simple case
    # test case 2: using the case provided. A coverage of 52.797393302% is obtained using 5 facilities
    unittest.main()
