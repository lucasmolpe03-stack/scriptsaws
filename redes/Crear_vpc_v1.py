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
        print("\n[1/2] Creando VPC...")
        vpc_response = ec2.create_vpc(
            CidrBlock='192.168.0.0/24',
            TagSpecifications=[
                {'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': 'MyVpc'}]}
            ]
        )
        vpc_id = vpc_response['Vpc']['VpcId']
        print(f"✓ VPC creada: {vpc_id}")
        
        # 2. Habilitar DNS
        print("\n[2/2] Habilitando DNS en la VPC...")
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
        print("✓ DNS habilitado")
        
        # Resumen final
        print("\n" + "="*60)
        print("VPC CREADA EXITOSAMENTE")
        print("="*60)
        print(f"VPC ID: {vpc_id}")
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
