#!/usr/bin/env python3
"""
Versión 5: Crear VPC, Subnet, Internet Gateway, Route Table y Security Group

Este script crea:
- VPC con CIDR 192.168.0.0/24
- Habilita DNS hostnames en la VPC
- Subnet con CIDR 192.168.0.0/28
- Habilita asignación automática de IP pública en la subnet
- Internet Gateway
- Adjunta el Internet Gateway a la VPC
- Route Table
- Ruta hacia Internet (0.0.0.0/0)
- Asocia la Route Table a la Subnet
- Security Group
- Reglas de ingreso para SSH (puerto 22)
- Reglas de ingreso para ICMP (ping)
"""

import boto3
from botocore.exceptions import ClientError

def main():
    try:
        # Inicializar cliente EC2
        print("Inicializando cliente EC2...")
        ec2 = boto3.client('ec2')
        
        # 1. Crear VPC
        print("\n[1/12] Creando VPC...")
        vpc_response = ec2.create_vpc(
            CidrBlock='192.168.0.0/24',
            TagSpecifications=[
                {'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': 'MyVpc'}]}
            ]
        )
        vpc_id = vpc_response['Vpc']['VpcId']
        print(f"✓ VPC creada: {vpc_id}")
        
        # 2. Habilitar DNS
        print("\n[2/12] Habilitando DNS en la VPC...")
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
        print("✓ DNS habilitado")
        
        # 3. Crear Subnet
        print("\n[3/12] Creando Subnet...")
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
        print("\n[4/12] Habilitando asignación automática de IP pública...")
        ec2.modify_subnet_attribute(SubnetId=subnet_id, MapPublicIpOnLaunch={'Value': True})
        print("✓ IP pública automática habilitada")
        
        # 5. Crear Internet Gateway
        print("\n[5/12] Creando Internet Gateway...")
        igw_response = ec2.create_internet_gateway(
            TagSpecifications=[
                {'ResourceType': 'internet-gateway', 'Tags': [{'Key': 'Name', 'Value': 'MiIg'}]}
            ]
        )
        igw_id = igw_response['InternetGateway']['InternetGatewayId']
        print(f"✓ Internet Gateway creado: {igw_id}")
        
        # 6. Adjuntar IGW a VPC
        print("\n[6/12] Adjuntando Internet Gateway a la VPC...")
        ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        print("✓ Internet Gateway adjuntado")
        
        # 7. Crear Route Table
        print("\n[7/12] Creando Route Table...")
        route_table_response = ec2.create_route_table(
            VpcId=vpc_id,
            TagSpecifications=[
                {'ResourceType': 'route-table', 'Tags': [{'Key': 'Name', 'Value': 'MiTablaEnrutadora'}]}
            ]
        )
        route_table_id = route_table_response['RouteTable']['RouteTableId']
        print(f"✓ Route Table creada: {route_table_id}")
        
        # 8. Agregar ruta a Internet
        print("\n[8/12] Agregando ruta hacia Internet (0.0.0.0/0)...")
        ec2.create_route(RouteTableId=route_table_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
        print("✓ Ruta 0.0.0.0/0 añadida al IGW")
        
        # 9. Asociar Route Table a Subnet
        print("\n[9/12] Asociando Route Table a la Subnet...")
        ec2.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)
        print("✓ Route Table asociada")
        
        # 10. Crear Security Group
        print("\n[10/12] Creando Security Group...")
        sg_response = ec2.create_security_group(
            VpcId=vpc_id,
            GroupName='gsmio',
            Description='Mi grupo de seguridad para salir al puerto 22'
        )
        sg_id = sg_response['GroupId']
        print(f"✓ Security Group creado: {sg_id}")
        
        # 11. Autorizar SSH
        print("\n[11/12] Autorizando tráfico SSH (puerto 22)...")
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH access'}]
                }
            ]
        )
        print("✓ Regla SSH autorizada")
        
        # 12. Autorizar ICMP
        print("\n[12/12] Autorizando tráfico ICMP (ping)...")
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'icmp',
                    'FromPort': -1,
                    'ToPort': -1,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'ICMP access'}]
                }
            ]
        )
        print("✓ Regla ICMP autorizada")
        
        # Resumen final
        print("\n" + "="*60)
        print("RED Y SEGURIDAD CREADAS EXITOSAMENTE")
        print("="*60)
        print(f"VPC ID:              {vpc_id}")
        print(f"Subnet ID:           {subnet_id}")
        print(f"Internet Gateway ID: {igw_id}")
        print(f"Route Table ID:      {route_table_id}")
        print(f"Security Group ID:   {sg_id}")
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
