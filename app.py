from scraper import scraper
from scraper import sentimenter
from db import accessor as ddb

# TODO
# Add twitter
# Categorize by date
# Stream new submissions to lambda
# Implement batch Comprehend calls
# Increase number of submissions analyzed (PRAW subreddit submissions query limit is 1000)
# Put items into campaign's table by date (each Item is a separate day)
# Create Lambda function to analyze data (overall sentiment by date)
# Store that information into a Sentiment_<CampaignName> table
# Index into ElasticSearch and continuously index new/streamed data
# Create UI element to specify items to get by date (submissions show in list) from ElasticSearch
# Show the date's Submissions and overall sentiment when a date is specified
# Prettify UI
# Flag posts requiring attention

# See the *_scratch.json files for the submissions and analysis_results structure templates


def run_scraper_and_analyzer(query_parameters):
    print("running")
    sources = query_parameters["sources"]
    keywords_list = query_parameters["keywords_list"]
    subreddits_list = []
    if "reddit" in sources:
        subreddits_list = query_parameters["subreddits_list"]

    # Scrape the data from sources
    print("scraping")
    reddit = scraper.init_reddit_scraper()
    submissions, analysis_results = scraper.scrape_submissions_from_subreddits(reddit, subreddits_list, keywords_list)
    analysis_results["sources"] = sources
    analysis_results["keywords"] = keywords_list

    # Analyze the text
    # (desired) side effect: analysis_results will be modified
    print("analyzing sentiment")
    sentimenter.analyze(submissions, analysis_results)

    print("submissions", submissions)
    print("analysis_results", analysis_results)
    return analysis_results


mock_params = {
    "keywords_list": ["the"],
    "subreddits_list": ["uwaterloo"],
    "sources": ["reddit"]
}

# run_scraper(mock_params)


def run_create_table(info):
    print("run_create_table with info ", info)
    table_name = info["Keys"]["CampaignName"]["S"].replace(" ", "")
    ddb.create_table(table_name)

    # call run_scraper
    campaign_params_info = info["NewImage"]
    query_parameters = {
        "keywords_list": campaign_params_info["keywords"]["SS"],
        "subreddits_list": campaign_params_info["subreddits"]["SS"],
        "sources": campaign_params_info["sources"]["SS"]
    }

    result = run_scraper_and_analyzer(query_parameters)

    # put returned data into table if it is active
    ddb.put_item(table_name, result)


def run_delete_table(info):
    print("run_delete_table with info", info)
    table_name = info["Keys"]["CampaignName"]["S"].replace(" ", "")
    ddb.delete_table(table_name)