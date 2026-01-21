# Explicación Detallada: plantilla_final.py

## Índice
1. [Estructura General](#estructura-general)
2. [Configuración](#configuración)
3. [Funciones por Región](#funciones-por-región)
4. [Conectividad](#conectividad)
5. [Flujo de Ejecución](#flujo-de-ejecución)

---

## Estructura General

El script está organizado en secciones claramente definidas:

```python
#!/usr/bin/env python3
import boto3  # SDK de AWS para Python
import time   # Para esperas (sleep)
import sys    # Para exit codes
```

**¿Por qué Python/Boto3?**
- ✅ Más robusto que Bash para manejo de JSON
- ✅ Mejor manejo de errores
- ✅ No hay problemas con parámetros booleanos (como `--egress`)
- ✅ Código más legible y mantenible

---

## Configuración

### Constantes Globales

```python
REGION_OREGON = 'us-west-2'
REGION_VIRGINIA = 'us-east-1'
```
**Propósito:** Centralizar las regiones para fácil modificación.

### CIDRs (Rangos de IP)

```python
OREGON_VPC_CIDR = '10.0.0.0/16'           # 65,536 IPs
OREGON_PUBLIC_SUBNET_CIDR = '10.0.1.0/24'  # 256 IPs
OREGON_PRIVATE_SUBNET_CIDR = '10.0.2.0/24' # 256 IPs
```

**¿Por qué estos rangos?**
- `10.0.0.0/16` para Oregon y `10.1.0.0/16` para Virginia **no se solapan**
- Permite comunicación entre VPCs sin conflictos
- `/24` para subnets es suficiente para ~250 hosts

### AMIs (Amazon Machine Images)

```python
AMI_OREGON = 'ami-00a8151272c45cd8e'      # Amazon Linux 2023
AMI_VIRGINIA = 'ami-07ff62358b87c7116'    # Amazon Linux 2023
```

**Importante:** Las AMIs son **específicas por región**. No puedes usar la AMI de Oregon en Virginia.

### KeyPair

```python
KEY_NAME_VIRGINIA = 'vockey'
```

**Nota:** Solo Virginia usa KeyPair. Oregon crea instancias sin KeyPair como solicitaste.

---

## Funciones por Región

### `create_oregon()` - Infraestructura en Oregon

Esta función crea **todos** los recursos de Oregon en orden:

#### 1. VPC (Virtual Private Cloud)

```python
vpc = ec2.create_vpc(
    CidrBlock=OREGON_VPC_CIDR,
    TagSpecifications=[{
        'ResourceType': 'vpc',
        'Tags': [{'Key': 'Name', 'Value': 'VPC-Oregon'}]
    }]
)
```

**¿Qué hace?**
- Crea una red virtual aislada en AWS
- Habilita DNS para resolución de nombres
- El tag `Name` permite identificarla fácilmente en la consola

#### 2. Subnets (Subredes)

```python
# Subnet Pública
pub = ec2.create_subnet(
    VpcId=r['vpc_id'],
    CidrBlock=OREGON_PUBLIC_SUBNET_CIDR,
    AvailabilityZone=f'{REGION_OREGON}a'
)
ec2.modify_subnet_attribute(
    SubnetId=r['public_subnet_id'],
    MapPublicIpOnLaunch={'Value': True}  # ← Auto-asigna IP pública
)
```

**Diferencia Pública vs Privada:**
- **Pública:** Tiene ruta a Internet Gateway, auto-asigna IPs públicas
- **Privada:** Solo tiene ruta a NAT Gateway, sin IPs públicas

#### 3. Internet Gateway (IGW)

```python
igw = ec2.create_internet_gateway(...)
ec2.attach_internet_gateway(
    InternetGatewayId=r['igw_id'],
    VpcId=r['vpc_id']
)
```

**Propósito:** Permite que recursos en subnets públicas accedan a Internet.

#### 4. NAT Gateway

```python
# Primero: Elastic IP
eip = ec2.allocate_address(Domain='vpc')

# Segundo: NAT Gateway
nat = ec2.create_nat_gateway(
    SubnetId=r['public_subnet_id'],  # ← Debe estar en subnet pública
    AllocationId=r['eip_id']
)

# Tercero: Esperar disponibilidad
ec2.get_waiter('nat_gateway_available').wait(...)
```

**¿Por qué NAT Gateway?**
- Permite que instancias en subnets **privadas** accedan a Internet
- Necesario para actualizaciones, descargas, etc.
- Debe estar en subnet pública pero sirve a la privada

#### 5. Route Tables (Tablas de Enrutamiento)

**Route Table Pública:**
```python
pub_rt = ec2.create_route_table(VpcId=r['vpc_id'])
ec2.create_route(
    RouteTableId=r['public_rt_id'],
    DestinationCidrBlock='0.0.0.0/0',  # Todo el tráfico
    GatewayId=r['igw_id']               # Va al Internet Gateway
)
ec2.associate_route_table(
    RouteTableId=r['public_rt_id'],
    SubnetId=r['public_subnet_id']
)
```

**Route Table Privada:**
```python
priv_rt = ec2.create_route_table(VpcId=r['vpc_id'])
ec2.create_route(
    RouteTableId=r['private_rt_id'],
    DestinationCidrBlock='0.0.0.0/0',
    NatGatewayId=r['nat_id']  # ← Va al NAT Gateway, no al IGW
)
```

**Flujo de Tráfico:**
```
Instancia Pública → Route Table Pública → IGW → Internet
Instancia Privada → Route Table Privada → NAT Gateway → IGW → Internet
```

#### 6. Security Group (Firewall de Instancia)

```python
sg = ec2.create_security_group(...)
ec2.authorize_security_group_ingress(
    GroupId=r['sg_id'],
    IpPermissions=[
        # SSH (puerto 22)
        {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        
        # HTTP (puerto 80)
        {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        
        # HTTPS (puerto 443)
        {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        
        # ICMP (ping)
        {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        
        # Todo el tráfico desde Virginia
        {'IpProtocol': '-1', 'IpRanges': [{'CidrIp': VIRGINIA_VPC_CIDR}]}
    ]
)
```

**Security Groups son STATEFUL:**
- Si permites entrada en puerto 80, la respuesta sale automáticamente
- No necesitas regla de salida explícita para respuestas

#### 7. Network ACLs (Firewall de Subnet)

**NACL Pública - Reglas de Entrada:**
```python
# Regla 100: HTTP
ec2.create_network_acl_entry(
    NetworkAclId=r['public_nacl_id'],
    RuleNumber=100,           # Menor número = mayor prioridad
    Protocol='6',             # 6 = TCP
    RuleAction='allow',
    Egress=False,             # False = Entrada (Ingress)
    CidrBlock='0.0.0.0/0',
    PortRange={'From': 80, 'To': 80}
)

# Regla 110: HTTPS
# Regla 120: SSH
# Regla 130: Puertos efímeros (1024-65535)
# Regla 140: ICMP
```

**NACL Pública - Reglas de Salida:**
```python
ec2.create_network_acl_entry(
    NetworkAclId=r['public_nacl_id'],
    RuleNumber=100,
    Protocol='-1',    # -1 = Todos los protocolos
    RuleAction='allow',
    Egress=True,      # True = Salida (Egress)
    CidrBlock='0.0.0.0/0'
)
```

**NACLs son STATELESS:**
- Debes configurar entrada **Y** salida explícitamente
- Por eso permitimos puertos efímeros (1024-65535) en entrada
- Las respuestas HTTP usan puertos efímeros

**Asociación de NACL:**
```python
# Obtener la asociación actual
assocs = ec2.describe_network_acls(
    Filters=[{'Name': 'association.subnet-id', 
              'Values': [r['public_subnet_id']]}]
)

# Reemplazar con nuestra NACL
ec2.replace_network_acl_association(
    AssociationId=assocs['NetworkAcls'][0]['Associations'][0]['NetworkAclAssociationId'],
    NetworkAclId=r['public_nacl_id']
)
```

#### 8. Instancias EC2

**Instancia Pública (SIN KeyPair):**
```python
pub_inst = ec2.run_instances(
    ImageId=AMI_OREGON,
    InstanceType='t2.micro',
    MinCount=1, MaxCount=1,
    # NO hay KeyName aquí ← Diferencia clave
    NetworkInterfaces=[{
        'DeviceIndex': 0,
        'SubnetId': r['public_subnet_id'],
        'Groups': [r['sg_id']],
        'AssociatePublicIpAddress': True  # ← Obtiene IP pública
    }]
)
```

**Instancia Privada (SIN KeyPair):**
```python
priv_inst = ec2.run_instances(
    ImageId=AMI_OREGON,
    InstanceType='t2.micro',
    MinCount=1, MaxCount=1,
    NetworkInterfaces=[{
        'DeviceIndex': 0,
        'SubnetId': r['private_subnet_id'],
        'Groups': [r['sg_id']],
        'AssociatePublicIpAddress': False  # ← Sin IP pública
    }]
)
```

### `create_virginia()` - Infraestructura en Virginia

**Diferencias con Oregon:**

1. **Región diferente:** `us-east-1`
2. **CIDRs diferentes:** `10.1.x.x` en lugar de `10.0.x.x`
3. **AMI diferente:** Específica para Virginia
4. **KeyPair incluido:** Las instancias usan `vockey`

```python
pub_inst = ec2.run_instances(
    ImageId=AMI_VIRGINIA,
    InstanceType='t2.micro',
    KeyName=KEY_NAME_VIRGINIA,  # ← Aquí está la diferencia
    MinCount=1, MaxCount=1,
    ...
)
```

**Todo lo demás es idéntico** en estructura.

---

## Conectividad

### `create_peering()` - VPC Peering

**Paso 1: Crear solicitud desde Oregon**
```python
peer = ec2_or.create_vpc_peering_connection(
    VpcId=oregon['vpc_id'],
    PeerVpcId=virginia['vpc_id'],
    PeerRegion=REGION_VIRGINIA  # ← Peering entre regiones
)
peering_id = peer['VpcPeeringConnection']['VpcPeeringConnectionId']
```

**Paso 2: Aceptar en Virginia**
```python
time.sleep(5)  # Esperar propagación
ec2_va.accept_vpc_peering_connection(
    VpcPeeringConnectionId=peering_id
)
```

**Paso 3: Configurar rutas**
```python
# Oregon → Virginia
ec2_or.create_route(
    RouteTableId=oregon['public_rt_id'],
    DestinationCidrBlock=VIRGINIA_VPC_CIDR,  # 10.1.0.0/16
    VpcPeeringConnectionId=peering_id
)

# Virginia → Oregon
ec2_va.create_route(
    RouteTableId=virginia['public_rt_id'],
    DestinationCidrBlock=OREGON_VPC_CIDR,  # 10.0.0.0/16
    VpcPeeringConnectionId=peering_id
)
```

**Resultado:**
```
Oregon (10.0.0.0/16) ←→ VPC Peering ←→ Virginia (10.1.0.0/16)
```

Cualquier instancia en Oregon puede comunicarse con cualquier instancia en Virginia usando IPs privadas.

### `create_tgw()` - Transit Gateway

**Paso 1: Crear Transit Gateway**
```python
tgw = ec2.create_transit_gateway(
    Description='Multi-Region TGW',
    Options={
        'AmazonSideAsn': 64512,  # ASN para BGP
        'DefaultRouteTableAssociation': 'enable',
        'DefaultRouteTablePropagation': 'enable',
        'DnsSupport': 'enable',
        'VpnEcmpSupport': 'enable'
    }
)
```

**Paso 2: Esperar disponibilidad (Polling Manual)**
```python
for _ in range(60):  # Máximo 10 minutos
    resp = ec2.describe_transit_gateways(TransitGatewayIds=[tgw_id])
    state = resp['TransitGateways'][0]['State']
    if state == 'available':
        break
    time.sleep(10)
```

**¿Por qué polling manual?**
- El waiter `transit_gateway_available` no existe en boto3
- Solución: Verificar el estado cada 10 segundos

**Paso 3: Crear VPC Attachment**
```python
att = ec2.create_transit_gateway_vpc_attachment(
    TransitGatewayId=tgw_id,
    VpcId=oregon['vpc_id'],
    SubnetIds=[oregon['private_subnet_id']],  # ← Usa subnet privada
)
```

**Paso 4: Esperar attachment**
```python
for _ in range(60):  # Máximo 5 minutos
    resp = ec2.describe_transit_gateway_vpc_attachments(
        TransitGatewayAttachmentIds=[att_id]
    )
    state = resp['TransitGatewayVpcAttachments'][0]['State']
    if state == 'available':
        break
    time.sleep(5)
```

**¿Para qué sirve el TGW?**
- Hub central para conectar múltiples VPCs
- Escalable: Puedes agregar más VPCs fácilmente
- En este script, está configurado pero no se usan rutas TGW (usamos VPC Peering)
- Listo para expansión futura

---

## Flujo de Ejecución

### `main()` - Función Principal

```python
def main():
    try:
        # 1. Crear infraestructura Oregon
        oregon = create_oregon()
        
        # 2. Crear infraestructura Virginia
        virginia = create_virginia()
        
        # 3. Conectar con VPC Peering
        peering = create_peering(oregon, virginia)
        
        # 4. Crear Transit Gateway
        tgw = create_tgw(oregon)
        
        # 5. Mostrar resumen
        print(f"Oregon VPC:    {oregon['vpc_id']}")
        print(f"Virginia VPC:  {virginia['vpc_id']}")
        print(f"VPC Peering:   {peering}")
        print(f"Transit GW:    {tgw}")
        
        return 0  # Exit code 0 = éxito
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()  # Muestra stack trace completo
        return 1  # Exit code 1 = error
```

### Orden de Ejecución

```
1. create_oregon()
   ├─ VPC
   ├─ Subnets
   ├─ IGW
   ├─ NAT Gateway (espera ~2 min)
   ├─ Route Tables
   ├─ Security Group
   ├─ NACLs
   └─ Instancias EC2

2. create_virginia()
   └─ (mismo proceso)

3. create_peering()
   ├─ Crear solicitud
   ├─ Aceptar
   └─ Configurar rutas

4. create_tgw()
   ├─ Crear TGW (espera ~2 min)
   └─ Crear Attachment (espera ~1 min)
```

**Tiempo total aproximado:** 8-10 minutos

---

## Manejo de Errores

### Try/Catch Global

```python
try:
    # Todo el código
except Exception as e:
    print(f"❌ ERROR: {e}")
    traceback.print_exc()
    return 1
```

**Beneficios:**
- Captura cualquier error de boto3
- Muestra stack trace completo para debugging
- Retorna exit code 1 para scripts automatizados

### Waiters

```python
# Para NAT Gateway (waiter disponible)
ec2.get_waiter('nat_gateway_available').wait(
    NatGatewayIds=[r['nat_id']]
)

# Para TGW (polling manual)
for _ in range(60):
    resp = ec2.describe_transit_gateways(...)
    if state == 'available':
        break
    time.sleep(10)
```

---

## Diccionario de Retorno

Cada función retorna un diccionario con todos los IDs:

```python
return {
    'vpc_id': 'vpc-xxxxx',
    'public_subnet_id': 'subnet-xxxxx',
    'private_subnet_id': 'subnet-xxxxx',
    'igw_id': 'igw-xxxxx',
    'nat_id': 'nat-xxxxx',
    'public_rt_id': 'rtb-xxxxx',
    'private_rt_id': 'rtb-xxxxx',
    'sg_id': 'sg-xxxxx',
    'public_instance_id': 'i-xxxxx',
    'private_instance_id': 'i-xxxxx'
}
```

**¿Por qué?**
- Permite pasar IDs entre funciones
- Necesario para VPC Peering (necesita IDs de ambas regiones)
- Facilita debugging (puedes ver todos los IDs creados)

---

## Conceptos Clave

### Stateful vs Stateless

**Security Groups (Stateful):**
```
Entrada: HTTP (80) → Permitido
Salida: Respuesta HTTP → Permitido automáticamente ✓
```

**NACLs (Stateless):**
```
Entrada: HTTP (80) → Permitido
Salida: Respuesta HTTP → Debes permitir puertos efímeros (1024-65535) ✓
```

### Públic vs Privado

**Subnet Pública:**
- Tiene ruta a IGW
- Auto-asigna IPs públicas
- Instancias accesibles desde Internet

**Subnet Privada:**
- Solo ruta a NAT Gateway
- Sin IPs públicas
- Instancias NO accesibles desde Internet
- Pueden salir a Internet vía NAT

### VPC Peering vs Transit Gateway

**VPC Peering:**
- Conexión 1-a-1 entre VPCs
- Bajo costo
- Ideal para pocas VPCs

**Transit Gateway:**
- Hub central (1-a-muchos)
- Mayor costo
- Ideal para muchas VPCs
- Escalable

---

## Resumen de Protocolos

| Protocolo | Número | Uso |
|-----------|--------|-----|
| TCP | 6 | HTTP, HTTPS, SSH |
| ICMP | 1 | Ping |
| Todos | -1 | Cualquier protocolo |

## Resumen de Puertos

| Puerto | Servicio |
|--------|----------|
| 22 | SSH |
| 80 | HTTP |
| 443 | HTTPS |
| 1024-65535 | Puertos efímeros (respuestas) |

---

## Ejecución

```bash
# Ejecutar script
py plantilla_final.py

# Limpiar recursos
bash eliminar_plantilla.sh
```

**Exit Codes:**
- `0` = Éxito
- `1` = Error
