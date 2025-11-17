# Obtén los IDs de las VPCs que tienen la etiqueta entorno=prueba
VPC_IDS=$(aws ec2 describe-vpcs \
    --filters "Name=tag:entorno,Values=prueba" \
    --query "Vpcs[*].VpcId" \
    --output text)

# Recorre cada ID de VPC y elimínala
for VPC_ID in $VPC_IDS; do
    echo "Eliminando VPC $VPC_ID..."

    # Eliminar recursos asociados (puentes de internet, subredes, etc.) antes de eliminar la VPC
    # Ejemplo: elimina subredes
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text)
    for SUBNET_ID in $SUBNET_IDS; do

        #Terminar todas las instancias EC2 en la subred
        INSTANCE_IDS=$(aws ec2 describe-instances \
            --filters "Name=subnet-id,Values=$SUBNET_ID" \
            --query "Reservations[*].Instances[*].InstanceId" \
            --output text)

        
        echo " Terminando instancias en la subred $SUBNET_ID: $INSTANCE_IDS"
        aws ec2 terminate-instances --instance-ids $INSTANCE_IDS
        aws ec2 wait instance-terminated --instance-ids $INSTANCE_IDS
        echo " Instancias eliminadas."
        

        aws ec2 delete-subnet --subnet-id $SUBNET_ID
        echo " Subnet $SUBNET_ID eliminada."
    done
    
    # (Opcional) Elimina más recursos aquí como Internet Gateways, Route Tables, etc., si existen
    aws ec2 describe-security-groups \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query "SecurityGroups[*].GroupId" \
    --output text

    # Elimina la VPC
    aws ec2 delete-vpc --vpc-id $VPC_ID
    echo "VPC $VPC_ID eliminada."
done


