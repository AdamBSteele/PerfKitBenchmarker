import os
import subprocess
import sys
from multiprocessing import Pool


def find_metdata(fp):
    metadata = ''
    with open(fp) as f:
        for line in f.readlines():
            if 'metadata' in line:
                metadata += line.split('|')[1].strip()
    return metadata


def run_directory():
    """
    Runs each .yaml in the dir in parallel
    """
    folder = sys.argv[1]
    files = [f for f in os.listdir(folder)]

    # Extract metadata from base
    base_metadata = ''
    if 'base.yaml' in files:
        print('Found base file. Extracting base_metadata')
        base_metadata = find_metdata(os.path.join(folder, 'base.yaml')) = "|"
        files.remove('base.yaml')

    with Pool(3) as p:
        parallel_tests = []

        for f in files:
            fp = os.path.join(folder, f)
            metadata = ','.join([base_metadata, find_metdata(fp), 'yaml:{}'.format(f)])
            args = build_args_list(fp, metadata)
            parallel_tests.append(args)

        p.map(subprocess.call, parallel_tests)


def run_file():
    fp = sys.argv[1]
    folder = os.path.split(fp)[0]

    metadata = ''
    base_path = os.path.join(folder, 'base.yaml')
    if os.path.isfile(base_path):
        metadata += find_metdata(base_path)
    metadata += find_metdata(fp)
    args = build_args_list(fp, metadata)
    subprocess.call(args)


def build_args_list(fp, metadata):
    base_args = ['./pkb.py',
                 '--benchmark_config_file={}'.format(fp),
                 '--metadata={}'.format(metadata)]
    args = base_args + sys.argv[2:]

    if '--bigquery_table' not in ''.join(args):
        args.append('--bigquery_table=pkb_results.multi_runs')

    if '--run_uri' not in ''.join(args):
        run_uri = fp[:-5].replace('.', '').replace('_', '')[-12:]
        args.append('--run_uri={}'.format(run_uri))
    print(args)
    return args


if __name__ == '__main__':
    arg = sys.argv[1]

    if '--full_suite' in sys.argv:
        assert os.path.isfile(sys.argv[1])
        base_file = sys.argv[1]
        instances = ["pkb-three-node-benchmarks",
                     "pkb-three-node-benchmarks-two",
                     "pkb-three-node-benchmarks-three",
                     "pkb-three-node-benchmarks-four"]

    if os.path.isfile(sys.argv[1]):
        run_file()
    elif os.path.isdir(sys.argv[1]):
        run_directory()
    else:
        print("File not found")
