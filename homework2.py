import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from scipy.stats import linregress
import networkx as nx

con = sqlite3.connect("database.sqlite")
cursor = con.cursor()

# TASK 2

"""
Exercise 2.1 Growth: This year, we are renting 16 servers to run our social media platform. They are soon at 100% capacity, so we need to rent more servers.
 We would like to rent enough to last for 3 more years without upgrades, plus 20% capacity for redundancy. 
 We need an estimate of how many servers we need to start renting based on past growth trends. 
 Plot the trend on a graph using Python and include it below. Answer and explain your queries/calculations below. 
 You may use SQL and/or Python to perform this task. (Note that the dataset may not end in the current year, please assume that the last data marks today’s date) (3 points)
"""
# User - created_at 7, comments - created_at 5, posts - created_at 4 
cursor.execute("SELECT id, created_at FROM users;")
users = cursor.fetchall()
users = [(x[0], datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S")) for x in users]
users = [(7, x[1]) for x in users]

cursor.execute("SELECT id, created_at FROM comments;")
comments = cursor.fetchall()
comments = [(x[0], datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S")) for x in comments]
comments = [(5, x[1]) for x in comments]

cursor.execute("SELECT id, created_at FROM posts;")
posts = cursor.fetchall()
posts = [(x[0], datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S")) for x in posts]
posts = [(4, x[1]) for x in posts]

points_and_dates = list(users) + list(comments) + list(posts)
points_and_dates.sort(key=lambda x: x[1])

binned_points_and_dates = {}
for points, timestamp in points_and_dates:
    date = timestamp.date()
    if date not in binned_points_and_dates:
        binned_points_and_dates[date] = 0
    binned_points_and_dates[date] += points

binned_dates = list(binned_points_and_dates.keys())
binned_points = list(binned_points_and_dates.values())

cum_points = list(np.cumsum(binned_points))
min_date = binned_dates[0]
max_date = binned_dates[-1]
goal_date = max_date.replace(year=max_date.year + 3)
binned_dates.append(goal_date)
binned_points.append(0)
cum_points.append(None)

dates_ordinal = np.array([d.toordinal() for d in binned_dates])
goal_date_ordinal = dates_ordinal[-1]
reg = linregress(dates_ordinal[:-1], binned_points[:-1])

start_point = reg.intercept + reg.slope * dates_ordinal[-2]
print(start_point)
prediction = reg.intercept + reg.slope * goal_date_ordinal
print(prediction)
prediction = prediction * 1.2
print(prediction)
change = prediction / start_point
print(change)
servers = 16 * change
print(f"Needed servers: {servers}")



plt.figure(figsize=(10, 6))
plt.plot(dates_ordinal, cum_points, alpha=0.5)
plt.xlabel('Ordinal time')
plt.ylabel('cumulative data points per day')
plt.show()

plt.plot(dates_ordinal, binned_points, alpha=0.5)
plt.axline(xy1=(0, reg.intercept), slope=reg.slope, linestyle="--", color="k")
plt.xlabel('Ordinal time')
plt.ylabel('data points per day')
plt.xlim(min_date.toordinal(), goal_date.toordinal())
plt.ylim(0, max(binned_points) * 1.1)
plt.show()

"""
Exercise 2.2 Virality: Identify the 3 most viral posts in the history of the platform. 
Select and justify a specific metric or requirements for a post to be considered viral. 
Answer and explain your queries/calculations below. You may use SQL and/or Python to perform this task. (4 points)
"""
cursor.execute("SELECT id, post_id FROM comments;")
comments = cursor.fetchall()

cursor.execute("SELECT id, post_id FROM reactions;")
reactions = cursor.fetchall()

# When measuring virality, both the amount of reactions and comments are considered. With the comments having a 1.5x weight compared to reactions.
# This is because database contains around 1.5x more reactions than commments, which makes sense since commenting requires more effort than reacting.
posts_scores = {}
posts_reaction_counts = {}
for reaction in reactions:
    post_id = reaction[1]
    if post_id not in posts_scores:
        posts_scores[post_id] = 0
    posts_scores[post_id] += 1
    if post_id not in posts_reaction_counts:
        posts_reaction_counts[post_id] = 0
    posts_reaction_counts[post_id] += 1

posts_comment_counts = {}
for comment in comments:
    post_id = comment[1]
    if post_id not in posts_scores:
        posts_scores[post_id] = 0
    posts_scores[post_id] += 1.5
    if post_id not in posts_comment_counts:
        posts_comment_counts[post_id] = 0
    posts_comment_counts[post_id] += 1

most_viral_posts = sorted(posts_scores.items(), key=lambda x: x[1], reverse=True)[:3]

count = 1
for post_id, engagement in most_viral_posts:
    cursor.execute(f"SELECT content FROM posts WHERE id = {post_id}")
    content = cursor.fetchone()[0]
    print(f"TOP {count} Post ID: {post_id}, Score: {engagement}, Comments: {posts_comment_counts.get(post_id)}, Reactions: {posts_reaction_counts.get(post_id)}, Content: {content}")
    count += 1

"""
Exercise 2.3 Content Lifecycle: What is the average time between the publishing of a post and the first engagement it receives? 
What is the average time between the publishing of a post and the last engagement it receives? 
Answer and explain your queries/calculations below. You may use SQL and/or Python to perform this task. (4 points)
"""
cursor.execute("SELECT id, created_at FROM posts;")
posts = cursor.fetchall()
posts = [(x[0], datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S").timestamp()) for x in posts]

cursor.execute("SELECT post_id, created_at FROM comments;")
comments = cursor.fetchall()
comments = [(x[0], datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S").timestamp()) for x in comments]

# Reactions do not have timestamps so they cannot be used for this task

comments_dict = {}
for comment in comments:
    post_id = comment[0]
    comment_time = comment[1]
    if post_id not in comments_dict:
        comments_dict[post_id] = (comment_time, comment_time)
    else:
        if comment_time < comments_dict[post_id][0]:
            comments_dict[post_id] = (comment_time, comments_dict[post_id][1])
        elif comment_time > comments_dict[post_id][1]:
            comments_dict[post_id] = (comments_dict[post_id][0], comment_time)

posts_with_no_engagement_count = 0
post_time_delta = {}
for post in posts:
    post_id = post[0]
    post_time = post[1]
    if post_id in comments_dict:
        first_engagement_time = comments_dict[post_id][0]
        last_engagement_time = comments_dict[post_id][1]
        first_delta = first_engagement_time - post_time
        last_delta = last_engagement_time - post_time
        post_time_delta[post_id] = (first_delta, last_delta)
    else:
        posts_with_no_engagement_count += 1

posts_with_engagement_count = len(posts) - posts_with_no_engagement_count

first_engagement_average = sum([x[0] for x in post_time_delta.values()]) / posts_with_engagement_count
last_engagement_average = sum([x[1] for x in post_time_delta.values()]) / posts_with_engagement_count

print(f"First engagement average: in seconds: {round(first_engagement_average, 2)}, in hours: {round(first_engagement_average / 3600, 2)}, in days: {round(first_engagement_average / 86400, 2)}")
print(f"Last engagement average: in seconds: {round(last_engagement_average, 2)}, in hours: {round(last_engagement_average / 3600, 2)}, in days: {round(last_engagement_average / 86400, 2)}")
print(f"Total posts: {len(posts)}, Posts with no engagement: {posts_with_no_engagement_count}")

"""
Exercise 2.4 Connections: Identify the top 3 user pairs who engage with each other’s content the most. 
Define and describe your metric for engagement. Answer and explain your queries/calculations below. 
You may use SQL and/or Python to perform this task. (4 points)
"""

G = nx.DiGraph()

cursor.execute("SELECT id FROM users;")
users = cursor.fetchall()

for user in users:
    G.add_node(user[0])

cursor.execute("SELECT id, user_id FROM posts;")
posts = cursor.fetchall()

cursor.execute("SELECT user_id, post_id FROM reactions;")
reactions = cursor.fetchall()

cursor.execute("SELECT user_id, post_id FROM comments;")
comments = cursor.fetchall()

posts_by_user = {}
for post in posts:
    posts_by_user[post[0]] = post[1]

reactions_temp = []
for reaction in reactions:
    reactions_temp.append((reaction[0], posts_by_user.get(reaction[1])))

comments_temp = []
for comment in comments:
    comments_temp.append((comment[0], posts_by_user.get(comment[1])))

engagements = reactions_temp + comments_temp

edge_weights = {}
for engagement in engagements:   
    if engagement not in edge_weights:
        edge_weights[engagement] = 0
    edge_weights[engagement] += 1

to_be_removed = []
for (from_user, to_user), weight in edge_weights.items():
    if from_user is not None and to_user is not None:
        if from_user != to_user:
            G.add_edge(from_user, to_user, weight=weight)
        else:
            to_be_removed.append((from_user, to_user))

for edge in to_be_removed:
    edge_weights.pop(edge)

G.remove_nodes_from(list(nx.isolates(G)))

# CODE FOR DISPLAYING THE GRAPH (SLOW)

pos = nx.kamada_kawai_layout(G)
nx.draw(G, pos, node_size=30, width=0.1, arrowsize=4)

edge_labels = nx.get_edge_attributes(G, "weight")
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, bbox=dict(alpha=0))

plt.show()

# END OF CODE FOR DISPLAYING THE GRAPH

total_edge_weights = {}
for (from_user, to_user), weight in edge_weights.items():
    if (to_user, from_user) in edge_weights:
        if (from_user, to_user) in total_edge_weights or (to_user, from_user) in total_edge_weights:
            continue
        weight2 = edge_weights[(to_user, from_user)]
        if weight >= weight2:
            weight_ratio = weight2 / weight
        else:
            weight_ratio = weight / weight2

        if weight_ratio > 0.1:
            total_weight = weight + weight2
            total_edge_weights[(from_user, to_user)] = (total_weight, weight, weight2, weight_ratio)

total_edge_weights = sorted(total_edge_weights.items(), key=lambda x: x[1][0])

count = 1
for element in total_edge_weights[-3:]:
    print(f"Top {count} user pair:")
    print(f"User 1 id: {element[0][0]}, User 2 id: {element[0][1]}, Total engagements: {element[1][0]}, 1 to 2 engagements: {element[1][1]}, 2 to 1 engagements: {element[1][2]}, ratio: {round(element[1][3], 2)}")
    count += 1

con.close()