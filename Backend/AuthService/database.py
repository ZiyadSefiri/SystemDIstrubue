from sqlalchemy import create_engine, text

user = "root"
password = "craftisher159753"
host = "localhost"
port = 3306
database = "authdb"

url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

print("Connection URL:", url)  # Debug: make sure it's correct

engine = create_engine(url)

try:
    with engine.connect() as conn:
        print("✅ Connected successfully to:", conn.execute(text("SELECT DATABASE();")).scalar())
except Exception as e:
    print("❌ Error while connecting to MySQL:", e)
