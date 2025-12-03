#!/usr/bin/env python3
"""
Script para crear infraestructura AWS completa:
- VPC con DNS habilitado
- Subnet con IP pública automática
- Internet Gateway
- Route Table con ruta a Internet
- Security Group (SSH + ICMP)
- Instancia EC2

Requisitos:
    pip install boto3

Configuración de credenciales AWS:
    - Opción 1: aws configure
    - Opción 2: Variables de entorno (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    - Opción 3: Archivo ~/.aws/credentials
"""

import boto3
from botocore.exceptions import ClientError

def main():
    try:
        # Inicializar cliente EC2
        print("Inicializando cliente EC2...")
        ec2 = boto3.client('ec2')
        
        # 1. Crear VPC
        print("\n[1/13] Creando VPC...")
        vpc_response = ec2.create_vpc(
            CidrBlock='192.168.0.0/24',
            TagSpecifications=[
                {'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': 'MyVpc'}]}
            ]
        )
        vpc_id = vpc_response['Vpc']['VpcId']
        print(f"✓ VPC creada: {vpc_id}")
        
        # 2. Habilitar DNS
        print("\n[2/13] Habilitando DNS en la VPC...")
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
        print("✓ DNS habilitado")
        
        # 3. Crear Subnet
        print("\n[3/13] Creando Subnet...")
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
        print("\n[4/13] Habilitando asignación automática de IP pública...")
        ec2.modify_subnet_attribute(SubnetId=subnet_id, MapPublicIpOnLaunch={'Value': True})
        print("✓ IP pública automática habilitada")
        
        # 5. Crear Internet Gateway
        print("\n[5/13] Creando Internet Gateway...")
        igw_response = ec2.create_internet_gateway(
            TagSpecifications=[
                {'ResourceType': 'internet-gateway', 'Tags': [{'Key': 'Name', 'Value': 'MiIg'}]}
            ]
        )
        igw_id = igw_response['InternetGateway']['InternetGatewayId']
        print(f"✓ Internet Gateway creado: {igw_id}")
        
        # 6. Adjuntar IGW a VPC
        print("\n[6/13] Adjuntando Internet Gateway a la VPC...")
        ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        print("✓ Internet Gateway adjuntado")
        
        # 7. Crear Route Table
        print("\n[7/13] Creando Route Table...")
        route_table_response = ec2.create_route_table(
            VpcId=vpc_id,
            TagSpecifications=[
                {'ResourceType': 'route-table', 'Tags': [{'Key': 'Name', 'Value': 'MiTablaEnrutadora'}]}
            ]
        )
        route_table_id = route_table_response['RouteTable']['RouteTableId']
        print(f"✓ Route Table creada: {route_table_id}")
        
        # 8. Agregar ruta a Internet
        print("\n[8/13] Agregando ruta hacia Internet (0.0.0.0/0)...")
        ec2.create_route(RouteTableId=route_table_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
        print("✓ Ruta 0.0.0.0/0 añadida al IGW")
        
        # 9. Asociar Route Table a Subnet
        print("\n[9/13] Asociando Route Table a la Subnet...")
        ec2.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)
        print("✓ Route Table asociada")
        
        # 10. Crear Security Group
        print("\n[10/13] Creando Security Group...")
        sg_response = ec2.create_security_group(
            VpcId=vpc_id,
            GroupName='gsmio',
            Description='Mi grupo de seguridad para salir al puerto 22'
        )
        sg_id = sg_response['GroupId']
        print(f"✓ Security Group creado: {sg_id}")
        
        # 11. Autorizar SSH
        print("\n[11/13] Autorizando tráfico SSH (puerto 22)...")
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
        print("\n[12/13] Autorizando tráfico ICMP (ping)...")
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
        
        # 13. Crear EC2 Instance
        print("\n[13/13] Creando instancia EC2...")
        instance_response = ec2.run_instances(
            ImageId='ami-0360c520857e3138f',
            InstanceType='t2.micro',
            KeyName='vockey',
            MinCount=1,
            MaxCount=1,
            NetworkInterfaces=[
                {
                    'DeviceIndex': 0,
                    'SubnetId': subnet_id,
                    'Groups': [sg_id],
                    'AssociatePublicIpAddress': True
                }
            ],
            TagSpecifications=[
                {'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'miec2'}]}
            ]
        )
        instance_id = instance_response['Instances'][0]['InstanceId']
        print(f"✓ Instancia EC2 creada: {instance_id}")
        
        # Resumen final
        print("\n" + "="*60)
        print("INFRAESTRUCTURA CREADA EXITOSAMENTE")
        print("="*60)
        print(f"VPC ID:              {vpc_id}")
        print(f"Subnet ID:           {subnet_id}")
        print(f"Internet Gateway:    {igw_id}")
        print(f"Route Table ID:      {route_table_id}")
        print(f"Security Group ID:   {sg_id}")
        print(f"EC2 Instance ID:     {instance_id}")
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
