from dotenv import load_dotenv
from pathlib import Path
import os
import pymongo

load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

mongodb_link = os.environ["MONGODB"]

myclient = pymongo.MongoClient(mongodb_link)
Collection = myclient["MIREA"]["Users"]