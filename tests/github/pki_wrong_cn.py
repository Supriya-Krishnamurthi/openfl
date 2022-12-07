# Copyright (C) 2020-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import shutil
import subprocess
import os
import time
import socket
from subprocess import Popen
import sys

from openfl.native import setup_plan


def prepare_workspace():
    subprocess.check_call(['fx', 'workspace', 'certify'])
    subprocess.check_call(['fx', 'plan', 'initialize'])

    subprocess.check_call([
        'fx', 'aggregator', 'generate-cert-request'
    ])
    subprocess.check_call([
        'fx', 'aggregator', 'certify',
        '-s'
    ])
    for col in ['one', 'two']:
        subprocess.check_call([
            'fx', 'collaborator', 'generate-cert-request',
            '-n', col,
            '-d', '1',
            '-s', '-x'
        ])
        subprocess.check_call([
            'fx', 'collaborator', 'certify',
            '-n', col,
            '-s'
        ])
    
    sys.path.append(os.getcwd())
    
def start_invalid_collaborator():
    '''
    We choose the gRPC client of another collaborator
    to check if aggregator would accept certificate
    that does not correspond to the collaborator's name.
    '''
    col_name = 'one'
    plan = setup_plan()
    plan.resolve()
    client = plan.get_client(
        'two', 
        plan.aggregator_uuid,
        plan.federation_uuid
        )
    collaborator = plan.get_collaborator(col_name, client=client)
    collaborator.run()


if __name__ == '__main__':
    origin_dir = os.getcwd()
    prefix = 'fed_workspace'
    subprocess.check_call([
        'fx', 'workspace', 'create',
        '--prefix', prefix,
        '--template', 'keras_cnn_mnist'
    ])
    os.chdir(prefix)
    fqdn = socket.getfqdn()
    try:
        prepare_workspace()
        agg = Popen(target=subprocess.check_call, args=[['fx','aggregator', 'start']])
        agg.start()
        time.sleep(3)
        print('Starting Collaborator...')
        start_invalid_collaborator()
        agg.join()
        assert False, 'Aggregator accepted invalid collaborator certificate.'
    finally:
        agg.kill()
        os.chdir(origin_dir)
        shutil.rmtree(prefix)