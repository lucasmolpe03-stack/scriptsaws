# aqui subimos el entorno al s3 que hemos creado
aws s3 cp plogin.zip s3://mibluegreen/plogin.zip

# aqui subimos la version 2 a la aplicacion
aws elasticbeanstalk create-application-version \
    --application-name phpapp \
    --version-label v2 \
    --source-bundle S3Bucket=mibluegreen,S3Key=plogin.zip

# aqui camiamos la version 1 por la version 2
aws elasticbeanstalk update-environment \
    --environment-name blue-env \
    --version-label v2