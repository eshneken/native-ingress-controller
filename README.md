# OCI OKE NativeIngressController Tester
This repository has steps to:
* Create an OKE cluster along with supporting VCN
* Configure OKE cluster to run OCI Native Ingress Controller
* Create pods running echoserver, nginx, and a custom Flask server that consumes random CPU cycles to simulate work
* Expose those pods to the Internet through the ingress controller via an OCI LBaaS instance
* Enable access log collection on the LBaaS and pipe those logs to OCI Logging Analytics
* Create a Logging Analytics Query to look at backend connect time
* Exercise the Native Ingress Controller via a client tester (whether locally or through an OCI Instance Pool) to generate load and metrics to review in the OCI Console

## Create Cluster with Native Ingress Controller

1. Create OKE cluster via OCI Console wizard (creates VCN, node pools, etc).  Make sure to use AMD E5 compute shapes since subsequent instructions assume cross-compilation for AMD.

2. Create policy for native ingress controller at the compartment level while replacing CLUSTER_OCID in statements with OCID of previously create cluster

```
Allow any-user to manage load-balancers in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to use virtual-network-family in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to manage cabundles in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to manage cabundle-associations in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to manage leaf-certificates in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to read leaf-certificate-bundles in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to manage certificate-associations in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to read certificate-authorities in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to manage certificate-authority-associations in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to read certificate-authority-bundles in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to read public-ips in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to manage floating-ips in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to manage waf-family in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
Allow any-user to read cluster-family in compartment sandbox where all {request.principal.type = 'workload', request.principal.namespace = 'native-ingress-controller-system', request.principal.service_account = 'oci-native-ingress-controller', request.principal.cluster_id = 'CLUSTER_OCID'}
```

3. Enable Certificate Manager Add-On from OKE Cluster Details in OCI Console

4. Enable NativeIngressController Add-On from OKE Cluster Details in OCI Console
    1. Fill in COMPARTMENT_OCID in UI for comparmentid
    1. Fill in LBAAS_SUBNET_OCID in UI for loadBalancerSubnetid
    1. Add a key named authType with value WorkoadIdentity

5. Update security lists for VCN created during step 1
    1. Add ingress rule to *LB seclist* for 0.0.0.0/0 to route to ports 80, 443
    1. Add egress rule to *LB seclist* to route all ports, all protocols to node/pod subnet CIDR
    1. Add ingress rule to *node/pod seclist* to route all ports, all protocols from LB subnet CIDR

## Compile, dockerize, and push burn-cpu service
Included here is burn-cpu which is a small Flask app to simulate load on k8s cluster.  The code is found in python/burn-cpu.py and every time the GET endpoint is invoked the service will spin in a tight loop for a random number of seconds between 0 and 2.

1. Create a python virtual environment by running: python3 -m venv .venv

2. Activate the virtual environment: source ./.venv/bin/activate

3. Install all the Python requirements:  pip install -r python/requirements.txt

4. Navigate to the python sub-directory and init your local docker runtime (i.e. rancher desktop)

5. Build an image locally:  docker build -t burn-cpu . --platform linux/amd64

6. Log into OCIR:  
```
docker login docker login ocir.us-ashburn-1.oci.oraclecloud.com -u USERNAME -p AUTH_TOKEN 
```
where USERNAME is your object storage namespace (found under Tenancy Details in the OCI Console) followed by a slash followed by your IAM username.  For example:
```
docker login docker login ocir.us-ashburn-1.oci.oraclecloud.com -u idxhcvzolqr/first.last@oracle.com -p BFWq23a.dst2woWv_-UB
```

7. Tag the local docker image with an OCIR tag:
```
docker tag burn-cpu ocir.us-ashburn-1.oci.oraclecloud.com/NAMESPACE/public/burn-cpu:1.0
```
where NAMESPACE is your object storage namespace (found under Tenancy Details in the OCI Console)  For example:
```
docker tag burn-cpu ocir.us-ashburn-1.oci.oraclecloud.com/idxhcvzolqr/public/burn-cpu:1.0
```

8. Push the image to OCIR:
```
docker push ocir.us-ashburn-1.oci.oraclecloud.com/NAMESPACE/public/burn-cpu:1.0
```
where NAMESPACE is your object storage namespace (found under Tenancy Details in the OCI Console)  For example:
```
docker push ocir.us-ashburn-1.oci.oraclecloud.com/idxhcvzolqr/public/burn-cpu:1.0
```

9. Check the Container Registry section in the OCI Console in the root compartment to see that public/burn-cpu repo and image have been created.

10. For simplicity, change the visibility of the repo to 'Public'.  Otherwise, you will need to configure imagePullSecrets in the yamls of the following section.

## Deploy Native Ingress Controller to OKE Cluster
In previous steps you've configured the OCI Native Ingress Controller as an Add-On.  Now you need to create an instance of the Ingress with a LBaaS facing the Internet.

1. Open 1-ingress-controller-defs.yaml and 
    1. Replace COMPARTMENT_OCID with the OCID of the compartment your cluster is in
    1. Replace LBAAS_SUBNET_OCID with the OCID of the LB subnet in your cluster's VCN

2. kubectl apply -f 1-ingress-controller-defs.yaml

## Deploy some workloads and expose them to the Ingress Controller
In this stage we deploy a number of k8s deployments which can act as backend targets for the Ingress Controller.  

1. Deploy an echoserver:  kubectl apply -f 2-echoserver.yaml

8. Deploy NGINX: kubectl apply -f 3-nginx.yaml

9. Deploy the burn-cpu service previously pushed into OCIR.  This will burn CPU cycles for random timeframes between 0 and 2 seconds and generate load on the OKE cluster to help demonstrate LBaaS and OKE metrics.  
    1. Open 4-burn_cpu.yaml and replace OBJECT_STORAGE_NAMESPACE with your object storage namespace.
    1. kubectl apply -f 4-burn_cpu.yaml

10. Register all the services just deployed with the Ingress Controller: kubectl apply -f 5-ingress.yaml

11. Verify everything looks good by executing: kubectl describe ingress native-ingress-class.  Your output should look something like:
```
Name:             native-ingress-class
Labels:           <none>
Namespace:        default
Address:          129.159.210.69
Ingress Class:    native-ingress-class
Default backend:  nginx-service:80 (10.0.10.35:80,10.0.10.161:80)
Rules:
  Host        Path  Backends
  ----        ----  --------
  *
              /echo1      echoserver-service:80 (10.0.10.47:8080,10.0.10.109:8080,10.0.10.221:8080)
              /echo2      echoserver-service:80 (10.0.10.47:8080,10.0.10.109:8080,10.0.10.221:8080)
              /path1      nginx-service:80 (10.0.10.35:80,10.0.10.161:80)
              /path2      nginx-service:80 (10.0.10.35:80,10.0.10.161:80)
              /burn_cpu   burn-cpu-service:80 (10.0.10.88:5000,10.0.10.50:5000,10.0.10.171:5000 + 27 more...)
Annotations:  <none>
Events:       <none>
```

## Test the ingress locally
Start by testing the ingress controller and all of the endpoints locally.  You want to make sure that you've followed previous steps which included creating & activating a Python virtual environment and installing all the pip requirements.

1. Edit python/client.py and update the lb_base variable with the public Address returned in the previous step where you kubectl described the ingress

2. You may choose to disable or enable the various endpoints to test in the endpoints array

3. Execute: python3 client.py

4. Verify that you're getting HHTP return codes of 200 for all the calls

```
Called http://129.159.210.69/path1/, Status Code: 200, Time: 31.41 ms
Called http://129.159.210.69/burn_cpu, Status Code: 200, Time: 1682.30 ms
Called http://129.159.210.69/burn_cpu, Status Code: 200, Time: 1730.48 ms
Called http://129.159.210.69/path1/, Status Code: 200, Time: 31.18 ms
Called http://129.159.210.69/burn_cpu, Status Code: 200, Time: 1785.04 ms
Called http://129.159.210.69/path1/, Status Code: 200, Time: 31.24 ms
Called http://129.159.210.69/burn_cpu, Status Code: 200, Time: 1919.28 ms
Called http://129.159.210.69/path1/, Status Code: 200, Time: 27.65 ms
Called http://129.159.210.69/burn_cpu, Status Code: 200, Time: 1947.85 ms
Called http://129.159.210.69/burn_cpu, Status Code: 200, Time: 1983.22 ms
```

## Load test the ingress in OCI
You've tested locally, but there are only so many concurrent threads you'll be able to run from your local machine and so much network throughput you can drive from a single client.  To more fully load test the LBaaS, ingress, and backends you will want to spin up an instance pool in OCI that runs the client in parallel from multiple VMs.

1. Create a public OCI bucket called "public-bucket" and upload python/client.py into the bucket.  This will allow the curl command on line 4 of cloud-init.sh to pull down the client into each new instance (once the OBJECT_STORAGE_NAMESPACE is properly replaed with your object storage namespace)

2. Create an OCI compute instance with the following parameters:
    1. VM.Standard.A1.Flex
    1. OCPU Count: 2
    1. Memory: 12 GB
    1: OS: Oracle Linux 8
    1: VCN/Subnet:  OKE Cluster VCN and LB subnet (the one which is public and has internet gateway access)
    1. Make sure you upload your private SSH key to allow access
    1. Expand advanced options and paste the contents of cloud-init.sh into the section for cloud-init.  Make sure to replace OBJECT_STORAGE_NAMESPACE with your object storage namespace.

3.  To verify everything worked SSH into the compute instance and look at the contents of output.txt to make sure it matches the expected local testing output from the last step.

4. From the instance details panel of this compute instance in the OCI Console, select More Actions -> Create instance configuration and create an instance config called lbass-client-config.

5. Navigate to Instance configurations in the console, find your newly created instance config, and click the "Create instance pool" button to create an instance pool.  Select appropriate VCN/subnet/placement data and create whatever number of concurrent instances you want to load test from.

6. Once the instance pool starts, you will now be testing in parallel.

## Logging Analytics
We want to be able to monitor how long each backend takes to return from the perspective of the load balancer.  This data is available in the LBaaS access logs.  We will enable access logging and forward those logs to OCI Logging Analytics to allow for aggregation and searching.

1. In the OCI Console, navigate to the load balancer instance created by your ingress setup.  Click on the Logs link in the left sidebar and enable access logging.  Create a new logging group when prompted and call it lbaas_logs.

2. Navigate to Identity -> Policies and create a policy called logging-analytics-policy in the root compartment  This policy should have the following statement:
    1. allow service loganalytics to READ loganalytics-features-family in tenancy	

3. Enable OCI Logging Analytics by following [this guide](https://docs.oracle.com/en/cloud/paas/logging-analytics/logqs/#before_you_begin).  When given the option, make sure to select audit log collection and include subcompartments.  You should see options for enabling log collection and to include the logging group (lbaas_logs) you previously created.

4. You always have the ability to add more sources later by navigating to Logging Analytics -> Administration -> Add Data in the OCI Console.

5. To generate load that will populate data for analysis, start your instance pool with some number of VMs and let them run for at least 15 minutes to generate a load profile.

6. Navigate to the Log Explorer in the OCI Console by following Logging Analytics -> Log Explorer.

7. You can construct time series queries against any of the [metrics coming from the load balancer logs](https://docs.oracle.com/en-us/iaas/Content/Logging/Reference/details_for_load_balancer_logs.htm).  For example:
```
'Log Source' = 'OCI Load Balancer Access Logs' | eval 'ProcessTime in MS' = 'Backend Connect Time' * 1000 | timestats max('ProcessTime in MS') by 'OCI Resource Name'
```
8. The data here is log based information generated in the LBaaS service logs.  In addition, [load balancer metrics](https://docs.oracle.com/en-us/iaas/Content/Balance/Reference/loadbalancermetrics.htm) can be viewed by [following these instructions](https://docs.oracle.com/en-us/iaas/Content/Balance/Reference/loadbalancermetrics_topic-Using_the_Console.htm#ViewMetrics)