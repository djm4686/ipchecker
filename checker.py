import configparser
import requests
import sqlite3
import logging
import datetime

logging.basicConfig(filename="checker.log", level=logging.INFO)

def get_ip(options):
  return requests.get(options.get("general", "ip_api")).json()["ip"]

def store_ip(current_ip, timestamp, options):
  with sqlite3.connect(options.get("sqlite", "db")) as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ips VALUES ('{}', '{}')".format(timestamp, current_ip))
    conn.commit()

def check_ip_change(current_ip, options):
  with sqlite3.connect(options.get("sqlite", "db")) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ips")
    rows = cursor.fetchall()
    if current_ip in [x[1] for x in rows]:
      log("IP hasnt changed: {}".format(current_ip))
      return False
    log("IP changed! New IP: {}".format(current_ip))
    return True

def email_new_ip(new_ip, options):
  import smtplib
  from email.mime.text import MIMEText
  sender = options.get("email", "sender_address")
  receiver = options.get("email", "receiver_address")
  server = options.get("email", "server")
  port = options.get("email", "server_port")

  subject = "New IP - {}".format(new_ip)
  body = "No more info"
  message = MIMEText(body)
  message["Subject"] = subject
  message["From"] = sender
  message["To"] = receiver
  s = smtplib.SMTP(server, port=port)
  s.ehlo()
  s.starttls()
  s.login(sender, options.get("email", "sender_password"))
  s.sendmail(sender, [receiver], message.as_string())
  s.quit()

def initialize_db(options):
  with sqlite3.connect(options.get("sqlite", "db")) as conn:
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE ips (date text, ip text)")
    conn.commit()

def read_cfg():
  parser = configparser.ConfigParser()
  parser.read("checker.cfg")
  return parser

def log(msg):
  logging.info(msg)

def main():
  current_timestamp = datetime.datetime.now()
  log("Starting check at {}".format(current_timestamp))
  options = read_cfg()
  try:
    initialize_db(options)
  except sqlite3.OperationalError:
    log("DB with name '{}' already exists.".format(options.get("sqlite", "db")))
  current_ip = get_ip(options)
  has_changed = check_ip_change(current_ip, options)
  if has_changed:
    store_ip(current_ip, current_timestamp, options)
    email_new_ip(current_ip, options)
  log("Ending check...")
if __name__ == "__main__":
  main()
