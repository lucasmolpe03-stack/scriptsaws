# Crear la VPC y guardar su ID
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 192.168.0.0/24 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=entorno,Value=prueba}]' \
    --query Vpc.VpcId --output text)

echo "$VPC_ID"

# Habilitar DNS en la VPC
aws ec2 modify-vpc-attribute \
    --vpc-id $VPC_ID \
    --enable-dns-hostnames

# Crear primera subred
SUB_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 192.168.0.0/28 \
    --query Subnet.SubnetId --output text)

# Crear segunda subred
SUB_ID1=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 192.168.0.16/28 \
    --query Subnet.SubnetId --output text)

echo "$SUB_ID y $SUB_ID1"

#creo el grupo de seguridad
SG_ID=$(aws ec2 create-security-group --vpc-id $VPC_ID \
    --group-name gsmio \
    --description "Mi grupo de seguridad para salir al puerto 22" \
    --query GroupId --output text)

echo $SG_ID

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --ip-permissions '[{"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH access"}]}]' 

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --ip-permissions '[{"IpProtocol": "icmp", "FromPort": -1, "ToPort": -1, "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "ICMP access"}]}]'


#creo un ec2 
EC2_ID=$(aws ec2 run-instances \
    --image-id ami-0360c520857e3138f \
    --instance-type t2.micro \
    --key-name vockey \
    --subnet-id $SUB_ID \
    --security-group-ids $SG_ID \
    --associate-public-ip-address \
    --query Instances.InstanceId --output text)

#creo un ec2 
EC2_ID1=$(aws ec2 run-instances \
    --image-id ami-0360c520857e3138f \
    --instance-type t2.micro \
    --key-name vockey \
    --subnet-id $SUB_ID1 \
    --security-group-ids $SG_ID \
    --associate-public-ip-address \
    --query Instances.InstanceId --output text)

echo $EC2_ID Y $EC2_ID1