# 🏗️ Terraform AWS Infrastructure

Plantilla de infraestructura AWS desplegada con Terraform. Crea una VPC completa con subred, grupo de seguridad y una instancia EC2 pública.

## ☁️ Proveedor

| Proveedor | Región |
|-----------|--------|
| AWS       | us-east-1 |

## 📦 Recursos desplegados

### 1. VPC — `aws_vpc.mi_vpc`
- **CIDR:** `10.0.0.0/16`
- **Nombre:** `tf-mi-vpc`

### 2. Subred — `aws_subnet.mi_subnet`
- **CIDR:** `10.0.0.0/24`
- **Zona de disponibilidad:** `us-east-1a`
- **Nombre:** `tf-mi_subred`

### 3. Grupo de Seguridad — `aws_security_group.gs_migrupo`
- **Nombre:** `mi_gs`
- **Regla de entrada:** Puerto `80` (HTTP) abierto desde `0.0.0.0/0`

### 4. Instancia EC2 — `aws_instance.example`
- **AMI:** `ami-0ed094fb1304fd857` (us-east-1)
- **Tipo:** `t3.micro`
- **Key pair:** `vockey`
- **IP pública:** Sí
- **Nombre:** `EC2Instance`

## 🗂️ Estructura del proyecto

```
terraform/
└── plantila.tf   # Definición principal de la infraestructura
```

## 🚀 Uso

### Requisitos previos
- [Terraform](https://www.terraform.io/downloads) instalado
- AWS CLI configurado con credenciales válidas
- Key pair `vockey` creado en AWS

### Despliegue

```bash
# Inicializar Terraform
terraform init

# Ver los cambios que se aplicarán
terraform plan

# Aplicar la infraestructura
terraform apply

# Destruir la infraestructura cuando no se necesite
terraform destroy
```

## 🔐 Notas de seguridad

> ⚠️ El grupo de seguridad tiene el puerto 80 abierto al mundo (`0.0.0.0/0`). Para entornos de producción, se recomienda restringir el acceso a IPs específicas.

## 👤 Autor

**lucasmolpe03-stack**