"""
The user of those methods should be able to control at least the following:
Which county, if not ”all counties” to plot the data from - optional argument
the time range to be plotted e.g. Start = ”29/03/2020” End = ”04/08/2020”
- optional argument 4
"""

import os
from typing import Optional
import re
import pandas as pd
import altair as alt
from flask import Flask, render_template, request, send_from_directory, url_for


app = Flask(__name__, static_url_path='/docs/_build/html')


def fix_dates(dmy_date: str) -> str:
    """
    Change day/month/year date to year-month-day
    @param dmy_date: string with date, on day-month-year
    @return: the date-string with right format
    ”29/03/2020”
    """
    if "-" in dmy_date:
        # Date is already a ISO date, don't reformat it
        return dmy_date

    date_array = dmy_date.split("/")
    return f"{date_array[2]}-{date_array[1]}-{date_array[0]}"


def get_data(county: str) -> pd.DataFrame:
    """
    Loads the data set for the given county
    @param county: The county we want to get the data on
    @return: The county as a pandas dataframe
    """
    file = os.path.join("data_files_updated", f"antall-meldte-covid-19-{county.lower()}.csv")
    data = pd.read_csv(file,
                       sep=';',
                       parse_dates=["Dato"],
                       dayfirst=True
                       )
    return data


def plot_reported_cases(county: str, start: Optional[str] = None, end: Optional[str] = None) -> alt.Chart:
    """
        Uses pandas to get info from data, and uses altair to make a bar plot.
        @param county: string, which county we should get data from
        @param start: string, the start date
        @param end: string, the end date
        @return: the bar plot
        """

    if county != "allcounties":
        data = get_data(county)
    else:
        data = get_data("allcounties")
        county = 'Norge'

    if start is not None:
        start = fix_dates(start)
        data = data[data["Dato"] >= start]
    else:
        start = data["Dato"].iloc[0]

    if end is not None:
        end = fix_dates(end)
        data = data[data["Dato"] <= end]
    else:
        end = data["Dato"].iloc[-1]

    regs = '\d{4}-\d{2}-\d{2}'  # remove timestamp
    end = re.findall(regs, str(end))[0]
    start = re.findall(regs, str(start))[0]

    title = 'Oversikt over antall rapporterte smitttede i ' + county + ' fra ' + start + ' til ' + end
    report_plot = alt.Chart(data, title=title).mark_bar().encode(
        x='Dato',
        y='Nye tilfeller',
        tooltip=['Dato', 'Nye tilfeller']
    ).properties(
        width=1120
    )

    return report_plot


def plot_cumulative_cases(county: str, start: Optional[str] = None, end: Optional[str] = None) -> alt.Chart:
    """
    Uses pandas to get info from data, and uses altair to create a line plot.
    @param county: string, which county we should get data from
    @param start: string, the start date
    @param end: string, the end date
    @return: the line plot
    """
    if county != "allcounties":
        data = get_data(county)
    else:
        data = get_data("allcounties")
        county = "Norge"

    if start is not None:
        start = fix_dates(start)
        data = data[data["Dato"] >= start]
    else:
        start = data["Dato"].iloc[0]
    if end is not None:
        end = fix_dates(end)
        data = data[data["Dato"] <= end]
    else:
        end = data["Dato"].iloc[-1]

    regs = '\d{4}-\d{2}-\d{2}' #remove timestamp
    end = re.findall(regs, str(end))[0]
    start = re.findall(regs, str(start))[0]

    #t = 'Oversikt over komulativt antall smitttede i ' + county + ', fra ' + str(start) + ' til ' + str(end)
    t = 'Oversikt over komulativt antall smitttede i ' + county + ', fra ' + start + ' til ' + end

    line_plot = alt.Chart(data, title=t).mark_line(color='green').encode(
        x='Dato',
        y='Kumulativt antall',
        tooltip=['Dato', 'Kumulativt antall']
    ).properties(
        width=1120
    )
    return line_plot


def plot_both(county: str, start: Optional[str] = None, end: Optional[str] = None) -> alt.Chart:
    """
    Combines the plots from the the functions plot_reported_cases
    and plot_cumulative_cases into a new plot.
    @param county: string, which county we should get data from
    @param start: string, the start date
    @param end: string, the end date
    @return: the combined plot
    """
    reported_bar = plot_reported_cases(county, start, end)
    cumulative_line = plot_cumulative_cases(county, start, end)
    if county == 'allcounties':
        county = 'Norge'
    t = 'Oversikt over komulativt antall smitttede og antall rapporterte smitttede i ' + county
    return alt.layer(reported_bar, cumulative_line, title=t).resolve_scale(
        y='independent'
    )


@app.route("/diagrams")
def both():
    """
    Uses the functions plot_cumulative_cases, plot_reported_cases and plot_both, to combine
    all plots and saves them.
    @return: the plot template

    cumulative_plot = plot_cumulative_cases("Oslo", "12/03/2020", "04/08/2020")
    reported_plot = plot_reported_cases("Oslo", "12/03/2020", "04/08/2020")
    both_plots = plot_both("Oslo", "29/03/2020", "04/08/2020")
    all_plots = (cumulative_plot & reported_plot & both_plots)
    all_plots.save(os.path.join("templates", "webPlots.html"))

    cumulative_plot = plot_cumulative_cases("Oslo")
    reported_plot = plot_reported_cases("Oslo")
    both_plots = plot_both("Oslo")
    all_plots = (cumulative_plot & reported_plot & both_plots)
    all_plots.save(os.path.join("templates", "webPlots.html"))
    """

    cumulative_plot = plot_cumulative_cases('allcounties')
    reported_plot = plot_reported_cases('allcounties')
    both_plots = plot_both('allcounties')
    all_plots = (both_plots & cumulative_plot & reported_plot )
    all_plots.save(os.path.join("templates", "webPlots.html"))

    return render_template('webPlots.html')


@app.route("/date")
def date():
    """
    Shows the date page
    @return: the html we want to see on given site
    """
    return render_template('date.html')

@app.route("/")
def startsite():
    """
    Shows the test page
    @return: the html we want to see on given site
    """
    return render_template('test.html')

@app.route("/ommeg")
def ommeg():
    """
    Shows the test page
    @return: the html we want to see on given site
    """
    return render_template('ommeg.html')


@app.route("/cv")
def get_cv():
    workingdir = os.path.abspath(os.getcwd())
    filepath = workingdir + '/static/files/'
    return send_from_directory(filepath, 'cornelia_cv.pdf')

@app.route("/handle_date", methods=['POST', 'GET'])
def handle_date():
    """
    Uses the user input to take inn start_date, end_date and which county we want to see.
    @return: the template with plot.
    """
    start_date = request.form["start_date"]
    end_date = request.form["end_date"]
    county = request.form["all_counties"]
    try:
        plot = plot_both(county, start_date, end_date)
        plot.save(os.path.join("templates", "webPlots2.html"))
        return render_template('webPlots2.html')
    except:
        return "Feil input, prøv igjen"



@app.route('/covid19')
def show_county_plot():
    """
    Shows the start page
    @return: The html code we want to see
    """
    return render_template('base.html')



@app.route('/docs/<path:path>')
def send_docs(path):
    """
    Static file hosting for the sphinx docs
    Args:
        path: file within docs/_build_html
    Returns:
        The requested file
    """
    return send_from_directory('docs/_build/html', path)


if __name__ == '__main__':
    app.run(debug=True)
