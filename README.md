# Job Connections Project Repo

## (1) Setup Repo
-------
##### (1.1) Get Local Code Editor
Open your local code editor (e.g. VS Code, PyCharm, I use VS Code personally, so this tutorial is for VS Code)
If you do not have VS Code you can download it for free here: https://code.visualstudio.com/download

##### (1.2) Get Git
Also make sure you have Git, install it here if you do not: https://git-scm.com/install/

During install of Git, if prompted `Add Git to PATH` make sure that option or box is checked!

##### (1.3) Clone Repo
In VS Code `File → Open Folder` and select your project folder to open it in VS Code

In the top menu `Terminal → New Terminal` to open an instance of the VS Code Terminal

Clone the repository to your local machine (need git installed; after installing git, you should restart your VS Code instance):

`git clone https://github.com/porterolson/jcp.git`

------
## (2) Download Anaconda
Download Anaconda if you do not have it already:

https://www.anaconda.com/download

## (3) Setup Environment

Once Anaconda is downloaded and installed `Windows Key + S` or `Command (⌘) + Space bar` then search for Anaconda Prompt, open it.

Change your directory to where you cloned this repo:

(e.g. `cd C:\Users\Porter\Desktop\jcp`)

Run to create a conda environment using the yaml file in the repo.

`conda env create -f def_dev.yml`

## (4) Running the scripts
------

##### (4.1) Getting Job Script

This script is used for getting jobs that have qualification lists and valid html and direct job link and then posting them to the Wordpress site using the Wordpress REST API.

NEEDS: `USERNAME`, `APP_PASSWORD`, `token` (instructions to get these are in **APPENDIX**)

OUTPUTS: a csv file containing the jobs posted to Wordpress (e.g. `2-16-2026_baker_seattle_jobs.csv`)

ALSO posts directly to Wordpress using Wordpress API

---------

##### (4.2) Job Expiration Script

This script uses Wordpress API to loop thru the check the direct links of each post to see if the job is still available or if the page is returns a Error 404 or soft 404.

NEEDS: `USERNAME`, `APP_PASSWORD`, `GEMINI_API_KEY`, `POST_TYPE` (further instructions in **APPENDIX**)

OUTPUTS: None

ALSO Privitizes all posts with non 200 response codes or have a high probability of being a soft 404 error.

------

## (Appendix)

#### (A.1) original_treat.txt
`original_treat.txt` contains the original treatment text script where a user recieves the same treatment every time, whereas the current script in `get_jobs_github.py` has a different treatment every time you reload the page. I include `original_treat.txt` in this repo so that if one desires to test/use the original treatment it is readily available.

------
#### (A.2) Getting Wordpress Username and Password
Start by emailing `Doctor Eastmond` and asking to be made an admin on Wordpress. This is the website building software we use to host and edit the JCP website, so you need access to be able to post job ads, remove job ads, edit website content, and access the data we collect.

If you don’t already have a Wordpress account, you’ll have to make one. It’s probably best to create it using your google account.

Once you have an account and are an admin, goto `https://jobconnectionsproject.org/wp-admin/index.php`

**ONCE AGAIN, DO NOT RUN THE UPDATER!!**

On the side menu goto `Users → Profile`

Scroll down to the bottom until you see this:
<img width="1698" height="571" alt="image" src="https://github.com/user-attachments/assets/608db582-e5c7-4ddd-ab67-e916b5366a48" />

Enter a new name for you application_password (NOTE: this is not your username).

Make sure to save/write down the password Wordpress then generates for you, this is your `application password`. Your `USERNAME` is simply your wordpress username (not the name of app_password)

Put these in the scripts and you are ready to use Wordpress API!

-------

#### (A.3) Getting GitHub Models Token

Start by creating a GitHub account.

Next goto `https://github.com/marketplace/models/azure-openai/gpt-4-1-mini`

Click on "Use This Model"
<img width="1917" height="937" alt="image" src="https://github.com/user-attachments/assets/b7e43b14-6883-4565-9160-c9d2555f6aa5" />

Click "Create Personal Access Token"
<img width="765" height="284" alt="image" src="https://github.com/user-attachments/assets/75ecf9e1-1f10-4bc7-9a44-a14567108381" />

Leave all the settings at their default and pick an expiration date (your token will no longer work after this date), and then click `Generate Token` at the bottom of the page.

Save your token to a safe place, and then use this in place of `token` in `get_jobs_github.py`

--------
#### (A.4) Getting Gemeni Token








