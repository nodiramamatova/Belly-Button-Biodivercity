# import necessary libraries
import os
import numpy as np
import pandas as pd

from flask import (    
    Flask,    
    render_template,    
    jsonify,    
    request,   
    redirect)

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import inspect, create_engine, func, desc
from sqlalchemy.engine import reflection
# Flask Setup
app = Flask(__name__)
#DB Setup
engine = create_engine("sqlite:///DataSets/belly_button_biodiversity.sqlite")
# Reflecting db into a new model
Base = automap_base()
# reflect tables
Base.prepare(engine, reflect=True)
# Save tables to classes
Otu = Base.classes.otu
Samples = Base.classes.samples
Samples_metadata = Base.classes.samples_metadata
#initiate a session
session = Session(engine)
#Creating routes
# Return the dashboard homepage
@app.route("/")
def index():
    return render_template("index.html")
#list of the sample names
@app.route("/names")
def names():    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt, session.bind)
    df.set_index('otu_id', inplace=True)
    
    return jsonify(list(df.columns))
#OTU descriptions
@app.route('/otu')
def otu():
    results = session.query(Otu.lowest_taxonomic_unit_found).all()
    otu_list = list(np.ravel(results))
    return jsonify(otu_list)
#MetaData for a given sample.
@app.route('/metadata/<sample>')
def sample_metadata(sample):
    sel = [Samples_metadata.AGE, Samples_metadata.BBTYPE,
           Samples_metadata.ETHNICITY,Samples_metadata.GENDER,
           Samples_metadata.LOCATION,Samples_metadata.SAMPLEID]
    results = session.query(*sel).\
        filter(Samples_metadata.SAMPLEID == sample[3:]).all()
    
    sample_metadata = {}
    for result in results :
        sample_metadata['AGE'] = result[0]
        sample_metadata['BBTYPE'] = result[1]
        sample_metadata['ETHNICITY'] = result[2]
        sample_metadata['GENDER'] = result[3]
        sample_metadata['LOCATION'] = result[4]
        sample_metadata['SAMPLEID'] = result[5]

   
    return jsonify(sample_metadata)
#Weekly Washing Frequency as a number
@app.route('/wfreq/<sample>')
def sample_wfreq(sample):
    results = session.query(Samples_metadata.WFREQ).\
        filter(Samples_metadata.SAMPLEID == sample[3:]).all()
    wfreq = np.ravel(results)
    return jsonify(int(wfreq[0]))
#OTU IDs and Sample Values for a given sample
@app.route('/samples/<sample>')
def samples(sample):
    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt, session.bind)
    
    if sample not in df.columns:
        return jsonify(f"Error : Sample {sample} Not Found!"), 400
    
    #return sample  values greater than 1
    df = df[df[sample] > 1]
    
    # Sort Descending order
    df = df.sort_values(by=sample, ascending=0)
    
    #format the data to send as json
    data = [{
		'otu_ids': df[sample].index.values.tolist(),
		'sample_values':  df[sample].values.tolist()
        }]
    return jsonify(data)
if __name__ == "__main__":    
    app.run()
