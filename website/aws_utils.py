import boto3
import logging
import botocore

class FileManagementUtils():
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'docx'}
    CONTENT_TYPES = {'txt':'text/plain',
                     'pdf':'application/pdf',
                     'png':'image/png',
                     'docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}


    def __init__(self
                 ,bucket_name
                 ,region_name
                 ,aws_access_key_id
                 ,aws_secret_access_key
                 ,service_name = 's3') -> None:
        
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.service_name = service_name

        self.session = boto3.session.Session(
            aws_access_key_id= aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name = self.region_name
        )



    def upload_file(self, file, file_name, file_extension):

        boto3_obj =  self.session.resource(self.service_name)
        try:
            boto3_obj.Bucket(self.bucket_name).upload_fileobj(file, file_name, 
                                                              ExtraArgs={'ContentType':FileManagementUtils.CONTENT_TYPES.get(file_extension.lower())})

            return True
        
        except:
            return False
        
    
    def create_presigned_url(self, object_name, type = 'view', expiration = 3600):
        boto3.setup_default_session()
        # Generate a presigned URL for the S3 object
        s3 = self.session.client('s3')

        
        try:

            if type.lower() == 'view':
                response = s3.generate_presigned_url('get_object',
                                                        Params={'Bucket': self.bucket_name,
                                                                'Key': object_name,
                                                                'ResponseContentDisposition': 'inline'},
                                                        ExpiresIn=expiration)
            
            elif type.lower() == 'download':
                response = s3.generate_presigned_url(
                            'get_object',
                            Params={
                                'Bucket': self.bucket_name,
                                'Key': object_name,
                                'ResponseContentType': 'application/octet-stream',
                                'ResponseContentDisposition': 'attachment'
                            },
                            ExpiresIn=expiration
                        )
                
        except Exception as e:
            print(e)
            logging.error(e)
            return False
        
        return response
    
    def delete_obj(self, object_name):
        s3 = self.session.client('s3')

        try:
            s3.delete_object(Bucket=self.bucket_name, Key=object_name)

        except Exception as e:
            print(e)
            logging.error(e)
            return "Error"



    @classmethod
    def allowed_file(cls, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in FileManagementUtils.ALLOWED_EXTENSIONS

