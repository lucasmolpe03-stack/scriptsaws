#!/bin/bash
# Script: copia_instancia.sh
# Descripción: Crea una copia de una instancia EC2 en otra región, usando el mismo tipo de instancia.
# Uso: ./copia_instancia.sh <region_origen> <id_instancia_origen> <region_destino>

# --- Validación de parámetros ---
if [ $# -ne 3 ]; then
  echo "Uso: $0 <region_origen> <id_instancia_origen> <region_destino>"
  exit 1
fi

REGION_ORIGEN=$1
INSTANCIA_ORIGEN=$2
REGION_DESTINO=$3

# --- Comprobación de la instancia origen ---
echo "Comprobando si la instancia $INSTANCIA_ORIGEN existe en la región $REGION_ORIGEN..."
EXISTE=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCIA_ORIGEN" \
  --region "$REGION_ORIGEN" \
  --query "Reservations[*].Instances[*].InstanceId" \
  --output text 2>/dev/null)

if [ -z "$EXISTE" ]; then
  echo "Error: la instancia $INSTANCIA_ORIGEN no existe en la región $REGION_ORIGEN."
  exit 1
fi
echo "Instancia encontrada."

# --- Obtener tipo de instancia origen ---
INSTANCE_TYPE=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCIA_ORIGEN" \
  --region "$REGION_ORIGEN" \
  --query "Reservations[0].Instances[0].InstanceType" \
  --output text)

echo "Tipo de instancia origen: $INSTANCE_TYPE"

# --- Crear imagen AMI sin detener la instancia ---
echo "Creando imagen AMI de la instancia origen..."
AMI_NAME="copia-${INSTANCIA_ORIGEN}-$(date +%Y%m%d%H%M%S)"
AMI_ID=$(aws ec2 create-image \
  --instance-id "$INSTANCIA_ORIGEN" \
  --region "$REGION_ORIGEN" \
  --name "$AMI_NAME" \
  --no-reboot \
  --query "ImageId" \
  --output text)

echo "Imagen creada con ID: $AMI_ID"

# --- Esperar a que la imagen esté disponible ---
echo "Esperando a que la imagen esté disponible..."
aws ec2 wait image-available --image-ids "$AMI_ID" --region "$REGION_ORIGEN"
echo "Imagen disponible."

# --- Copiar la imagen a la región destino ---
echo "Copiando la imagen a la región destino ($REGION_DESTINO)..."
AMI_DEST_ID=$(aws ec2 copy-image \
  --source-region "$REGION_ORIGEN" \
  --source-image-id "$AMI_ID" \
  --region "$REGION_DESTINO" \
  --name "${AMI_NAME}-copy" \
  --query "ImageId" \
  --output text)

echo "Imagen copiada con ID: $AMI_DEST_ID"

# --- Esperar a que la imagen copiada esté disponible ---
echo "Esperando a que la imagen copiada esté disponible..."
aws ec2 wait image-available --image-ids "$AMI_DEST_ID" --region "$REGION_DESTINO"
echo "Imagen copiada disponible en $REGION_DESTINO."

# --- Crear un nuevo par de claves en la región destino ---
KEY_NAME="key-${REGION_DESTINO}-$(date +%Y%m%d%H%M%S)"
KEY_FILE="${KEY_NAME}.pem"

echo "Creando un nuevo par de claves ($KEY_NAME)..."
aws ec2 create-key-pair \
  --key-name "$KEY_NAME" \
  --region "$REGION_DESTINO" \
  --query "KeyMaterial" \
  --output text > "$KEY_FILE"

chmod 400 "$KEY_FILE"
echo "Clave guardada en: $KEY_FILE"

# --- Obtener recursos por defecto (VPC, subred y grupo de seguridad) ---
echo "Obteniendo VPC, subred y grupo de seguridad por defecto..."
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=isDefault,Values=true" \
  --region "$REGION_DESTINO" \
  --query "Vpcs[0].VpcId" \
  --output text)

SUBNET_ID=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=default-for-az,Values=true" \
  --region "$REGION_DESTINO" \
  --query "Subnets[0].SubnetId" \
  --output text)

SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" \
  --region "$REGION_DESTINO" \
  --query "SecurityGroups[0].GroupId" \
  --output text)

# --- Lanzar nueva instancia con el mismo tipo que la original ---
echo "Lanzando nueva instancia en $REGION_DESTINO con tipo $INSTANCE_TYPE..."
INSTANCE_NEW=$(aws ec2 run-instances \
  --image-id "$AMI_DEST_ID" \
  --instance-type "$INSTANCE_TYPE" \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --subnet-id "$SUBNET_ID" \
  --region "$REGION_DESTINO" \
  --query "Instances[0].InstanceId" \
  --output text)

echo "Nueva instancia lanzada: $INSTANCE_NEW"

# --- Limpiar AMIs ---
echo "Eliminando imágenes creadas..."
aws ec2 deregister-image --image-id "$AMI_ID" --region "$REGION_ORIGEN"
aws ec2 deregister-image --image-id "$AMI_DEST_ID" --region "$REGION_DESTINO"
echo "Imágenes eliminadas."

echo "Proceso completado con éxito."
