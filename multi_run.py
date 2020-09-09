import os
import subprocess
import sys
from multiprocessing import Pool

if __name__ == '__main__':
    files = os.listdir(sys.argv[1])
    metadata = ''
    with open(os.path.join(sys.argv[1], 'base.yaml')) as f:
        for line in f.readlines():
            if 'metadata' in line:
                metadata = line.split('|')[1].strip()
                print(metadata)
                break
    with Pool(3) as p:
        parallel_tests = []
        for f in files:
            if f == 'base.yaml':
                continue
            fp = os.path.join(sys.argv[1], f)
            args = ['./pkb.py',
                    '--benchmark_config_file={}'.format(fp),
                    '--metadata={}'.format(metadata)]
            if len(sys.argv) > 2:
                for s in sys.argv[2:]:
                    args.append(s)
            parallel_tests.append(args)
        p.map(subprocess.call, parallel_tests)
