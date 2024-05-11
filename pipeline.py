import os
import requests
import pandas as pd
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import json

load_dotenv("keys.env")

API_KEY = os.getenv("RAPIDAPI_KEY")

url = "https://api-nba-v1.p.rapidapi.com/standings"

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com",
}

params = {"league": "standard", "season": "2022"}


def check_rate_limits():
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    daily_limit = response.headers.get("x-ratelimit-requests-limit")
    remaining = response.headers.get("x-ratelimit-requests-remaining")
    calls_per_min_allowed = response.headers.get("X-RateLimit-Limit")
    calls_per_min_remaining = response.headers.get("X-RateLimit-Remaining")
    rate_limits = {
        "daily_limit": daily_limit,
        "remaining": remaining,
        "calls_per_min_allowed": calls_per_min_allowed,
        "calls_per_min_remaining": calls_per_min_remaining,
    }

    print(rate_limits)


def get_team_stats(url, headers, params):

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(err)
    except requests.exceptions.RequestException as e:
        print(e)
    except requests.exceptions.Timeout as t:
        print(t)
    except requests.exceptions.RequestException as re:
        print(re)


def get_top_5_teams(data):
    teams = data["response"]
    top_teams = []

    sorted_teams = sorted(teams, key=lambda x: (x["conference"]["rank"]))

    for team in sorted_teams[:5]:
        top_teams.append(
            {
                "Team Name": team["team"]["name"],
                "Conference": team["conference"]["name"],
                "Rank": team["conference"]["rank"],
                "Total Wins": team["win"]["total"],
                "Total Losses": team["loss"]["total"],
                "Win Details": team["win"],
                "Loss Details": team["loss"],
                "Division Details": team["division"],
                "Streak Details": {
                    "Current Streak": team["streak"],
                    "Winning Streak": team["winStreak"],
                    "Tie Breaker Points": team["tieBreakerPoints"],
                },
                "Logo": team["team"]["logo"],
            }
        )
    return top_teams


def create_dataframe(topteams):

    df = pd.DataFrame(topteams)

    # Flatten 'Win Details'
    win_details_df = df["Win Details"].apply(pd.Series)
    win_details_df.columns = [
        "Win_" + str(col) for col in win_details_df.columns
    ]  # Rename columns
    df = pd.concat([df.drop(["Win Details"], axis=1), win_details_df], axis=1)

    # Flatten 'Loss Details'
    loss_details_df = df["Loss Details"].apply(pd.Series)
    loss_details_df.columns = ["Loss_" + str(col) for col in loss_details_df.columns]
    df = pd.concat([df.drop(["Loss Details"], axis=1), loss_details_df], axis=1)

    # Flatten 'Division Details'
    division_details_df = df["Division Details"].apply(pd.Series)
    division_details_df.columns = [
        "Division_" + str(col) for col in division_details_df.columns
    ]
    df = pd.concat([df.drop(["Division Details"], axis=1), division_details_df], axis=1)

    # Flatten 'Streak Details'
    streak_details_df = df["Streak Details"].apply(pd.Series)
    streak_details_df.columns = [
        "Streak_" + str(col) for col in streak_details_df.columns
    ]
    df = pd.concat([df.drop(["Streak Details"], axis=1), streak_details_df], axis=1)

    return df


create_dataframe(get_top_5_teams(get_team_stats(url, headers, params)))

HOST = os.getenv("HOST")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_USERNAME = os.getenv("MYSQL_USERNAME")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")


def create_connection_to_db(host, username, password, db):

    connection = None
    try:
        connection = mysql.connector.connect(
            host=host, user=username, passwd=password, database=db
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection


def create_table(connection):

    CREATE_TABLE_SQL_QUERY = """
    CREATE TABLE IF NOT EXISTS top_teams (
    Team_Name VARCHAR(255),
    Conference VARCHAR(255),
    Rank INT,
    Total_Wins INT,
    Total_Losses INT, 
    Division_Name VARCHAR(255),
    Division_Rank INT,
    Division_Win INT,
    Division_Loss INT,
    Division_GamesBehind VARCHAR(255), -- assuming GamesBehind could be NULL or a string
    Win_Home INT,
    Win_Away INT,
    Win_Total INT,
    Win_Percentage VARCHAR(255),
    Win_LastTen INT,
    Loss_Home INT,
    Loss_Away INT,
    Loss_Total INT,
    Loss_Percentage VARCHAR(255),
    Loss_LastTen INT,
    Streak_CurrentStreak INT,
    Streak_WinningStreak BOOLEAN,
    Streak_TieBreakerPoints VARCHAR(255), -- assuming it can be NULL or a string
    Logo VARCHAR(1024)
);
    """
    try:
        cursor = connection.cursor()
        cursor.execute(CREATE_TABLE_SQL_QUERY)
        connection.commit()
        print("Table created successfully")
    except Error as e:
        print(f"The error '{e}' occurred")


def insert_into_table(connection, df):

    cursor = connection.cursor()
    INSERT_DATA_SQL_QUERY = """

    INSERT INTO top_teams (Team_Name, Conference, Rank, Total_Wins, Total_Losses, Division_Name, Division_Rank, Division_Win, Division_Loss, Division_GamesBehind, Win_Home, Win_Away, Win_Total, Win_Percentage, Win_LastTen, Loss_Home, Loss_Away, Loss_Total, Loss_Percentage, Loss_LastTen, Streak_CurrentStreak, Streak_WinningStreak, Streak_TieBreakerPoints, Logo)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    
    """
    data_values_astuples= [tuple(x) for x in df.to_numpy()]  
    cursor.executemany(INSERT_DATA_SQL_QUERY, data_values_astuples)
    connection.commit()
    print("Data inserted successfully")



def main():
    check_rate_limits()
    data = get_team_stats(url, headers, params)
    if data and 'response' in data and data['response']:
        topteams = get_top_5_teams(data)
        df = create_dataframe(topteams)
        print(df.to_string(index=False))
    else:
        print("No data found")
    connection = create_connection_to_db(HOST, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DATABASE)

    if connection is not None:
        create_table(connection)
        df = create_dataframe(topteams)
        insert_into_table(connection, df)



main()