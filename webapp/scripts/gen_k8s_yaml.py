import argparse
import os
import datetime

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('model', help='choose a model')
    parser.add_argument('flow', help='choose a flow', choices=['train', 'eval', 'serve'])
    parser.add_argument('--ps_num', help='choose ps number', type=int)
    parser.add_argument('--worker_num', help='choose worker number', type=int)
    parser.add_argument('--epoch', help='choose worker number', type=float)
    parser.add_argument('--record_dir', help='record files path')
    parser.add_argument('--signature', help='signature label')
    args = parser.parse_args()
    return args

def generate_train_configmap(model, signature, req_nodes, port, epoch):
    ps_hosts, worker_hosts = [], []
    for i in range(req_nodes['ps']):
        ps_host = '{}-{}-ps-{}.default.svc.cluster.local:{}'.format(model, signature, i, port)
        ps_hosts.append(ps_host)
    ps_hosts_str = ','.join(ps_hosts)
    for i in range(req_nodes['worker']):
        worker_host = '{}-{}-worker-{}.default.svc.cluster.local:{}'.format(model, signature, i, port)
        worker_hosts.append(worker_host)
    worker_hosts_str = ','.join(worker_hosts)

    k8s_configmap = """---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {0}-{1}-configmap
data:
  PS_HOSTS: "{2}"
  WORKER_HOSTS: "{3}"
  NUM_EPOCH: "{4}"
  MODEL_NAME: "{0}"
  SIGNATURE: "{1}"
""".format(model, signature, ps_hosts_str, worker_hosts_str, epoch)
    return k8s_configmap

def generate_train_service(job, id, port, model, signature):
    k8s_service = """---
apiVersion: v1
kind: Service
metadata:
  name: {3}-{4}-{0}-{1}
spec:
  type: ClusterIP
  ports:
  - port: {2}
    targetPort: {2}
    protocol: TCP
  selector:
    job: {0}
    task: t{1}
    model: {3}
    signature: s{4}
""".format(job, id, port, model, signature)
    return k8s_service

def generate_train_job(job, id, port, model, signature, record_dir):
    k8s_job = """---
apiVersion: v1
kind: Pod
metadata:
  name: {3}-{4}-{0}-{1}
  labels:
    job: {0}
    task: t{1}
    model: {3}
    signature: s{4}
spec:
  restartPolicy: Never
  volumes:
  - name: tf-volume
    persistentVolumeClaim:
      claimName: tf-pvc
  containers:
  - name: tf-training
    image: exaai/tf-gpu
    securityContext:
      privileged: true
    command: ["/bin/bash"]
    args: ["{5}/{0}.sh"]
    ports:
    - name: tf-training-ports
      containerPort: {2}
      protocol: TCP
      name: http
    volumeMounts:
    - mountPath: /nfs
      name: tf-volume
    envFrom:
    - configMapRef:
        name: {3}-{4}-configmap
    env:
    - name: JOB_NAME
      value: {0}
    - name: TASK_ID
      value: "{1}"
    - name: TRAIN_DIR
      value: "/nfs/nvme/train/{3}-{4}"
""".format(job, id, port, model, signature, record_dir)

    if job == 'worker':
        k8s_job += """
    resources:
      requests:
        cpu: 3000m
        memory: 16Gi
        nvidia.com/gpu: 1
      limits:
        cpu: 6000m
        memory: 32Gi       
        nvidia.com/gpu: 1
"""
    else:
        k8s_job += """
    - name: CUDA_VISIBLE_DEVICES
      value: " "
    resources:
      requests:
        cpu: 2000m
        memory: 16Gi
      limits:
        cpu: 4000m
        memory: 32Gi       
"""
    return k8s_job

def generate_train_config(model, signature, ps_num, worker_num, epoch, record_dir):
    req_nodes = {}
    req_nodes['ps'] = ps_num if ps_num else 2
    req_nodes['worker'] = worker_num if worker_num else 4
    port = 2220

    k8s_config = ''
    k8s_config += generate_train_configmap(model, signature, req_nodes, port, epoch)
    for job in ['ps', 'worker']:
        for i in range(req_nodes[job]):
            k8s_config += generate_train_service(job, i, port, model, signature)
            k8s_config += generate_train_job(job, i, port, model, signature, record_dir)

    return k8s_config

def main():
    args = parse_args()
    k8s_config = ''
    signature = args.signature if args.signature else datetime.datetime.now().strftime("%y%m%d%H%M%S")
    epoch = args.epoch if args.epoch else 1.0
    if args.flow == 'train':
        k8s_config = generate_train_config(args.model, signature, args.ps_num, args.worker_num, epoch, args.record_dir)
    elif args.flow == 'eval':
        k8s_config = generate_eval_config(args.model, signature)
    else:
        pass

    if args.record_dir:
        if not os.path.isdir(args.record_dir):
            os.makedirs(args.record_dir, 0o777)
        cfg_file = '{}/train.yaml'.format(args.record_dir)
        with open(cfg_file, 'w+') as f:
            f.write(k8s_config)
        print("Yaml config generated at {}".format(cfg_file))
    else:
        print(k8s_config)

if __name__ == "__main__":
    main()
