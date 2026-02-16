# Job Connections Project Repo

#### (1) Setup Repo
-------
##### (1.1) Get Local Code Editor
Open your local code editor (e.g. VS Code, PyCharm, I use VS Code personally, so this tutorial is for VS Code)
If you do not have VS Code you can download it for free here: https://code.visualstudio.com/download

-------
##### (1.2) Get Git
Also make sure you have Git, install it here if you do not: https://git-scm.com/install/

During install of Git, if prompted `Add Git to PATH` make sure that option or box is checked!

-------
##### (1.3) Clone Repo
In VS Code `File → Open Folder` and select your project folder to open it in VS Code

In the top menu `Terminal → New Terminal` to open an instance of the VS Code Terminal

Clone the repository to your local machine (need git installed; after installing git, you should restart your VS Code instance):

`git clone https://github.com/porterolson/jcp.git`

#### (2) Download Anaconda
Download Anaconda if you do not have it already:

https://www.anaconda.com/download

#### (3) Setup Environment

Once downloaded and installed `Windows Key + S` or `Command (⌘) + Space bar` then search for Anaconda Prompt, open it.

Change your directory to where you cloned this repo:

(e.g. `cd C:\Users\Porter\Desktop\jcp`)

Run to create a conda environment using the yaml file in the repo.

`conda env create -f def_dev.yml`

#### (4) Running the scripts
------

##### (4.1) Getting Job Script

This script is used for getting jobs that have qualification lists and valid html and direct job link and then posting them to the Wordpress site using the Wordpress REST API.

NEEDS: `USERNAME`, `APP_PASSWORD`, `token` (instructions in the code)

OUTPUTS: a csv file containing the jobs posted to Wordpress (e.g. `2-16-2026_baker_seattle_jobs.csv`)

ALSO posts directly to Wordpress using Wordpress API

---------

##### (4.2) Job Expiration Script

This script uses Wordpress API to loop thru the check the direct links of each post to see if the job is still available or if the page is returns a Error 404 or soft 404.

NEEDS: `USERNAME`, `APP_PASSWORD`, `GEMINI_API_KEY`, `POST_TYPE`

OUTPUTS: None

ALSO Privitizes all posts with non 200 response codes or have a high probability of being a soft 404 error.

------

## (A.1)

`original_treat.txt` contains the original treatment text script where a user recieves the same treatment every time, whereas the current script in `get_jobs_github.py` has a different treatment every time you reload the page. I include `original_treat.txt` in this repo so that if one desires to test/use the original treatment it is readily available.



