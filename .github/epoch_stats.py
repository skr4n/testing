import os
import psycopg2
import csv
from datetime import datetime

dsn = os.environ.get("DATABASE_URL")
if dsn is None:
    print("DATABASE_URL must be set")
    exit(1)
conn = psycopg2.connect(dsn)

with open("epoch_stats.csv") as f:
    reader = csv.reader(f, dialect='unix')
    epochs = list(reader)

print("epoch len:", len(epochs))
if len(epochs) == 0:
    first_run = True
    last_saved_epoch = '2024-03-30'
else:
    first_run = False
    last_saved_epoch = epochs[1][1]

try:
    last_saved_epoch = datetime.strptime(last_saved_epoch, "%Y-%m-%d").date()
except Exception as e:
    print(e)
    exit(1)

print(f"fetching new epochs since {str(last_saved_epoch)}")
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT
        *,
        distributed_tokens / total_active_votes AS tokens_per_vote,
        distributed_rewards_usd / total_active_votes AS usd_per_vote,
        '' AS volume
    FROM stake_epochs
    WHERE epoch > (%s)
    ORDER BY epoch DESC
    """, [str(last_saved_epoch)])

    new_epochs = []
    for row in cursor.fetchall():
        new_epochs.append(list(str(col) for col in row))
    col_names = [desc[0] for desc in cursor.description]

mode = 'w+' if first_run else 'a'
with open('epoch_stats.csv', mode) as f:
    writer = csv.writer(f, dialect='unix', quoting=csv.QUOTE_MINIMAL)
    if first_run:
        writer.writerow(col_names)
    writer.writerows(new_epochs)
print(f"found {len(new_epochs)} new epochs since {last_saved_epoch}:\n{new_epochs}")

conn.close()
