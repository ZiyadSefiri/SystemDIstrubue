from sqlalchemy import create_engine, text

user = "dev"
password = ""
host = "localhost"
port = 3306
database = "car_service"

def connect_database() :
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

    print("Connection URL:", url)  # Debug: make sure it's correct

    try:
        engine = create_engine(url)
    except Exception as e:
        print("Failed to create engine:", e)
        raise
    return engine

