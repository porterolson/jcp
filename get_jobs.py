
#imports
import polars as pl #i mostly use polars as it is faster than pandas and you can seamlessly switch back and forth when you need
import pandas as pd
from datetime import datetime
import datetime as dt
from jobspy import scrape_jobs
import requests
from bs4 import BeautifulSoup

#####################################################
#prompt user
#####################################################
OCC_TITLE=input('Occupation title: ')
DATE_POSTED=input('Earliest date posted (eg. 1/5/2026): ')
OCC_LOCATION=input('Location: ')

#get the hours since job posting for the hours_old param
today=datetime.today()
try:
    date_posted_datetime=datetime.strptime(DATE_POSTED, "%m/%d/%Y")
except ValueError:
    print('Invalid Date')

#compute the delta of the days and then make it into hours
delta=today-date_posted_datetime
DELTA_HOURS=delta.total_seconds()/3600


################################################################################
#jobspy api (github)
################################################################################
print('LOADING')
print('\n')
print('Warnings and errors from jobspy search sites may appear, but the program is still running')


#returns a pd data frame
jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "zip_recruiter", "google",'glassdoor'], # "glassdoor", "bayt", "naukri", "bdjobs"
    search_term=OCC_TITLE,
    google_search_term=f"{OCC_TITLE} jobs near {OCC_LOCATION} since {DATE_POSTED}",
    location=OCC_LOCATION,
    results_wanted=20,

    hours_old=int(DELTA_HOURS),
    country_indeed='USA',
    
    linkedin_fetch_description=True, # gets more info such as description, direct job url (slower)
    # proxies=["208.195.175.46:65095", "208.195.175.45:65095", "localhost"],
)

###############################################################################

#jobs polars df
#make the jobs df into polars
jobs_pl=pl.DataFrame(jobs)
jobs_potential=jobs_pl.filter(pl.col('job_url_direct').is_not_null())#filter to only have jobs with direct links

#Search the job HTML for these keywords

KEYWORDS = [
    "what you'll need",
    "qualifications",
    "what you'll bring",
    "experience and attributes",
    "basic qualifications",
    "years",
    "what you have",
    "what you'll bring"
]

###Simple function to get keywords on page
#note this doesnot work if the website uses javascript or also blocks automated traffic
def page_contains_keywords(url, keywords, timeout=10):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # Get visible text
        page_text = soup.get_text(separator=" ").lower()

        # Check if ANY keyword appears
        for kw in keywords:
            if kw.lower() in page_text:
                return 1

        return 0

    except Exception as e:
        print(f"Error with {url}: {e}")
        return 0

##########################################################################
#get the list of links that have the direct link
job_list=jobs_potential['job_url_direct'].to_list()
results = [] #init a list 
#check if the keywords show up in the 
for url in job_list:
    flag = page_contains_keywords(url, KEYWORDS)
    results.append(flag)

#make qual a column in the dataframe
qual_series=pl.Series(results)
jobs_potential=jobs_potential.with_columns((qual_series).alias('qualifications'))
jobs_potential_final=jobs_potential.filter(pl.col('qualifications')==1)
##########################################################################

#final
print(f'Found {sum(results)} jobs with direct links and qualifications.')


jobs_potential_final.write_csv(f'{today.month}-{today.day}-{today.year}_jobs.csv')
print(f'Output has been saved to {today.month}-{today.day}-{today.year}_jobs.csv')
