import os
import subprocess
import sys
import tempfile
from datetime import datetime
from multiprocessing import Pool

BASE = """
benchmarks:
  - cloud_spanner_ycsb:
      flags:
        ycsb_skip_load_stage: True

        # Spanner
        cloud_spanner_config: regional-us-west1
        gce_network_name: default

        # VMs
        machine_type: n1-standard-1
        ycsb_threads_per_client: "25"

        # Data size: 1 column per row, row size 1KB, 100GB total size
        ycsb_field_count: 1
        ycsb_field_length: 1000

        # Run for 30 minutes
        ycsb_timelimit: 1800 # 30 minutes
        ycsb_operation_count: 100000000 # Very high

        # Lock environment to a particular version
        ycsb_version: 0.17.0
        ycsb_measurement_type: hdrhistogram

        # TODO: Add custom tar url
        # ycsb_tar_url: https://storage.googleapis.com/externally_shared_files/ycsb-0.18.0-SNAPSHOT.tar.gz

"""


INSTANCES = {
    '3': {
        'cloud_spanner_instance_name': 'pkb-three-node-benchmarks-west1',
        'cloud_spanner_nodes': '3',
        'ycsb_record_count': '100000000',
        'ycsb_client_vms': '30',
        'zones': 'us-west1-a,us-west1-b,us-west1-c'
    },
    '6': {
        'cloud_spanner_instance_name': 'pkb-six-node-benchmarks-west1',
        'cloud_spanner_nodes': '6',
        'ycsb_record_count': '200000000',
        'ycsb_client_vms': '60',
        'zones': 'us-west1-a,us-west1-b,us-west1-c'
    },
    '9': {
        'cloud_spanner_instance_name': 'pkb-nine-node-benchmarks-west1',
        'cloud_spanner_nodes': '9',
        'ycsb_record_count': '300000000',
        'ycsb_client_vms': '90',
        'zones': 'us-west1-a,us-west1-b,us-west1-c'
    }
}

TARGET_QPS_PER_VM = {
    'throughput': {
        'a': 330,  # R/W 50/50: 3.3k QPS/Node
        'b': 830,  # R/W  95/5: 8.3k QPS/Node
        'c': 1000, # Read-Only: 10k QPS/Node
        'x': 200   # Write-Only: 2k QPS/Node
    },
    'latency': {
        # Latency uses 2/3rd target of throughput
        'a': int(330 * 0.66),
        'b': int(830 * 0.66),
        'c': int(1000 * 0.66),
        'x': int(200 * 0.66)
    }
}

def build_yaml(tmp_yaml, test, workload, node_count):
    indent = '        '
    with open(tmp_yaml, 'w') as tmpfile:
        # Write BASE
        for l in BASE.split('\n'):
            tmpfile.writelines([l, '\n'])

        # tmpfile.writelines([l for l in BASE.split('\n')])
        # tmpfile.writelines(['\n'])

        # Write the instance values
        for k in INSTANCES[node_count].keys():
            tmpfile.writelines([ indent + "{}: {}\n".format(k, INSTANCES[node_count][k]) ])

        # Write the workload values
        # Python is fun. This ends up looking like: workloada,workloada,workload,...
        w = ','.join(['workload' + workload] * 11)
        tmpfile.writelines([indent + "ycsb_workload_files: " + w + "\n"])

        # Write the QPS Targets
        t = TARGET_QPS_PER_VM[test][workload]
        tmpfile.writelines(
            [indent + "ycsb_run_parameters: target={},requestdistribution=zipfian,dataintegrity=true".format(t) + "\n"]
        )


def main():
    for test in ['throughput', 'latency']:
        for workload in ['c', 'a', 'b', 'x']:
            parallel_runs = []
            for node_count in INSTANCES:

                tmp_yaml = '/tmp/suite_{}_{}_{}.yaml'.format(test, workload, node_count)

                build_yaml(tmp_yaml, test, workload, node_count)
                run_date = datetime.now().strftime("%Y%m%d")
                parallel_runs.append([
                    './pkb.py',
                    '--benchmark_config_file={}'.format(tmp_yaml),
                    '--metadata=pkb_test:{},workload:{},node_count:{},run_date:{}'.format(test, workload, node_count, run_date),
                    '--bigquery_table=spanner_pkb_results.tmp_staging'
                ])

            with Pool(3) as p:
                if not '--dry_run' in ''.join(sys.argv):
                    p.map(subprocess.call, parallel_runs)

if __name__ == '__main__':
    main()
