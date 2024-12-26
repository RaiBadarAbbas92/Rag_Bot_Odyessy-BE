from starlette.config import Config

# Attempt to load .env file
try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

# Retrieve configuration values from the environment or .env file
DATABASE_URL = config("DATABASE_URL", cast=str)
JWT_SECRET_KEY = config("JWT_SECRET_KEY", cast=str)
ALGORITHM = config("ALGORITHM", cast=str, default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=30)
