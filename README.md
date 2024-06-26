# Project Description

This template demonstrates extracting data from APIs and loading it into a MySQL database via a Python pipeline.

Inside the python file, the ETL process will be used to prepare the data for the mySQL database. All data is taken from rapidAPIs and in this example we will be [grabbing nba data from this api](https://api-sports.io/documentation/nba/v2)

## Installation

We will be utilising mySQL by Oracle, which can be installed [here](https://dev.mysql.com/downloads/installer/)

We will also be using multiple libraries in our python so be sure to install this
```bash
pip install pandas python-dotenv mysql-connector-python
```

## Pseudo-Code

The approach for this project goes like this:

1. Define the data we want from the REST API
2. Send a GET request to the API for the data we want
3. Transform the data
4. Load the initial historical data and append more updated data to the MySQL database
5. Schedule the data pipeline jobs to be executed every 5 mins (using a list of dates provided)


## Analysing the Dataset

From the [documentation](https://api-sports.io/documentation/nba/v2#section/Authentication/API-SPORTS-Account), we can see that every request that we make to the api returns 6 parameters

```bash
get("https://v2.nba.api-sports.io/status");

// response
{
    "get": "status",
    "parameters": [],
    "errors": [],
    "results": 1,
    "response": {
        "account": {
            "firstname": "xxxx",
            "lastname": "XXXXXX",
            "email": "xxx@xxx.com"
        },
        "subscription": {
            "plan": "Free",
            "end": "2020-04-10T23:24:27+00:00",
            "active": true
        },
        "requests": {
            "current": 12,
            "limit_day": 100
        }
    }
}
```

What we are interested is the response parameter, where all the information is stored in.
Since we are only interested in receiving data from this api, we will only be using the GET request

After querying the API using an app like [Postman](https://www.postman.com/), we can kind of visualize the data that will be given to us 

```json
{
    "get": "standings/",
    "parameters": {
        "league": "standard",
        "season": "2022"
    },
    "errors": [],
    "results": 30,
    "response": [
        {
            "league": "standard",
            "season": 2022,
            "team": {
                "id": 2,
                "name": "Boston Celtics",
                "nickname": "Celtics",
                "code": "BOS",
                "logo": "https://upload.wikimedia.org/wikipedia/fr/thumb/6/65/Celtics_de_Boston_logo.svg/1024px-Celtics_de_Boston_logo.svg.png"
            },
            "conference": {
                "name": "east",
                "rank": 2,
                "win": 57,
                "loss": 25
            },
            "division": {
                "name": "atlantic",
                "rank": 1,
                "win": 57,
                "loss": 25,
                "gamesBehind": null
            },
            "win": {
                "home": 32,
                "away": 25,
                "total": 57,
                "percentage": "0.695",
                "lastTen": 8
            },
            "loss": {
                "home": 9,
                "away": 16,
                "total": 25,
                "percentage": "0.305",
                "lastTen": 2
            },
            "gamesBehind": null,
            "streak": 3,
            "winStreak": true,
            "tieBreakerPoints": null
        },
```

Because the data inside has nested dictionaries, we need to flatten the table using pandas to make the table SQL-compatible



## Rate Limits

Since our rapidAPI account is free, we have a limit on how many times you can request, so therefore we need to make a function that checks the daily usage left to make sure we do not overshoot


## NOTE
This is just an example and a template of how to convert data from a rest API to mySQL table, the approach may need to be changed if the rest API gives data in a different format or there are different data required. Please adapt this code accordingly