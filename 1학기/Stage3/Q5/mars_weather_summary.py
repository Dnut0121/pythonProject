import csv
import mysql.connector
from datetime import datetime

class MySQLHelper:
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor()

    def create_table(self):
        create_query = '''
        CREATE TABLE IF NOT EXISTS mars_weather (
            weather_id INT AUTO_INCREMENT PRIMARY KEY,
            mars_date DATETIME NOT NULL,
            temp INT,
            storm INT
        );
        '''
        self.cursor.execute(create_query)
        self.conn.commit()

    def insert_weather_data(self, mars_date, temp, storm):
        insert_query = '''
        INSERT INTO mars_weather (mars_date, temp, storm)
        VALUES (%s, %s, %s);
        '''
        self.cursor.execute(insert_query, (mars_date, temp, storm))

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()

def read_csv_and_insert_to_db(file_path, db_helper):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            mars_date = datetime.strptime(row['mars_date'], '%Y-%m-%d')
            temp = float(row['temp']) if row['temp'] else None
            storm_val = row.get('storm') or row.get('stom')
            storm = int(storm_val) if storm_val else None
            db_helper.insert_weather_data(mars_date, temp, storm)

    db_helper.commit()


if __name__ == "__main__":
    db = MySQLHelper(
        host='localhost',
        user='root',
        password='1234',
        database='codyssey'
    )

    db.create_table()
    read_csv_and_insert_to_db('mars_weathers_data.csv', db)
    db.close()
