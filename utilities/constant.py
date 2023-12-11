import os
from dotenv import load_dotenv


TEST_ENV = 'test'
HYPHEN_JOINED_DATE_FORMAT = '%Y-%m-%d'
HYPHEN_JOINED_DATE_REGEX = r'\d{4}-\d{2}-\d{2}'
DEFAULT_TZ='Asia/Shanghai'


load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))