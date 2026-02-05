#!/bin/bash

# Script para crear una instancia RDS MySQL con acceso público
# Configuración de variables

DB_INSTANCE_IDENTIFIER="mysql-rds-instance"
DB_ENGINE="mysql"
DB_ENGINE_VERSION="8.4.7"  # Última versión estable de MySQL 8.0
DB_INSTANCE_CLASS="db.t3.micro"  # Tipo de instancia (Free tier eligible)
ALLOCATED_STORAGE="20"  # GB de almacenamiento
DB_NAME="mydatabase"
MASTER_USERNAME="admin"
MASTER_PASSWORD="adminadmin"  # Cambiar por una contraseña segura
VPC_SECURITY_GROUP_IDS=""  # Se puede especificar un security group existente
DB_SUBNET_GROUP_NAME=""  # Se puede especificar un subnet group existente
PUBLICLY_ACCESSIBLE="true"
BACKUP_RETENTION_PERIOD="7"
MULTI_AZ="false"
STORAGE_TYPE="gp3"  # General Purpose SSD (gp3)
STORAGE_ENCRYPTED="true"

echo "=========================================="
echo "Creando instancia RDS MySQL"
echo "=========================================="
echo "Identificador: $DB_INSTANCE_IDENTIFIER"
echo "Motor: $DB_ENGINE $DB_ENGINE_VERSION"
echo "Clase de instancia: $DB_INSTANCE_CLASS"
echo "Almacenamiento: ${ALLOCATED_STORAGE}GB"
echo "Acceso público: $PUBLICLY_ACCESSIBLE"
echo "=========================================="

# Crear la instancia RDS
aws rds create-db-instance \
    --db-instance-identifier "$DB_INSTANCE_IDENTIFIER" \
    --db-instance-class "$DB_INSTANCE_CLASS" \
    --engine "$DB_ENGINE" \
    --engine-version "$DB_ENGINE_VERSION" \
    --master-username "$MASTER_USERNAME" \
    --master-user-password "$MASTER_PASSWORD" \
    --allocated-storage "$ALLOCATED_STORAGE" \
    --storage-type "$STORAGE_TYPE" \
    --storage-encrypted \
    --publicly-accessible \
    --backup-retention-period "$BACKUP_RETENTION_PERIOD" \
    --no-multi-az \
    --db-name "$DB_NAME" \
    --tags Key=Name,Value="MySQL-RDS-Instance" Key=Environment,Value="Development"

# Verificar el resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Instancia RDS creada exitosamente"
    echo "=========================================="
    echo ""
    echo "La instancia está siendo creada. Esto puede tardar varios minutos."
    echo ""
    echo "Para verificar el estado, ejecuta:"
    echo "aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_IDENTIFIER --query 'DBInstances[0].DBInstanceStatus'"
    echo ""
    echo "Para obtener el endpoint de conexión una vez disponible:"
    echo "aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_IDENTIFIER --query 'DBInstances[0].Endpoint.Address' --output text"
    echo ""
    echo "=========================================="
    echo "IMPORTANTE: Configuración de seguridad"
    echo "=========================================="
    echo "1. Asegúrate de configurar el Security Group para permitir conexiones en el puerto 3306"
    echo "2. Comando para modificar el security group:"
    echo "   aws ec2 authorize-security-group-ingress --group-id <SG_ID> --protocol tcp --port 3306 --cidr 0.0.0.0/0"
    echo ""
    echo "3. Para conectarte a la base de datos:"
    echo "   mysql -h <ENDPOINT> -P 3306 -u $MASTER_USERNAME -p"
    echo "=========================================="
else
    echo ""
    echo "✗ Error al crear la instancia RDS"
    echo "Verifica los logs para más detalles"
    exit 1
fi