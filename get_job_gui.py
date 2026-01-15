# ---------------- GUI WRAPPER ----------------
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# ---------------- YOUR ORIGINAL IMPORTS ----------------
import polars as pl
import pandas as pd
from datetime import datetime
import datetime as dt
from jobspy import scrape_jobs
import requests
from bs4 import BeautifulSoup

# ---------------- YOUR ORIGINAL FUNCTION ----------------
def page_contains_keywords(url, keywords, timeout=10):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        page_text = soup.get_text(separator=" ").lower()

        for kw in keywords:
            if kw.lower() in page_text:
                return 1
        return 0

    except Exception as e:
        print(f"Error with {url}: {e}")
        return 0

# ---------------- YOUR SCRIPT (UNCHANGED LOGIC) ----------------
def run_script(OCC_TITLE, DATE_POSTED, OCC_LOCATION):
    try:
        today = datetime.today()

        try:
            date_posted_datetime = datetime.strptime(DATE_POSTED, "%m/%d/%Y")
        except ValueError:
            messagebox.showerror("Invalid Date", "Use MM/DD/YYYY format")
            return

        delta = today - date_posted_datetime
        DELTA_HOURS = delta.total_seconds() / 3600

        print("LOADING\n")
        print("Warnings and errors from jobspy search sites may appear, but the program is still running")

        jobs = scrape_jobs(
            site_name=["indeed", "linkedin", "zip_recruiter", "google", "glassdoor"],
            search_term=OCC_TITLE,
            google_search_term=f"{OCC_TITLE} jobs near {OCC_LOCATION} since {DATE_POSTED}",
            location=OCC_LOCATION,
            results_wanted=20,
            hours_old=int(DELTA_HOURS),
            country_indeed="USA",
            linkedin_fetch_description=True,
        )

        jobs_pl = pl.DataFrame(jobs)
        jobs_potential = jobs_pl.filter(pl.col("job_url_direct").is_not_null())

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

        job_list = jobs_potential["job_url_direct"].to_list()
        results = []

        for url in job_list:
            results.append(page_contains_keywords(url, KEYWORDS))

        jobs_potential = jobs_potential.with_columns(
            pl.Series(results).alias("qualifications")
        )

        jobs_potential_final = jobs_potential.filter(
            pl.col("qualifications") == 1
        )


        lower_occ_title=OCC_TITLE.lower()
        lower_occ_title=lower_occ_title.strip()
        out_file = f"{today.month}-{today.day}-{today.year}_{lower_occ_title}_jobs.csv"
        jobs_potential_final.write_csv(out_file)

        messagebox.showinfo(
            "Done",
            f"Found {sum(results)} jobs with qualifications.\nSaved to {out_file}"
        )

    except Exception as e:
        messagebox.showerror("Error", str(e))

    finally:
        stop_loading()

# ---------------- LOADING SPINNER CONTROL ----------------
def start_loading():
    run_btn.config(state="disabled")
    spinner.start(10)
    spinner.grid(row=4, column=0, columnspan=2, pady=10)

def stop_loading():
    spinner.stop()
    spinner.grid_remove()
    run_btn.config(state="normal")

# ---------------- THREAD START ----------------
def start():
    start_loading()
    threading.Thread(
        target=run_script,
        args=(
            occ_entry.get(),
            date_entry.get(),
            loc_entry.get()
        ),
        daemon=True
    ).start()

# ---------------- TKINTER UI ----------------
root = tk.Tk()
root.title("Job Qualification Scraper")
root.geometry("480x260")
root.resizable(False, False)

frame = ttk.Frame(root, padding=15)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="Occupation Title").grid(row=0, column=0, sticky="w")
occ_entry = ttk.Entry(frame, width=40)
occ_entry.grid(row=0, column=1)

ttk.Label(frame, text="Earliest Date Posted (MM/DD/YYYY)").grid(row=1, column=0, sticky="w")
date_entry = ttk.Entry(frame, width=40)
date_entry.grid(row=1, column=1)

ttk.Label(frame, text="Location").grid(row=2, column=0, sticky="w")
loc_entry = ttk.Entry(frame, width=40)
loc_entry.grid(row=2, column=1)

run_btn = ttk.Button(frame, text="Run", command=start)
run_btn.grid(row=3, column=1, pady=10, sticky="e")

# 🔄 SPINNER (hidden by default)
spinner = ttk.Progressbar(frame, mode="indeterminate", length=300)
spinner.grid_remove()

root.mainloop()
