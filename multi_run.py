import os
import subprocess
import sys
from multiprocessing import Pool


def find_metdata(file_path):
    metadata = ''
    with open(file_path) as f:
        for line in f.readlines():
            if 'metadata' in line:
                metadata += line.split('|')[1].strip()
    return metadata


if __name__ == '__main__':
    folder = sys.argv[1]
    files = [f for f in os.listdir(folder)]

    # Extract metadata from base
    base_metadata = ''
    if 'base.yaml' in files:
        print('Found base file. Extracting base_metadata')
        base_metadata = find_metdata(os.path.join(folder, 'base.yaml'))
        files.remove('base.yaml')

    with Pool(3) as p:
        parallel_tests = []

        for f in files:
            fp = os.path.join(folder, f)

            metadata = ','.join([base_metadata, find_metdata(fp), 'yaml:{}'.format(f)])

            base_args = ['./pkb.py',
                         '--benchmark_config_file={}'.format(fp),
                         '--metadata={}'.format(metadata)]
            args = base_args + sys.argv[2:]

            parallel_tests.append(args)

        p.map(subprocess.call, parallel_tests)
