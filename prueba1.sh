# variables
VPC_ID="vpc-00b8113465167153f"
S1="subnet-0685f6d10b65f5f2f"
I1="i-02fcb96a8d80cbf36"
I2="i-0ffb9b62bf237f969"

# crear grupo de seguridad
SG_ID=$(aws ec2 create-security-group \
  --group-name "sgalb" \
  --description "grupo de seguridad con http y https" \
  --query 'GroupId' --output text)

# editar las reglas de entrada
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# creacion del grupo de destino
TG_ARN=$(aws elbv2 create-target-group \
    --name tg-act2 \
    --protocol TCP \
    --port 80 \
    --target-type instance \
    --vpc-id $VPC_ID \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# registrar las instancias
aws elbv2 register-targets \
    --target-group-arn $TG_ARN \
    --targets Id=$I1 Id=$I2

# crear el balanceador de carga 
LB_ARN=$(aws elbv2 create-load-balancer \
  --name "mi-alb" \
  --subnets $S1 \
  --security-groups $SG_ID \
  --type network \
  --scheme internet-facing \
  --ip-address-type ipv4 \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# crear el agente de escucha
LISTENER_ARN=$(aws elbv2 create-listener \
  --load-balancer-arn $LB_ARN \
  --protocol TCP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN \
  --query 'Listeners[0].ListenerArn' --output text)