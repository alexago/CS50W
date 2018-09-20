import sqlalchemy
import os

file = open("database.sql")
engine = sqlalchemy.create_engine(os.getenv("DATABASE_URL"))
escaped_sql = sqlalchemy.text(file.read())
engine.execute(escaped_sql)