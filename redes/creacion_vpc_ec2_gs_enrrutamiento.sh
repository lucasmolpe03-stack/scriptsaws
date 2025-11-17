#creo la vpc y devuelvo su id
VPC_ID=$(aws ec2 create-vpc --cidr-block 192.168.0.0/24 --query Vpc.VpcId --output text \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=MyVpc}]' \
    --query Vpc.VpcId --output text)

#muestro el id de la vpc
echo $VPC_ID

#habilito dns en la vpc
aws ec2 modify-vpc-attribute \
    --vpc-id $VPC_ID \
    --enable-dns-hostnames "{\"Value\":true}"

#crear una subnet
SUB_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 192.168.0.0/28 \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=mi-subred-lucas1}]' \
    --query Subnet.SubnetId --output text)

echo $SUB_ID

#habilito la asignacion de ipv4publica en la subred 
#comprobar como NO se habilita y tenemos que hacerlo a porteriori
aws ec2 modify-subnet-attribute --subnet-id $SUB_ID --map-public-ip-on-launch

#crear internet gateway
IG_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=MiIg}]' \
    --query 'InternetGateway.InternetGatewayId' --output text)

echo $IG_ID

#adjuntar internet gateway
aws ec2 attach-internet-gateway \
    --internet-gateway-id $IG_ID \
    --vpc-id $VPC_ID

#crear tabla de enrutamiento
TE_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=MiTablaEnrutadora}]' \
    --query 'RouteTable.RouteTableId' --output text)

echo $TE_ID

# Agregar ruta hacia internet
aws ec2 create-route \
    --route-table-id $TE_ID \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id $IG_ID

echo "Ruta 0.0.0.0/0 añadida al IGW"

# Asociar la tabla de rutas a la subred
aws ec2 associate-route-table \
    --route-table-id $TE_ID \
    --subnet-id $SUB_ID

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
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=miec2}]' \
    --query Instances.InstanceId --output text)