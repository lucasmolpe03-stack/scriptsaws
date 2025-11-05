# Sustituye estos valores
NAME_PREFIX="mi-alb"
VPC_ID="vpc-00b8113465167153f"
SUBNET_IDS="subnet-0685f6d10b65f5f2f"
INSTANCE_IDS=("i-02fcb96a8d80cbf36" "i-0ffb9b62bf237f969")

ALB_SG_ID=$(aws ec2 create-security-group \
  --group-name "${NAME_PREFIX}-alb-sg" \
  --description "SG para ALB (HTTP/HTTPS)" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

# Permitir HTTP (80) desde internet
aws ec2 authorize-security-group-ingress --group-id $ALB_SG_ID \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

# (Opcional) Permitir HTTPS (443)
aws ec2 authorize-security-group-ingress --group-id $ALB_SG_ID \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

echo "ALB Security Group: $ALB_SG_ID"

