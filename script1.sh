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
