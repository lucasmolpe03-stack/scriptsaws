#!/usr/bin/env python3
"""
PLANTILLA FINAL UNIFICADA - INFRAESTRUCTURA AWS MULTI-REGIÓN
============================================================

Script completo que despliega infraestructura en Oregon y Virginia:
- VPCs, Subnets, IGWs, NAT Gateways
- Instancias EC2 (sin KeyPair en Oregon, con vockey en Virginia)
- Network ACLs
- VPC Peering para conectividad entre regiones

Uso: py plantilla_final.py
"""

import boto3
import time
import sys

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

REGION_OREGON = 'us-west-2'
REGION_VIRGINIA = 'us-east-1'

OREGON_VPC_CIDR = '10.0.0.0/16'
OREGON_PUBLIC_SUBNET_CIDR = '10.0.1.0/24'
OREGON_PRIVATE_SUBNET_CIDR = '10.0.2.0/24'

VIRGINIA_VPC_CIDR = '10.1.0.0/16'
VIRGINIA_PUBLIC_SUBNET_CIDR = '10.1.1.0/24'
VIRGINIA_PRIVATE_SUBNET_CIDR = '10.1.2.0/24'

AMI_OREGON = 'ami-00a8151272c45cd8e'
AMI_VIRGINIA = 'ami-07ff62358b87c7116'

KEY_NAME_VIRGINIA = 'vockey'

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def print_step(step, total, desc):
    print(f"\n[{step}/{total}] {desc}")

# ============================================================================
# OREGON
# ============================================================================

def create_oregon():
    print("\n" + "="*70)
    print("OREGON (us-west-2)")
    print("="*70)
    
    ec2 = boto3.client('ec2', region_name=REGION_OREGON)
    r = {}
    
    # VPC
    print_step(1, 8, "VPC")
    vpc = ec2.create_vpc(CidrBlock=OREGON_VPC_CIDR, TagSpecifications=[{'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': 'VPC-Oregon'}]}])
    r['vpc_id'] = vpc['Vpc']['VpcId']
    ec2.modify_vpc_attribute(VpcId=r['vpc_id'], EnableDnsHostnames={'Value': True})
    ec2.modify_vpc_attribute(VpcId=r['vpc_id'], EnableDnsSupport={'Value': True})
    print(f"   ✓ {r['vpc_id']}")
    
    # Subnets
    print_step(2, 8, "Subnets")
    pub = ec2.create_subnet(VpcId=r['vpc_id'], CidrBlock=OREGON_PUBLIC_SUBNET_CIDR, AvailabilityZone=f'{REGION_OREGON}a', TagSpecifications=[{'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-Public-Subnet'}]}])
    r['public_subnet_id'] = pub['Subnet']['SubnetId']
    ec2.modify_subnet_attribute(SubnetId=r['public_subnet_id'], MapPublicIpOnLaunch={'Value': True})
    
    priv = ec2.create_subnet(VpcId=r['vpc_id'], CidrBlock=OREGON_PRIVATE_SUBNET_CIDR, AvailabilityZone=f'{REGION_OREGON}a', TagSpecifications=[{'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-Private-Subnet'}]}])
    r['private_subnet_id'] = priv['Subnet']['SubnetId']
    print(f"   ✓ Public: {r['public_subnet_id']}, Private: {r['private_subnet_id']}")
    
    # IGW
    print_step(3, 8, "Internet Gateway")
    igw = ec2.create_internet_gateway(TagSpecifications=[{'ResourceType': 'internet-gateway', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-IGW'}]}])
    r['igw_id'] = igw['InternetGateway']['InternetGatewayId']
    ec2.attach_internet_gateway(InternetGatewayId=r['igw_id'], VpcId=r['vpc_id'])
    print(f"   ✓ {r['igw_id']}")
    
    # NAT
    print_step(4, 8, "NAT Gateway")
    eip = ec2.allocate_address(Domain='vpc', TagSpecifications=[{'ResourceType': 'elastic-ip', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-NAT-EIP'}]}])
    r['eip_id'] = eip['AllocationId']
    nat = ec2.create_nat_gateway(SubnetId=r['public_subnet_id'], AllocationId=r['eip_id'], TagSpecifications=[{'ResourceType': 'natgateway', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-NAT'}]}])
    r['nat_id'] = nat['NatGateway']['NatGatewayId']
    print(f"   ⏳ Esperando NAT Gateway...")
    ec2.get_waiter('nat_gateway_available').wait(NatGatewayIds=[r['nat_id']])
    print(f"   ✓ {r['nat_id']}")
    
    # Route Tables
    print_step(5, 8, "Route Tables")
    pub_rt = ec2.create_route_table(VpcId=r['vpc_id'], TagSpecifications=[{'ResourceType': 'route-table', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-Public-RT'}]}])
    r['public_rt_id'] = pub_rt['RouteTable']['RouteTableId']
    ec2.create_route(RouteTableId=r['public_rt_id'], DestinationCidrBlock='0.0.0.0/0', GatewayId=r['igw_id'])
    ec2.associate_route_table(RouteTableId=r['public_rt_id'], SubnetId=r['public_subnet_id'])
    
    priv_rt = ec2.create_route_table(VpcId=r['vpc_id'], TagSpecifications=[{'ResourceType': 'route-table', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-Private-RT'}]}])
    r['private_rt_id'] = priv_rt['RouteTable']['RouteTableId']
    ec2.create_route(RouteTableId=r['private_rt_id'], DestinationCidrBlock='0.0.0.0/0', NatGatewayId=r['nat_id'])
    ec2.associate_route_table(RouteTableId=r['private_rt_id'], SubnetId=r['private_subnet_id'])
    print(f"   ✓ Configuradas")
    
    # Security Group
    print_step(6, 8, "Security Group")
    sg = ec2.create_security_group(GroupName='Oregon-SG', Description='SG Oregon', VpcId=r['vpc_id'], TagSpecifications=[{'ResourceType': 'security-group', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-SG'}]}])
    r['sg_id'] = sg['GroupId']
    ec2.authorize_security_group_ingress(GroupId=r['sg_id'], IpPermissions=[
        {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': '-1', 'IpRanges': [{'CidrIp': VIRGINIA_VPC_CIDR}]}
    ])
    print(f"   ✓ {r['sg_id']}")
    
    # NACLs
    print_step(7, 8, "Network ACLs")
    pub_nacl = ec2.create_network_acl(VpcId=r['vpc_id'], TagSpecifications=[{'ResourceType': 'network-acl', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-Public-NACL'}]}])
    r['public_nacl_id'] = pub_nacl['NetworkAcl']['NetworkAclId']
    
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=100, Protocol='6', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', PortRange={'From': 80, 'To': 80})
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=110, Protocol='6', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', PortRange={'From': 443, 'To': 443})
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=120, Protocol='6', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', PortRange={'From': 22, 'To': 22})
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=130, Protocol='6', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', PortRange={'From': 1024, 'To': 65535})
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=140, Protocol='1', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', IcmpTypeCode={'Type': -1, 'Code': -1})
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=100, Protocol='-1', RuleAction='allow', Egress=True, CidrBlock='0.0.0.0/0')
    
    assocs = ec2.describe_network_acls(Filters=[{'Name': 'association.subnet-id', 'Values': [r['public_subnet_id']]}])
    if assocs['NetworkAcls']:
        ec2.replace_network_acl_association(AssociationId=assocs['NetworkAcls'][0]['Associations'][0]['NetworkAclAssociationId'], NetworkAclId=r['public_nacl_id'])
    
    priv_nacl = ec2.create_network_acl(VpcId=r['vpc_id'], TagSpecifications=[{'ResourceType': 'network-acl', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-Private-NACL'}]}])
    r['private_nacl_id'] = priv_nacl['NetworkAcl']['NetworkAclId']
    
    ec2.create_network_acl_entry(NetworkAclId=r['private_nacl_id'], RuleNumber=100, Protocol='-1', RuleAction='allow', Egress=False, CidrBlock=OREGON_PUBLIC_SUBNET_CIDR)
    ec2.create_network_acl_entry(NetworkAclId=r['private_nacl_id'], RuleNumber=110, Protocol='6', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', PortRange={'From': 1024, 'To': 65535})
    ec2.create_network_acl_entry(NetworkAclId=r['private_nacl_id'], RuleNumber=100, Protocol='-1', RuleAction='allow', Egress=True, CidrBlock='0.0.0.0/0')
    
    assocs = ec2.describe_network_acls(Filters=[{'Name': 'association.subnet-id', 'Values': [r['private_subnet_id']]}])
    if assocs['NetworkAcls']:
        ec2.replace_network_acl_association(AssociationId=assocs['NetworkAcls'][0]['Associations'][0]['NetworkAclAssociationId'], NetworkAclId=r['private_nacl_id'])
    print(f"   ✓ Configuradas")
    
    # Instancias (SIN KeyPair)
    print_step(8, 8, "Instancias EC2")
    pub_inst = ec2.run_instances(ImageId=AMI_OREGON, InstanceType='t2.micro', MinCount=1, MaxCount=1,
        NetworkInterfaces=[{'DeviceIndex': 0, 'SubnetId': r['public_subnet_id'], 'Groups': [r['sg_id']], 'AssociatePublicIpAddress': True}],
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-Public-Instance'}]}])
    r['public_instance_id'] = pub_inst['Instances'][0]['InstanceId']
    
    priv_inst = ec2.run_instances(ImageId=AMI_OREGON, InstanceType='t2.micro', MinCount=1, MaxCount=1,
        NetworkInterfaces=[{'DeviceIndex': 0, 'SubnetId': r['private_subnet_id'], 'Groups': [r['sg_id']], 'AssociatePublicIpAddress': False}],
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-Private-Instance'}]}])
    r['private_instance_id'] = priv_inst['Instances'][0]['InstanceId']
    print(f"   ✓ {r['public_instance_id']} (Pub), {r['private_instance_id']} (Priv)")
    
    return r

# ============================================================================
# VIRGINIA
# ============================================================================

def create_virginia():
    print("\n" + "="*70)
    print("VIRGINIA (us-east-1)")
    print("="*70)
    
    ec2 = boto3.client('ec2', region_name=REGION_VIRGINIA)
    r = {}
    
    # VPC
    print_step(1, 8, "VPC")
    vpc = ec2.create_vpc(CidrBlock=VIRGINIA_VPC_CIDR, TagSpecifications=[{'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': 'VPC-Virginia'}]}])
    r['vpc_id'] = vpc['Vpc']['VpcId']
    ec2.modify_vpc_attribute(VpcId=r['vpc_id'], EnableDnsHostnames={'Value': True})
    ec2.modify_vpc_attribute(VpcId=r['vpc_id'], EnableDnsSupport={'Value': True})
    print(f"   ✓ {r['vpc_id']}")
    
    # Subnets
    print_step(2, 8, "Subnets")
    pub = ec2.create_subnet(VpcId=r['vpc_id'], CidrBlock=VIRGINIA_PUBLIC_SUBNET_CIDR, AvailabilityZone=f'{REGION_VIRGINIA}a', TagSpecifications=[{'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-Public-Subnet'}]}])
    r['public_subnet_id'] = pub['Subnet']['SubnetId']
    ec2.modify_subnet_attribute(SubnetId=r['public_subnet_id'], MapPublicIpOnLaunch={'Value': True})
    
    priv = ec2.create_subnet(VpcId=r['vpc_id'], CidrBlock=VIRGINIA_PRIVATE_SUBNET_CIDR, AvailabilityZone=f'{REGION_VIRGINIA}a', TagSpecifications=[{'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-Private-Subnet'}]}])
    r['private_subnet_id'] = priv['Subnet']['SubnetId']
    print(f"   ✓ Public: {r['public_subnet_id']}, Private: {r['private_subnet_id']}")
    
    # IGW
    print_step(3, 8, "Internet Gateway")
    igw = ec2.create_internet_gateway(TagSpecifications=[{'ResourceType': 'internet-gateway', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-IGW'}]}])
    r['igw_id'] = igw['InternetGateway']['InternetGatewayId']
    ec2.attach_internet_gateway(InternetGatewayId=r['igw_id'], VpcId=r['vpc_id'])
    print(f"   ✓ {r['igw_id']}")
    
    # NAT
    print_step(4, 8, "NAT Gateway")
    eip = ec2.allocate_address(Domain='vpc', TagSpecifications=[{'ResourceType': 'elastic-ip', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-NAT-EIP'}]}])
    r['eip_id'] = eip['AllocationId']
    nat = ec2.create_nat_gateway(SubnetId=r['public_subnet_id'], AllocationId=r['eip_id'], TagSpecifications=[{'ResourceType': 'natgateway', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-NAT'}]}])
    r['nat_id'] = nat['NatGateway']['NatGatewayId']
    print(f"   ⏳ Esperando NAT Gateway...")
    ec2.get_waiter('nat_gateway_available').wait(NatGatewayIds=[r['nat_id']])
    print(f"   ✓ {r['nat_id']}")
    
    # Route Tables
    print_step(5, 8, "Route Tables")
    pub_rt = ec2.create_route_table(VpcId=r['vpc_id'], TagSpecifications=[{'ResourceType': 'route-table', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-Public-RT'}]}])
    r['public_rt_id'] = pub_rt['RouteTable']['RouteTableId']
    ec2.create_route(RouteTableId=r['public_rt_id'], DestinationCidrBlock='0.0.0.0/0', GatewayId=r['igw_id'])
    ec2.associate_route_table(RouteTableId=r['public_rt_id'], SubnetId=r['public_subnet_id'])
    
    priv_rt = ec2.create_route_table(VpcId=r['vpc_id'], TagSpecifications=[{'ResourceType': 'route-table', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-Private-RT'}]}])
    r['private_rt_id'] = priv_rt['RouteTable']['RouteTableId']
    ec2.create_route(RouteTableId=r['private_rt_id'], DestinationCidrBlock='0.0.0.0/0', NatGatewayId=r['nat_id'])
    ec2.associate_route_table(RouteTableId=r['private_rt_id'], SubnetId=r['private_subnet_id'])
    print(f"   ✓ Configuradas")
    
    # Security Group
    print_step(6, 8, "Security Group")
    sg = ec2.create_security_group(GroupName='Virginia-SG', Description='SG Virginia', VpcId=r['vpc_id'], TagSpecifications=[{'ResourceType': 'security-group', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-SG'}]}])
    r['sg_id'] = sg['GroupId']
    ec2.authorize_security_group_ingress(GroupId=r['sg_id'], IpPermissions=[
        {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': '-1', 'IpRanges': [{'CidrIp': OREGON_VPC_CIDR}]}
    ])
    print(f"   ✓ {r['sg_id']}")
    
    # NACLs
    print_step(7, 8, "Network ACLs")
    pub_nacl = ec2.create_network_acl(VpcId=r['vpc_id'], TagSpecifications=[{'ResourceType': 'network-acl', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-Public-NACL'}]}])
    r['public_nacl_id'] = pub_nacl['NetworkAcl']['NetworkAclId']
    
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=100, Protocol='6', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', PortRange={'From': 80, 'To': 80})
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=110, Protocol='6', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', PortRange={'From': 443, 'To': 443})
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=120, Protocol='6', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', PortRange={'From': 22, 'To': 22})
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=130, Protocol='6', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', PortRange={'From': 1024, 'To': 65535})
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=140, Protocol='1', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', IcmpTypeCode={'Type': -1, 'Code': -1})
    ec2.create_network_acl_entry(NetworkAclId=r['public_nacl_id'], RuleNumber=100, Protocol='-1', RuleAction='allow', Egress=True, CidrBlock='0.0.0.0/0')
    
    assocs = ec2.describe_network_acls(Filters=[{'Name': 'association.subnet-id', 'Values': [r['public_subnet_id']]}])
    if assocs['NetworkAcls']:
        ec2.replace_network_acl_association(AssociationId=assocs['NetworkAcls'][0]['Associations'][0]['NetworkAclAssociationId'], NetworkAclId=r['public_nacl_id'])
    
    priv_nacl = ec2.create_network_acl(VpcId=r['vpc_id'], TagSpecifications=[{'ResourceType': 'network-acl', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-Private-NACL'}]}])
    r['private_nacl_id'] = priv_nacl['NetworkAcl']['NetworkAclId']
    
    ec2.create_network_acl_entry(NetworkAclId=r['private_nacl_id'], RuleNumber=100, Protocol='-1', RuleAction='allow', Egress=False, CidrBlock=VIRGINIA_PUBLIC_SUBNET_CIDR)
    ec2.create_network_acl_entry(NetworkAclId=r['private_nacl_id'], RuleNumber=110, Protocol='6', RuleAction='allow', Egress=False, CidrBlock='0.0.0.0/0', PortRange={'From': 1024, 'To': 65535})
    ec2.create_network_acl_entry(NetworkAclId=r['private_nacl_id'], RuleNumber=100, Protocol='-1', RuleAction='allow', Egress=True, CidrBlock='0.0.0.0/0')
    
    assocs = ec2.describe_network_acls(Filters=[{'Name': 'association.subnet-id', 'Values': [r['private_subnet_id']]}])
    if assocs['NetworkAcls']:
        ec2.replace_network_acl_association(AssociationId=assocs['NetworkAcls'][0]['Associations'][0]['NetworkAclAssociationId'], NetworkAclId=r['private_nacl_id'])
    print(f"   ✓ Configuradas")
    
    # Instancias (CON KeyPair)
    print_step(8, 8, "Instancias EC2")
    pub_inst = ec2.run_instances(ImageId=AMI_VIRGINIA, InstanceType='t2.micro', KeyName=KEY_NAME_VIRGINIA, MinCount=1, MaxCount=1,
        NetworkInterfaces=[{'DeviceIndex': 0, 'SubnetId': r['public_subnet_id'], 'Groups': [r['sg_id']], 'AssociatePublicIpAddress': True}],
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-Public-Instance'}]}])
    r['public_instance_id'] = pub_inst['Instances'][0]['InstanceId']
    
    priv_inst = ec2.run_instances(ImageId=AMI_VIRGINIA, InstanceType='t2.micro', KeyName=KEY_NAME_VIRGINIA, MinCount=1, MaxCount=1,
        NetworkInterfaces=[{'DeviceIndex': 0, 'SubnetId': r['private_subnet_id'], 'Groups': [r['sg_id']], 'AssociatePublicIpAddress': False}],
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Virginia-Private-Instance'}]}])
    r['private_instance_id'] = priv_inst['Instances'][0]['InstanceId']
    print(f"   ✓ {r['public_instance_id']} (Pub), {r['private_instance_id']} (Priv)")
    
    return r

# ============================================================================
# VPC PEERING
# ============================================================================

def create_peering(oregon, virginia):
    print("\n" + "="*70)
    print("VPC PEERING")
    print("="*70)
    
    ec2_or = boto3.client('ec2', region_name=REGION_OREGON)
    ec2_va = boto3.client('ec2', region_name=REGION_VIRGINIA)
    
    print_step(1, 2, "Creando conexión de peering")
    peer = ec2_or.create_vpc_peering_connection(
        VpcId=oregon['vpc_id'],
        PeerVpcId=virginia['vpc_id'],
        PeerRegion=REGION_VIRGINIA,
        TagSpecifications=[{'ResourceType': 'vpc-peering-connection', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-Virginia-Peering'}]}]
    )
    peering_id = peer['VpcPeeringConnection']['VpcPeeringConnectionId']
    print(f"   ✓ Solicitud: {peering_id}")
    
    time.sleep(5)
    ec2_va.accept_vpc_peering_connection(VpcPeeringConnectionId=peering_id)
    print(f"   ✓ Aceptado en Virginia")
    
    print_step(2, 2, "Configurando rutas")
    ec2_or.create_route(RouteTableId=oregon['public_rt_id'], DestinationCidrBlock=VIRGINIA_VPC_CIDR, VpcPeeringConnectionId=peering_id)
    ec2_or.create_route(RouteTableId=oregon['private_rt_id'], DestinationCidrBlock=VIRGINIA_VPC_CIDR, VpcPeeringConnectionId=peering_id)
    ec2_va.create_route(RouteTableId=virginia['public_rt_id'], DestinationCidrBlock=OREGON_VPC_CIDR, VpcPeeringConnectionId=peering_id)
    ec2_va.create_route(RouteTableId=virginia['private_rt_id'], DestinationCidrBlock=OREGON_VPC_CIDR, VpcPeeringConnectionId=peering_id)
    print(f"   ✓ Rutas configuradas")
    
    return peering_id

# ============================================================================
# TRANSIT GATEWAY
# ============================================================================

def create_tgw(oregon):
    print("\n" + "="*70)
    print("TRANSIT GATEWAY")
    print("="*70)
    
    ec2 = boto3.client('ec2', region_name=REGION_OREGON)
    
    print_step(1, 2, "Creando Transit Gateway en Oregon")
    tgw = ec2.create_transit_gateway(
        Description='Multi-Region TGW',
        Options={
            'AmazonSideAsn': 64512,
            'DefaultRouteTableAssociation': 'enable',
            'DefaultRouteTablePropagation': 'enable',
            'DnsSupport': 'enable',
            'VpnEcmpSupport': 'enable'
        },
        TagSpecifications=[{'ResourceType': 'transit-gateway', 'Tags': [{'Key': 'Name', 'Value': 'Multi-Region-TGW'}]}]
    )
    tgw_id = tgw['TransitGateway']['TransitGatewayId']
    print(f"   ✓ TGW creado: {tgw_id}")
    
    print(f"   ⏳ Esperando disponibilidad del TGW...")
    for _ in range(60):
        resp = ec2.describe_transit_gateways(TransitGatewayIds=[tgw_id])
        state = resp['TransitGateways'][0]['State']
        if state == 'available':
            break
        time.sleep(10)
    print(f"   ✓ TGW disponible")
    
    print_step(2, 2, "Creando VPC Attachment")
    att = ec2.create_transit_gateway_vpc_attachment(
        TransitGatewayId=tgw_id,
        VpcId=oregon['vpc_id'],
        SubnetIds=[oregon['private_subnet_id']],
        TagSpecifications=[{'ResourceType': 'transit-gateway-attachment', 'Tags': [{'Key': 'Name', 'Value': 'Oregon-VPC-Attachment'}]}]
    )
    att_id = att['TransitGatewayVpcAttachment']['TransitGatewayAttachmentId']
    print(f"   ✓ Attachment creado: {att_id}")
    
    print(f"   ⏳ Esperando disponibilidad del attachment...")
    for _ in range(60):
        resp = ec2.describe_transit_gateway_vpc_attachments(TransitGatewayAttachmentIds=[att_id])
        state = resp['TransitGatewayVpcAttachments'][0]['State']
        if state == 'available':
            break
        time.sleep(5)
    print(f"   ✓ Attachment disponible")
    
    return tgw_id

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*70)
    print("🚀 DESPLIEGUE COMPLETO AWS MULTI-REGIÓN")
    print("="*70)
    
    try:
        oregon = create_oregon()
        virginia = create_virginia()
        peering = create_peering(oregon, virginia)
        tgw = create_tgw(oregon)
        
        print("\n" + "="*70)
        print("✅ DESPLIEGUE COMPLETADO EXITOSAMENTE")
        print("="*70)
        print(f"\nOregon VPC:    {oregon['vpc_id']}")
        print(f"Virginia VPC:  {virginia['vpc_id']}")
        print(f"VPC Peering:   {peering}")
        print(f"Transit GW:    {tgw}")
        print("\n" + "="*70)
        
        return 0
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
