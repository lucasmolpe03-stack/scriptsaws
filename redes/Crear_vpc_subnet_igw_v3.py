#!/usr/bin/env python3
"""
Versión 1: Crear VPC con DNS habilitado

Este script crea:
- VPC con CIDR 192.168.0.0/24
- Habilita DNS hostnames en la VPC
"""

import boto3
from botocore.exceptions import ClientError

def main():
    try:
        # Inicializar cliente EC2
        print("Inicializando cliente EC2...")
        ec2 = boto3.client('ec2')
        
        # 1. Crear VPC
        print("\n[1/3] Creando VPC...")
        vpc_response = ec2.create_vpc(
            CidrBlock='192.168.0.0/24',
            TagSpecifications=[
                {'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': 'MyVpc'}]}
            ]
        )
        vpc_id = vpc_response['Vpc']['VpcId']
        print(f"✓ VPC creada: {vpc_id}")
        
        # 2. Habilitar DNS
        print("\n[2/3] Habilitando DNS en la VPC...")
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
        print("✓ DNS habilitado")

        # 3. Crear Subnet
        print("\n[3/3] Creando Subnet...")
        subnet_response = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock='192.168.0.0/28',
            TagSpecifications=[
                {'ResourceType': 'subnet', 'Tags': [{'Key': 'Name', 'Value': 'mi-subred-lucas1'}]}
            ]
        )
        subnet_id = subnet_response['Subnet']['SubnetId']
        print(f"✓ Subnet creada: {subnet_id}")
        
        
        # 4. Habilitar IP pública automática
        print("\n[4/6] Habilitando asignación automática de IP pública...")
        ec2.modify_subnet_attribute(SubnetId=subnet_id, MapPublicIpOnLaunch={'Value': True})
        print("✓ IP pública automática habilitada")
        
        # 5. Crear Internet Gateway
        print("\n[5/6] Creando Internet Gateway...")
        igw_response = ec2.create_internet_gateway(
            TagSpecifications=[
                {'ResourceType': 'internet-gateway', 'Tags': [{'Key': 'Name', 'Value': 'MiIg'}]}
            ]
        )
        igw_id = igw_response['InternetGateway']['InternetGatewayId']
        print(f"✓ Internet Gateway creado: {igw_id}")
        
        # 6. Adjuntar IGW a VPC
        print("\n[6/6] Adjuntando Internet Gateway a la VPC...")
        ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        print("✓ Internet Gateway adjuntado")
        
        # Resumen final
        print("\n" + "="*60)
        print("VPC, SUBNET E INTERNET GATEWAY CREADOS EXITOSAMENTE")
        print("="*60)
        print(f"VPC ID:              {vpc_id}")
        print(f"Subnet ID:           {subnet_id}")
        print(f"Internet Gateway ID: {igw_id}")
        print("="*60)
        
    except ClientError as e:
        print(f"\n❌ Error de AWS: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
