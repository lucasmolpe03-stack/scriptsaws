# aqui creo un baquet s3
aws s3 mb s3://mibluegreen

# aqui subo el archivo del entorno blue
aws s3 cp index2.zip s3://mibluegreen/index2.zip

# aqui creo la aplicacion
aws elasticbeanstalk create-application \
    --application-name phpapp \
    --description "Aplicación PHP con index.html"

# aqui subo la version uno de la aplicacion con el entorno blue del s3
aws elasticbeanstalk create-application-version \
    --application-name phpapp \
    --version-label v1 \
    --source-bundle S3Bucket=mibluegreen,S3Key=index2.zip

# y aqui creo el entorno y le pongo la aplicacion que hemos creado
aws elasticbeanstalk create-environment \
  --application-name phpapp \
  --environment-name blue-env \
  --version-label v1 \
  --solution-stack-name "64bit Amazon Linux 2023 V4.7.8 running PHP 8.4" \
  --option-settings \
  Namespace=aws:autoscaling:launchconfiguration,OptionName=IamInstanceProfile,Value=LabInstanceProfile \
  Namespace=aws:elasticbeanstalk:environment,OptionName=ServiceRole,Value=LabRole \
  Namespace=aws:autoscaling:launchconfiguration,OptionName=EC2KeyName,Value=vockey