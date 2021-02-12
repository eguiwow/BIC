
try:
	from boto.s3.connection import S3Connection
	from botocore.exceptions import ClientError
	from boto.s3.key import Key
except ModuleNotFoundError:
	print ('Boto not available, skipping')
	pass

import time
import os
from os.path import join, abspath, dirname
from traceback import print_exc

class S3handler:
	"""
	Class that uploads or downloads files to s3 bucket
	"""

	def __init__(self, verbose = True):
		try:
			S3_ID = os.environ['S3_ID']
			S3_SECRET = os.environ['S3_SECRET']
			S3_BUCKET = os.environ['S3_BUCKET']
		except KeyError:
			print ('Environment not previously loaded, trying local .env')
			try:
			
			    with open(join(dirname(__file__), '.env'), 'r') as file:
			        S3_ID = file.readline().strip('\r\n').split('=')[1]
			        S3_SECRET = file.readline().strip('\r\n').split('=')[1]
			        S3_BUCKET = file.readline().strip('\r\n').split('=')[1]
			    print ('Loaded local file')

			except FileNotFoundError:
				print_exc()
				pass
				return None

		else:
			print ('Loaded environment keys')

		self.conn = S3Connection(S3_ID, S3_SECRET, is_secure = False)
		self.bucket = self.conn.get_bucket(S3_BUCKET)
		self.verbose = verbose

	def std_out(self, msg, type_message = None, force = False):
		if self.verbose or force: 
			if type_message is None: print(msg)	
			elif type_message == 'SUCCESS': print(f'[SUCCESS] {msg}')
			elif type_message == 'WARNING': print(f'[WARNING] {msg}') 
			elif type_message == 'ERROR': print(f'[ERROR] {msg}')

	def get_objects(self):
		objects = self.bucket.list()
		
		object_names = [obj.name for obj in objects]
		if object_names is not None:
			self.std_out(f'Successfully got keys in bucket {self.bucket.name}', 'SUCCESS')
			return object_names
		else:
			self.std_out(f'No keys in bucket {self.bucket}', 'ERROR')			
			return None

	def download(self, filename, s3filename = ''):

		if s3filename == '': s3filename = os.path.basename(filename)
		self.std_out(f'Target file name for download: {s3filename}')
		
		key_dest = Key(self.bucket, s3filename)
		key_dest.get_contents_to_filename(filename)

		self.std_out(f'Downloaded files to {filename}')

	def upload(self, filename, s3filename = '', expiration = 1296000):
		if s3filename == '': s3filename = os.path.basename(filename)
		self.std_out(f'Target file name for upload: {s3filename}')

		key_dest = Key(self.bucket, s3filename)
		key_dest.set_contents_from_filename(filename)
		response = self.conn.generate_url(expires_in= expiration, method='GET',
											bucket=self.bucket.name, key=s3filename)

		# The response contains the presigned URL
		self.std_out(f'Uploaded files from {filename} to {s3filename}', 'SUCCESS')
		self.std_out(f'URL {response}')

		return response

	def delete_key(self, s3filename):

		if s3filename == '': s3filename = os.path.basename(s3filename)

		if s3filename in self.get_objects():
			key_dest = Key(self.bucket, s3filename)
			self.bucket.delete_key(key_dest)
			self.std_out(f'Deleted key {key_dest} from {self.bucket.name}', 'SUCCESS')
		else:
			self.std_out('File not in bucket', 'ERROR')