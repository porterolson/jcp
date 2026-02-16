# Job Connections Project Repo

#### (1) Clone Repo
Clone the repository to your local machine:

`git clone https://github.com/porterolson/jcp.git`

#### (2) Download Anaconda
Download Anaconda if you do not have it already:

https://www.anaconda.com/download

#### (3) Setup Environment

Once downloaded `Windows Key + S` or `Command (⌘) + Space bar` then search for Anaconda Prompt, open it.

Change your directory to where you cloned this repo:

(e.g. `cd C:\Users\Porter\Desktop\jcp`)

Run to create a conda environment using the yaml file in the repo.

`conda env create -f def_dev.yml`

#### (4) Running the scripts
------

##### (4.1) Getting Job Script

This script is used for getting jobs that have qualification lists and valid html and direct job link and then posting them to the wordpress site using the Wordpress REST API.

NEEDS: `USERNAME`, `APP_PASSWORD`, `token` (instructions in the code)

OUTPUTS: a csv file containing the jobs posted to wordpress (e.g. `2-16-2026_baker_seattle_jobs.csv`)

also posts directly to wordpress using Wordpress API


