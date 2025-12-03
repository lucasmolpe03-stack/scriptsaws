# Versiones del Script de Infraestructura AWS con Boto3

Este directorio contiene diferentes versiones incrementales del script para crear infraestructura AWS usando boto3.

## 📋 Descripción de las Versiones

### **Versión 1: `version1_crear_vpc.py`**
**Componentes:**
- ✅ VPC con CIDR 192.168.0.0/24
- ✅ DNS habilitado

**Comando de ejecución:**
```bash
py version1_crear_vpc.py
```

**Commit sugerido:**
```bash
git add version1_crear_vpc.py
git commit -m "feat: crear VPC con DNS habilitado usando boto3"
```

---

### **Versión 2: `version2_crear_vpc_subnet.py`**
**Componentes:**
- ✅ VPC con CIDR 192.168.0.0/24
- ✅ DNS habilitado
- ✅ Subnet con CIDR 192.168.0.0/28
- ✅ IP pública automática en subnet

**Comando de ejecución:**
```bash
py version2_crear_vpc_subnet.py
```

**Commit sugerido:**
```bash
git add version2_crear_vpc_subnet.py
git commit -m "feat: agregar creación de subnet con IP pública automática"
```

---

### **Versión 3: `version3_crear_vpc_subnet_igw.py`**
**Componentes:**
- ✅ VPC con CIDR 192.168.0.0/24
- ✅ DNS habilitado
- ✅ Subnet con CIDR 192.168.0.0/28
- ✅ IP pública automática en subnet
- ✅ Internet Gateway
- ✅ IGW adjuntado a VPC

**Comando de ejecución:**
```bash
py version3_crear_vpc_subnet_igw.py
```

**Commit sugerido:**
```bash
git add version3_crear_vpc_subnet_igw.py
git commit -m "feat: agregar Internet Gateway y adjuntarlo a la VPC"
```

---

### **Versión 4: `version4_crear_vpc_subnet_igw_routetable.py`**
**Componentes:**
- ✅ VPC con CIDR 192.168.0.0/24
- ✅ DNS habilitado
- ✅ Subnet con CIDR 192.168.0.0/28
- ✅ IP pública automática en subnet
- ✅ Internet Gateway
- ✅ IGW adjuntado a VPC
- ✅ Route Table
- ✅ Ruta hacia Internet (0.0.0.0/0)
- ✅ Route Table asociada a Subnet

**Comando de ejecución:**
```bash
py version4_crear_vpc_subnet_igw_routetable.py
```

**Commit sugerido:**
```bash
git add version4_crear_vpc_subnet_igw_routetable.py
git commit -m "feat: agregar Route Table con ruta a Internet y asociación a subnet"
```

---

### **Versión 5: `version5_crear_vpc_subnet_igw_routetable_sg.py`**
**Componentes:**
- ✅ VPC con CIDR 192.168.0.0/24
- ✅ DNS habilitado
- ✅ Subnet con CIDR 192.168.0.0/28
- ✅ IP pública automática en subnet
- ✅ Internet Gateway
- ✅ IGW adjuntado a VPC
- ✅ Route Table
- ✅ Ruta hacia Internet (0.0.0.0/0)
- ✅ Route Table asociada a Subnet
- ✅ Security Group
- ✅ Regla SSH (puerto 22)
- ✅ Regla ICMP (ping)

**Comando de ejecución:**
```bash
py version5_crear_vpc_subnet_igw_routetable_sg.py
```

**Commit sugerido:**
```bash
git add version5_crear_vpc_subnet_igw_routetable_sg.py
git commit -m "feat: agregar Security Group con reglas SSH e ICMP"
```

---

### **Versión 6: `version6_completo_con_ec2.py`** ⭐ (COMPLETO)
**Componentes:**
- ✅ VPC con CIDR 192.168.0.0/24
- ✅ DNS habilitado
- ✅ Subnet con CIDR 192.168.0.0/28
- ✅ IP pública automática en subnet
- ✅ Internet Gateway
- ✅ IGW adjuntado a VPC
- ✅ Route Table
- ✅ Ruta hacia Internet (0.0.0.0/0)
- ✅ Route Table asociada a Subnet
- ✅ Security Group
- ✅ Regla SSH (puerto 22)
- ✅ Regla ICMP (ping)
- ✅ Instancia EC2 (t2.micro)

**Comando de ejecución:**
```bash
py version6_completo_con_ec2.py
```

**Commit sugerido:**
```bash
git add version6_completo_con_ec2.py
git commit -m "feat: agregar creación de instancia EC2 - infraestructura completa"
```

---

## 🚀 Flujo de Trabajo con Git

### Opción 1: Commits individuales por versión
```bash
# Versión 1
git add version1_crear_vpc.py
git commit -m "feat: crear VPC con DNS habilitado usando boto3"
git push

# Versión 2
git add version2_crear_vpc_subnet.py
git commit -m "feat: agregar creación de subnet con IP pública automática"
git push

# Versión 3
git add version3_crear_vpc_subnet_igw.py
git commit -m "feat: agregar Internet Gateway y adjuntarlo a la VPC"
git push

# Versión 4
git add version4_crear_vpc_subnet_igw_routetable.py
git commit -m "feat: agregar Route Table con ruta a Internet y asociación a subnet"
git push

# Versión 5
git add version5_crear_vpc_subnet_igw_routetable_sg.py
git commit -m "feat: agregar Security Group con reglas SSH e ICMP"
git push

# Versión 6
git add version6_completo_con_ec2.py
git commit -m "feat: agregar creación de instancia EC2 - infraestructura completa"
git push

# README
git add README_VERSIONES.md
git commit -m "docs: agregar documentación de versiones del script"
git push
```

### Opción 2: Un solo commit con todas las versiones
```bash
git add version*.py README_VERSIONES.md
git commit -m "feat: agregar versiones incrementales del script de infraestructura AWS con boto3"
git push
```

---

## 📝 Requisitos

### Instalación de boto3
```bash
py -m pip install boto3
```

### Configuración de credenciales AWS
```bash
aws configure
```

O configurar variables de entorno:
```powershell
$env:AWS_ACCESS_KEY_ID="tu_access_key"
$env:AWS_SECRET_ACCESS_KEY="tu_secret_key"
$env:AWS_DEFAULT_REGION="us-east-1"
```

---

## ⚠️ Notas Importantes

1. **Key Pair**: Todas las versiones que crean EC2 usan `vockey` como key pair. Asegúrate de que existe en tu cuenta AWS.

2. **AMI ID**: La AMI `ami-0360c520857e3138f` debe estar disponible en tu región.

3. **Security Group Name**: El nombre `gsmio` debe ser único. Si ya existe, cambia el nombre en el script.

4. **Costos**: Recuerda que crear recursos en AWS puede generar costos. Elimina los recursos cuando no los necesites.

---

## 🧹 Limpieza de Recursos

Para eliminar los recursos creados, puedes usar la consola de AWS o crear un script de limpieza.

**Orden de eliminación:**
1. Terminar instancia EC2
2. Eliminar Security Group
3. Desasociar Route Table de Subnet
4. Eliminar Route Table
5. Desadjuntar Internet Gateway de VPC
6. Eliminar Internet Gateway
7. Eliminar Subnet
8. Eliminar VPC

---

## 📚 Recursos Adicionales

- [Documentación oficial de Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Boto3 EC2 Examples](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/ec2-examples.html)
