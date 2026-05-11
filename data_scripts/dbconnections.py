import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_db_handle(database="shiksha", mysqldb=5):
    if mysqldb == 5:
        return mysql.connector.connect(
            host=os.environ["DB5_HOST"],
            user=os.environ["DB5_USER"],
            passwd=os.environ["DB5_PASSWORD"],
            port=int(os.environ.get("DB5_PORT", 3306)),
            database=database,
            use_pure=True,
            raise_on_warnings=True,
        )
    elif mysqldb == 8:
        return mysql.connector.connect(
            host=os.environ["DB8_HOST"],
            user=os.environ["DB8_USER"],
            passwd=os.environ["DB8_PASSWORD"],
            port=int(os.environ.get("DB8_PORT", 3310)),
            database=database,
            use_pure=True,
            raise_on_warnings=True,
        )
