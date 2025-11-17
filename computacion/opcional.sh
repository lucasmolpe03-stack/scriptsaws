

# --- Validación de parámetros ---
if [ $# -ne 1 ]; then
  echo "Uso: $0 <id_instancia_origen>"
  exit 1
fi

INSTANCIA_ORIGEN=$1

# --- Aviso previo ---
echo "⚠️  Atención: este proceso DETENDRÁ la instancia '$INSTANCIA_ORIGEN'."
read -p "¿Desea continuar? (s/n): " CONFIRMAR
if [[ "$CONFIRMAR" != "s" && "$CONFIRMAR" != "S" ]]; then
  echo "Proceso abortado por el usuario."
  exit 0
fi

# --- Comprobación de la instancia origen ---
echo "Comprobando si la instancia $INSTANCIA_ORIGEN existe ..."
EXISTE=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCIA_ORIGEN" \
  --query "Reservations[*].Instances[*].InstanceId" \
  --output text 2>/dev/null)

INSTANCE_TYPE=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCIA_ORIGEN" \
  --query "Reservations[0].Instances[0].InstanceType" \
  --output text)

echo "Tipo de instancia origen: $INSTANCE_TYPE"

if [ -z "$EXISTE" ]; then
  echo "Error: la instancia $INSTANCIA_ORIGEN no existe."
  exit 1
fi
echo "Instancia encontrada."

echo "viendo si la instancia $INSTANCIA_ORIGEN esta encendida ..."
ENCENDIDA=$(aws ec2 describe-instances \
    --instance-ids $INSTANCIA_ORIGEN \
    --query "Reservations[*].Instances[*].[State.Name]" \
    --output text 2>/dev/null)


if [ "$ENCENDIDA" == "running" ]; then
  echo "Instancia $INSTANCIA_ORIGEN está en ejecución. Deteniendo..."
  aws ec2 stop-instances \
    --instance-ids $INSTANCIA_ORIGEN \
    --query "StoppingInstances[*].[CurrentState.Name]" \
    --output text
  aws ec2 wait instance-stopped \
    --instance-ids $INSTANCIA_ORIGEN
  echo "La instancia esta detenida"
else
  echo "Instancia $INSTANCIA_ORIGEN no está en ejecución (estado: $ENCENDIDA)."
fi

aws ec2 modify-instance-attribute \
    --instance-id $INSTANCIA_ORIGEN \
    --instance-type "{\"Value\": \"t3.micro\"}"
echo "Instancia cambiada."

aws ec2 start-instances \
    --instance-ids $INSTANCIA_ORIGEN \
    --query "StartingInstances[*].[CurrentState.Name]" \
    --output text
echo "la instancia se esta encendiendo ..."
aws ec2 wait instance-running \
    --instance-ids $INSTANCIA_ORIGEN
echo "la instancia esta encendida"

INSTANCE_TYPE=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCIA_ORIGEN" \
  --query "Reservations[0].Instances[0].InstanceType" \
  --output text)

echo "Tipo de instancia origen: $INSTANCE_TYPE"

