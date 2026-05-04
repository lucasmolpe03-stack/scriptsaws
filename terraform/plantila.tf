#region y proveedor que uso

provider "aws" {
    region = "us-east-1"
}

# crear VPC
resource "aws_vpc" "mi_vpc" {
    cidr_block = "10.0.0.0/16"
    tags = {
        Name = "tf-mi-vpc"
    }
}

# creamos la subred
resource "aws_subnet" "mi_subnet" {
    vpc_id              = aws_vpc.mi_vpc.id
    cidr_block          = "10.0.0.0/24"
    availability_zone   = "us-east-1a"
    tags = {
        Name = "tf-mi_subred"
    }
}

# creacion del grupo de seguridad
resource "aws_security_group" "gs_migrupo" {
    name = "mi_gs"
    vpc_id = aws_vpc.mi_vpc.id

    ingress {
        cidr_blocks = ["0.0.0.0/0"]
        description = "Acceso el puerto 80 desde el exterior"
        from_port = 80
        to_port = 80
        protocol = "tcp"
    }
}

# crear una ec2
resource "aws_instance" "example" {
  ami           = "ami-0ed094fb1304fd857" # us_east-1
  instance_type = "t3.micro"
  key_name      = "vockey"
  subnet_id     = aws_subnet.mi_subnet.id # asignar la subred
  associate_public_ip_address = true
  vpc_security_group_ids = [aws_security_group.gs_migrupo.id]

  tags = {
    Name = "EC2Instance"
  }
}