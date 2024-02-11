from dotenv import load_dotenv
from pathlib import Path
import os
import pymongo
import datetime

load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

mongodb_link = os.environ["MONGODB"]
startweek = datetime.date(2023, 2, 9).isocalendar()[1]

myclient = pymongo.MongoClient(mongodb_link)
Collection = myclient["MIREA"]["Users"]
