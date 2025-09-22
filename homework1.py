import sqlite3

con = sqlite3.connect("database.sqlite")
cursor = con.cursor()

# TASK 1
"""
Exercise 1.1 Reading the dataset: Load the database and for each table, print and inspect the available columns and the number of 
rows. Explain below how you loaded the database. For each table, describe all columns (name, purpose, type, example of contents). 
You may use SQL and/or Python to perform this task. (3 points)
""" 

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
tables.remove(('sqlite_sequence',))

for table in tables:
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    print(f"table: {table[0]}, rows: {cursor.fetchone()[0]}")
    for col in columns:
        print(col)

"""
Exercise 1.2 Lurkers: How many users are there on the platform who have not interacted with posts or posted any content yet 
(but may have followed other users)? Answer and explain your queries/calculations below. 
You may use SQL and/or Python to perform this task. (3 points)
"""

cursor.execute("SELECT a.id FROM users a WHERE a.id NOT IN (SELECT b.user_id FROM reactions b UNION SELECT c.user_id FROM comments c UNION SELECT d.user_id FROM posts d);")
lurkers = cursor.fetchall()
print(f"Lurkers: {len(lurkers)}")

"""
Exercise 1.3 Influencers: In the history of the platform, who are the 5 users with the most engagement on their posts? 
Describe how you measure engagement. Answer and explain your queries/calculations below. 
You may use SQL and/or Python to perform this task. (4 points)
"""
cursor.execute("SELECT id FROM users;")
users = cursor.fetchall()

posts_by_user = {}
for user in users:
    cursor.execute(f"SELECT id FROM posts WHERE user_id = {user[0]};")
    posts = cursor.fetchall()
    if posts:
        posts_dict = {}
        for post in posts:
            cursor.execute(f"SELECT COUNT(*) FROM reactions WHERE post_id = {post[0]};")
            reactions_count = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM comments WHERE post_id = {post[0]};")
            comments_count = cursor.fetchone()[0]
            posts_dict[post[0]] = reactions_count + comments_count
        posts_by_user[user[0]] = posts_dict
    else:
        posts_by_user[user[0]] = {}

total_engagement_by_user = {}
for user, posts in posts_by_user.items():
    total_engagement_by_user[user] = sum(posts.values())

total_engagement_by_user = dict(sorted(total_engagement_by_user.items(), key=lambda item: item[1], reverse=True))

print("Top 5 influencers:")
for i in range(5):
    user_id = list(total_engagement_by_user.keys())[i]
    cursor.execute(f"SELECT username FROM users WHERE id = {user_id};")
    username = cursor.fetchone()[0]
    engagement = total_engagement_by_user[user_id]
    print(f"User id: {user_id}, Username: {username}, Engagement: {engagement}")

"""
Exercise 1.4 Spammers: Identify users who have shared the same text in posts or comments at least 3 times over and over again (in all their history, not just the last 3 contributions). Answer and explain your queries/calculations below. You may use SQL and/or Python to perform this task. (5 points)
"""
cursor.execute("SELECT id FROM users;")
users = cursor.fetchall()

user_contents_count = {}
for user in users:
    cursor.execute(f"SELECT content FROM posts WHERE user_id = {user[0]} UNION ALL SELECT content from comments WHERE user_id = {user[0]};")
    contents = cursor.fetchall()
    if contents:
        content_dict = {}
        for content in contents:
            if content[0] in content_dict:
                content_dict[content[0]] += 1
            else:
                content_dict[content[0]] = 1
        user_contents_count[user[0]] = content_dict
    else:
        user_contents_count[user[0]] = {}

spammers = []

for user, contents in user_contents_count.items():
    for content, count in contents.items():
        if count >= 3:
            cursor.execute(f"SELECT username FROM users WHERE id = {user};")
            username = cursor.fetchone()[0]
            spammers.append((user, username))
            break
print("Spammers:")
print(spammers)

con.close()