import os
import os.path as osp
import sys
sys.path.append('./fastsk')
import argparse
import json
import numpy as np
from fastsk import Kernel
from utils import FastaUtility, GkmRunner, GaKCoRunner, FastskRunner, time_fastsk, time_gkm, time_gakco
import pandas as pd
import time
from scipy import special
import multiprocessing
import subprocess

# Subprocess timeout (s)
TIMEOUT = 3600
MAXTIME = 1800
GKM_DATA = '/localtmp/dcb7xz/FastSK/baselines/gkm_data'
GKM_EXEC = '/localtmp/dcb7xz/FastSK/baselines/gkmsvm'
FASTSK_DATA = '/localtmp/dcb7xz/FastSK/data/'

def time_blended(t):
    pass

def thread_experiment(dataset, g, m, k):
    output_csv = dataset + '_vary_threads_I50.csv'
    results = {
        'fastsk_exact_time' : [],
        'fastsk_approx_time' : [],
        'fastsk_approx_time_t1' : [],
        'fastsk_I50': [],
        'gkm_time' : [],
    }

    train_file = osp.join('./data', dataset + '.train.fasta')
    reader = FastaUtility()
    Xtrain, Ytrain = reader.read_data(train_file)

    for t in range(1, 21):
        # fastsk_exact = time_fastsk(g, m, t, FASTSK_DATA, prefix=dataset, approx=False)
        # fastsk_approx = time_fastsk(g, m, t, FASTSK_DATA, prefix=dataset, approx=True)
        # fastsk_approx_t1 = time_fastsk(g, m, t=1, FASTSK_DATA, prefix=dataset, approx=True)
        # fastsk_approx_t1 = time_fastsk(g, m, t=1, FASTSK_DATA, prefix=dataset, approx=True)
        # gkm = time_gkm(g, m, t, GKM_DATA, GKM_EXEC, prefix=dataset)
        fastsk_exact = 0
        fastsk_approx = 0
        fastsk_approx_t1 = 0
        fastsk_approx_t1 = 0
        gkm = 0
        fastsk_I50 = time_fastsk(g, m, t=1, 
            data_location=FASTSK_DATA, 
            prefix=dataset, 
            approx=True, 
            max_iters=50)

        results['fastsk_exact_time'].append(fastsk_exact)
        results['fastsk_approx_time'].append(fastsk_approx)
        results['fastsk_approx_time_t1'].append(fastsk_approx_t1)
        results['fastsk_I50'].append(fastsk_I50)
        results['gkm_time'].append(gkm)

        # log_str = "{} - exact: {}, approx: {} approx_t1: {}, gkm: {}"
        # print(log_str.format(dataset, fastsk_exact, fastsk_approx, fastsk_approx_t1, gkm))
        log_str = "{} - I50: {}"
        print(log_str.format(dataset, fastsk_I50))

        df = pd.DataFrame(results)
        df.to_csv(output_csv, index=False)

def run_thread_experiments(params):
    for p in params:
        dataset, type_, g, m, k = p['Dataset'], p['type'], p['g'], p['m'], p['k']
        assert k == g - m
        if type_ == 'dna':
            thread_experiment(dataset, g, m, k)

def g_time_experiment(dataset):
    '''Nov 14 experiments:
        - FastSK-Approx 1 thread
        - FastSK-Approx 10 thread
        - FastSK-Approx 20 thread
        - FastSK-Approx 1 thread
        - FastSK-Approx 10 thread
        - FastSK-Approx 20 thread
    '''
    output_csv = dataset + '_g_times_nov14.csv'
    results = {
        'g': [],
        'k': [],
        'm': [],
        'FastSK-Approx 1 thread': [],
        'FastSK-Approx 10 thread': [],
        'FastSK-Approx 20 thread': [],
        'FastSK-Approx 1 thread no variance 50 iters': [],
        'FastSK-Approx 10 thread no variance 50 iters': [],
        'FastSK-Approx 20 thread no variance 50 iters': [],
        'gkm-Approx 1 thread': [],
        'gkm-Approx 10 thread': [],
        'gkm-Approx 20 thread': []
    }

    train_file = osp.join('./data', dataset + '.train.fasta')
    reader = FastaUtility()
    Xtrain, Ytrain = reader.read_data(train_file)
    
    min_g, max_g = 6, 20
    k = 6
    
    skip_fastsk_exact, skip_gkm_exact = True, True
    skip_fastsk_approx_t1, skip_fastsk_approx_t10, skip_fastsk_approx_t20 = False, False, False
    skip_fastsk_approx_t1_no_var, skip_fastsk_approx_t10_no_var, skip_fastsk_approx_t20_no_var = False, False, False
    skip_gkm_approx_t1, skip_gkm_approx_t10, skip_gkm_approx_t20 = False, False, False

    for g in range(min_g, max_g + 1):
        m = g - k
        max_I = int(special.comb(g, m))

        fastsk_approx_t1, fastsk_approx_t10, fastsk_approx_t20 = [0] * 3
        gkm_approx_t1, gkm_approx_t10, gkm_approx_t20 = [0] * 3

        ## FastSK-Exact 
        if not skip_fastsk_exact:
            fastsk_exact = time_fastsk(g, m, t=20, data_location=FASTSK_DATA,prefix=dataset,approx=False,timeout=TIMEOUT)
            if (fastsk_exact >= MAXTIME and g > 8):
                skip_fastsk_exact = True
        
        ## FastSK-Approx, iterate until convergence is reached
        if not skip_fastsk_approx_t1:
            fastsk_approx_t1 = time_fastsk(g, m, t=1, data_location=FASTSK_DATA, prefix=dataset,
                approx=True, max_iters=max_I, timeout=TIMEOUT)
            if (fastsk_approx_t1 >= MAXTIME and g > 8):
                skip_fastsk_approx_t1 = True

        if not skip_fastsk_approx_t10:
            fastsk_approx_t10 = time_fastsk(g, m, t=10, data_location=FASTSK_DATA, prefix=dataset,
                approx=True, max_iters=max_I, timeout=TIMEOUT)
            if (fastsk_approx_t10 >= MAXTIME and g > 8):
                skip_fastsk_approx_t10 = True

        if not skip_fastsk_approx_t20:
            fastsk_approx_t20 = time_fastsk(g, m, t=20, data_location=FASTSK_DATA, prefix=dataset,
                approx=True, max_iters=max_I, timeout=TIMEOUT)
            if (fastsk_approx_t20 >= MAXTIME and g > 8):
                skip_fastsk_approx_t20 = True

        ## FastSK-Approx, don't make convergence calculations; iterate 100 times
        if not skip_fastsk_approx_t1_no_var:
            fastsk_approx_t1_no_var = time_fastsk(g, m, t=1, data_location=FASTSK_DATA, prefix=dataset,
                approx=True, max_iters=50, skip_variance=True, timeout=TIMEOUT)
            if (fastsk_approx_t1_no_var >= MAXTIME and g > 8):
                skip_fastsk_approx_t1_no_var = True

        if not skip_fastsk_approx_t10_no_var:
            fastsk_approx_t10_no_var = time_fastsk(g, m, t=10, data_location=FASTSK_DATA, prefix=dataset, 
                approx=True, max_iters=50, skip_variance=True, timeout=TIMEOUT)
            if (fastsk_approx_t10_no_var >= MAXTIME and g > 8):
                skip_fastsk_approx_t10_no_var = True

        if not skip_fastsk_approx_t20_no_var:
            fastsk_approx_t20_no_var = time_fastsk(g, m, t=20, data_location=FASTSK_DATA, prefix=dataset, 
                approx=True, max_iters=50, skip_variance=True, timeout=TIMEOUT)
            if (fastsk_approx_t20_no_var >= MAXTIME and g > 8):
                skip_fastsk_approx_t20_no_var = True

        ## gkm-Exact
        if not skip_gkm_exact:
            gkm_exact = time_gkm(g, m, t=20, gkm_data=GKM_DATA, gkm_exec=GKM_EXEC, 
                prefix=dataset, approx=False, timeout=TIMEOUT)
            if (gkm_exact >= MAXTIME and g > 8):
                skip_gkm_exact = True
        
        ## gkm-Approx, max_d = 3
        if not skip_gkm_approx_t1:
            gkm_approx_t1 = time_gkm(g, m, t=1, gkm_data=GKM_DATA, gkm_exec=GKM_EXEC, 
                prefix=dataset, approx=True, timeout=TIMEOUT)
            if (gkm_approx_t1 >= MAXTIME and g > 8):
                skip_gkm_approx_t1 = True

        if not skip_gkm_approx_t10:
            gkm_approx_t10 = time_gkm(g, m, t=10, gkm_data=GKM_DATA, gkm_exec=GKM_EXEC, 
                prefix=dataset, approx=True, timeout=TIMEOUT)
            if (gkm_approx_t10 >= MAXTIME and g > 8):
                skip_gkm_approx_t10 = True

        if not skip_gkm_approx_t20:
            gkm_approx_t20 = time_gkm(g, m, t=20, gkm_data=GKM_DATA, gkm_exec=GKM_EXEC, 
                prefix=dataset, approx=True, timeout=TIMEOUT)
            if (gkm_approx_t20 >= MAXTIME and g > 8):
                skip_gkm_approx_t20 = True

        ## Save results
        results['g'].append(g)
        results['k'].append(k)
        results['m'].append(m)
        results['FastSK-Approx 1 thread'].append(fastsk_approx_t1)
        results['FastSK-Approx 10 thread'].append(fastsk_approx_t10)
        results['FastSK-Approx 20 thread'].append(fastsk_approx_t20)
        results['FastSK-Approx 1 thread no variance 50 iters'].append(fastsk_approx_t1_no_var)
        results['FastSK-Approx 10 thread no variance 50 iters'].append(fastsk_approx_t10_no_var)
        results['FastSK-Approx 20 thread no variance 50 iters'].append(fastsk_approx_t20_no_var)
        results['gkm-Approx 1 thread'].append(gkm_approx_t1)
        results['gkm-Approx 10 thread'].append(gkm_approx_t10)
        results['gkm-Approx 20 thread'].append(gkm_approx_t20)

        print("{} - g = {}, m = {}".format(dataset, g, m))

        df = pd.DataFrame(results)
        df.to_csv(output_csv, index=False)

def run_g_time_experiments(params):
    for p in params:
        dataset, type_ = p['Dataset'], p['type']
        if type_ == 'dna':
            g_time_experiment(dataset)

def I_experiment(dataset, g, m, k, C):
    output_csv = dataset + '_vary_I.csv'
    results = {
        'I': [],
        'acc' : [],
        'auc' : [],
    }

    if m == 0:
        m = 1

    max_I = min(int(special.comb(g, m)), 100)
    iter_vals = []
    if (max_I > 10):
        iter_vals += list(range(1, 10))
        iter_vals += list(range(10, max_I, 10))
        iter_vals.append(max_I)
    else:
        iter_vals = list(range(1, max_I + 1))

    for I in iter_vals:
        fastsk = FastskRunner(dataset)
        acc, auc = fastsk.train_and_test(g, m, t=1, approx=True, I=I, delta=0.025, C=C)
        log_str = "{}: I = {}, auc = {}, acc = {}".format(dataset, I, auc, acc)
        print(log_str)
        results['I'].append(I)
        results['acc'].append(acc)
        results['auc'].append(auc)

        df = pd.DataFrame(results)
        df.to_csv(output_csv, index=False)

def run_I_experiments(params):
    for p in params:
        dataset, type_, g, m, k, C = p['Dataset'], p['type'], p['g'], p['m'], p['k'], p['C']
        # if dataset in ['ZZZ3', 'KAT2B', 'EP300_47848']:
        #     continue
        assert k == g - m
        I_experiment(dataset, g, m, k, C)

def delta_experiment(dataset, g, m, k, C):
    output_csv = dataset + '_vary_delta.csv'
    results = {
        'delta': [],
        'acc' : [],
        'auc' : [],
    }

    max_I = int(special.comb(g, m))
    delta_vals = [0.005 * i for i in range(20)] + [0.1 * i for i in range(1, 11)]
    for d in delta_vals:
        fastsk = FastskRunner(dataset)
        acc, auc = fastsk.train_and_test(g, m, t=1, approx=True, I=max_I, delta=d, C=C)
        log_str = "{}: d = {}, acc = {}, auc = {}".format(dataset, d, acc, auc)
        print(log_str)
        results['delta'].append(d)
        results['acc'].append(acc)
        results['auc'].append(auc)

    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)

def run_delta_experiments(params):
    for p in params:
        dataset, type_, g, m, k, C = p['Dataset'], p['type'], p['g'], p['m'], p['k'], p['C']
        assert k == g - m
        if dataset in ['ZZZ3', 'KAT2B', 'EP300_47848']:
            continue
        delta_experiment(dataset, g, m, k, C)

def check_C_vals(g, m, dataset):
    best_auc, best_acc, best_C = 0, 0, 0
    C_vals = [10**i for i in range(-3, 3)]
    max_I = max_I = min(int(special.comb(g, m)), 100)
    for C in C_vals:
        fastsk = FastskRunner(dataset)
        acc, auc = fastsk.train_and_test(g, m, t=1, I=max_I, approx=True, C=C)
        if auc > best_auc:
            best_acc, best_auc = acc, auc
    return best_acc, best_auc, C

def g_auc_experiment(dataset, C):
    output_csv = dataset + '_g_auc_k6.csv'
    results = {
        'g': [],
        'k': [],
        'm': [],
        'C' : [],
        'fastsk_approx_acc' : [],
        'fastsk_approx_auc' : [],
        'gkm_approx_acc' : [],
        'gkm_approx_auc' : [],
    }

    train_file = osp.join('/localtmp/dcb7xz/FastSK/data', dataset + '.train.fasta')
    test_file = osp.join('/localtmp/dcb7xz/FastSK/data', dataset + '.test.fasta')

    fasta_util = FastaUtility()
    max_g = min(fasta_util.shortest_seq(train_file), fasta_util.shortest_seq(test_file), 20)
    k = 6

    for g in range(k, max_g + 1):
        m = g - k
        #max_I = min(int(special.comb(g, m)), 500)
        #fastsk = FastskRunner(dataset)
        #acc, auc = fastsk.train_and_test(g, m, t=1, I=max_I, approx=True, C=C)
        acc, auc, C = check_C_vals(g, m, dataset)
        log_str = "Acc {}, AUC {}, g {}, m {}".format(acc, auc, g, m)
        print(log_str)
        results['g'].append(g)
        results['k'].append(k)
        results['m'].append(m)
        results['C'].append(C)
        results['acc'].append(acc)
        results['auc'].append(auc)

        df = pd.DataFrame(results)
        df.to_csv(output_csv, index=False)


def run_g_auc_experiments(params):
    for p in params:
        dataset, type_, g, m, k, C = p['Dataset'], p['type'], p['g'], p['m'], p['k'], p['C']
        assert k == g - m
        if not dataset in ['KAT2B', 'TP53', 'ZZZ3'] and type_ == 'dna':
            g_auc_experiment(dataset, C)

def fastsk_gkm_dna_kernel_times(params):
    output_csv = 'fastsk_gkm_dna_kernel_times_part2.csv'
    results = {
        'dataset': [],
        'g': [],
        'm': [],
        'k': [],        
        'fastsk_exact': [],
        'fastsk_approx_t1': [],
        'fastsk_I50': [],
        'gkm_exact': [],
        'gkm_approx': [],
    }
    count = 0
    for p in params:
        dataset, type_, g, m, k = p['Dataset'], p['type'], p['g'], p['m'], p['k']
        if type_ != 'dna':
            continue

        if dataset not in ['KAT2B', 'TP53', 'ZZZ3']:
            continue

        max_I = int(special.comb(g, m))

        fastsk_exact = time_fastsk(g, m, t=20,
            data_location=FASTSK_DATA,
            prefix=dataset, 
            approx=False)
        
        fastsk_approx_t1 = time_fastsk(g, m, t=1, 
            data_location=FASTSK_DATA,
            prefix=dataset, 
            approx=True, 
            max_iters=max_I)

        fastsk_I50 = time_fastsk(g, m, t=1, 
            data_location=FASTSK_DATA, 
            prefix=dataset, 
            approx=True, 
            max_iters=50)

        gkm_exact = time_gkm(g, m, t=20,
            gkm_data=GKM_DATA,
            gkm_exec=GKM_EXEC, 
            prefix=dataset, 
            approx=False)
        
        gkm_approx = time_gkm(g, m, t=1,
            gkm_data=GKM_DATA,
            gkm_exec=GKM_EXEC, 
            prefix=dataset, 
            approx=True)

        results['dataset'].append(dataset)
        results['g'].append(g)
        results['m'].append(m)
        results['k'].append(k)
        results['fastsk_exact'].append(fastsk_exact)
        results['fastsk_approx_t1'].append(fastsk_approx_t1)
        results['fastsk_I50'].append(fastsk_I50)
        results['gkm_exact'].append(gkm_exact)
        results['gkm_approx'].append(gkm_approx)

        for key in results:
            print('{} - {}'.format(key, results[key][count]))
        
        df = pd.DataFrame(results)
        df.to_csv(output_csv, index=False)

        count += 1

df = pd.read_csv('./evaluations/datasets_to_use.csv')
params = df.to_dict('records')

#fastsk_gkm_dna_kernel_times(params)

### Thread experiments
#run_thread_experiments(params)

### g kernel timing experiments
run_g_time_experiments(params)

### g kernel AUC experiments
#run_g_auc_experiments(params)
#g_auc_experiment('TP53', 0.1)

'''
KAT2B,dna,13,7,6,1
TP53,dna,7,2,5,0.1
ZZZ3,dna,10,4,6,0.1
'''

#run_increase_g_experiments(params)

## m experiments
pass

## AUC vs I experiments
#I_experiment('1.1', 8, 4, 4, 0.01)
#run_I_experiments(params)

## AUC vs g experiments
pass

### AUC vs delta experiments
#delta_experiment('1.1', g=8, m=4, k=4, C=0.01)
#run_delta_experiments(params)
