#creo la vpc y devuelvo su id
VPC_ID=$(aws ec2 create-vpc --cidr-block 192.168.0.0/24 --query Vpc.VpcId --output text \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=MyVpc}]' \
    --query Vpc.VpcId --output text)

#muestro el id de la vpc
echo $VPC_ID

#habilitodns en la vpc
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