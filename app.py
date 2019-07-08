import argparse
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import PyPDF2
import re
import seaborn as sns

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('-pdf', default=None)
parser.add_argument('-text', default=None)
parser.add_argument('-start', type=int, default=0)
parser.add_argument('-end', type=int, default=0)
parser.add_argument('-save', action='store_true')
args = parser.parse_args()

# load data
if os.path.exists('dissertation_dates.json'):
    store = json.load(open('dissertation_dates.json','rb'))
else:
    store = {}

dates = []
if args.pdf:
    name=args.pdf
    # load pdf
    file = open(args.pdf, 'rb')
    fileReader = PyPDF2.PdfFileReader(file)
    
    page_start = args.start
    page_end = args.end
    pages = []
    for page_num in range(page_start-1, page_end):
        page = fileReader.getPage(page_num).extractText()
        pages.append(page)
        dates += re.findall('\(((?:19|20)\d\d)', page)
    
    print('*'*79)
    print('First page indexed: ')
    print('*'*79)
    print(pages[0])
    print('\n'+'*'*79)
    print('Last page indexed: ')
    print('*'*79)
    print(pages[-1])
    
elif args.text:
    name = args.text    
    text = '\n'.join(open(args.text, 'r').readlines())
    dates += re.findall('\(((?:19|20)\d\d)', text)
    
# convert dates
dates = [int(i) for i in dates]
if len(dates) == 0:
    print('Something went wrong, no dates found! Ending program')
    exit()
store[name] = dates

# get background
averages = []
all_dates = []
for key, val in store.items():
    averages.append(np.median(val))
    all_dates += val

# get cdfs
min_date = np.min([np.min(x) for x in store.values()])
max_date = np.max([np.max(x) for x in store.values()])
date_bins = np.linspace(min_date, max_date, 40)
cdfs = {}
for key,val in store.items():
    values, base = np.histogram(val, bins=date_bins)
    #evaluate the cumulative
    cumulative = np.cumsum(values) 
    cdfs[key] = cumulative/np.sum(cumulative)
    
if args.save:
    json.dump(store, open('dissertation_dates.json','w'))

colors = ['r','b']
sns.set_context('poster')
size=12
f = plt.figure(figsize=(size, size*.66))
context_ax = f.add_axes([0,.1,.5,.4])
current_ax = f.add_axes([0,.55,.5,.4])
cum_ax = f.add_axes([.55,.1,.45,.8])

# plot date distributions
sns.distplot(dates, ax=current_ax, bins=20, 
             hist_kws={'rwidth':.9}, color=colors[0])
sns.distplot(all_dates, ax=context_ax, bins=20, 
             hist_kws={'rwidth':.9}, color=colors[1])
# plot date averages
sns.rugplot(averages, ax=context_ax, color='k')
# plot CDFs
for key,val in cdfs.items():
    if key == name:
        cum_ax.plot(date_bins[:-1], val, color=colors[0], zorder=10)
    else:
        cum_ax.plot(date_bins[:-1], val, color=colors[1], alpha=.5)
    

# set up axes
current_ax.tick_params(bottom=False, labelbottom=False,
                       labelleft=False, left=False)
context_ax.tick_params(labelleft=False, left=False)
cum_ax.tick_params(labelleft=False, left=False)
sns.despine(ax=current_ax, offset=size, left=True)
sns.despine(ax=context_ax, offset=size, left=True)
sns.despine(ax=cum_ax, offset=size, left=True)
context_ax.invert_yaxis()

# set xaxis
x_min = min(current_ax.get_xlim()[0], context_ax.get_xlim()[0])
x_max = min(current_ax.get_xlim()[1], context_ax.get_xlim()[1])
current_ax.set_xlim(x_min, x_max)
context_ax.set_xlim(x_min, x_max)
cum_ax.set_xlim(x_min, x_max)

# add legends
current_ax.text(.2,.8, 'Current Dissertation', fontsize=size*1.5,
                transform=current_ax.transAxes, color=colors[0])
context_ax.text(.2,.2, 'All Dissertations', fontsize=size*1.5,
                transform=context_ax.transAxes, color=colors[1])
cum_ax.text(.2,.8, 'Date CDFs', fontsize=size*1.5,
                transform=cum_ax.transAxes, color='k')
plt.show()


"""
#can't figure this out

text=text.replace('\n','')
match = re.search(match_str, text)
match.groups()
last_sure_letter = text.index(match.group(4))+len(match.group(4))
text = text[last_sure_letter:]
    
while True:
    match = re.match(match_str, text.replace('\n',''))
    match.groups()
    #re.match(r'.*\s(.*,\s?).*', a).group(1)
    group = match.groups()
    
    citations.append(match.groups())
    last_sure_letter = text.index(match.group(4))+len(match.group(4))
    text = text[last_sure_letter:]
"""


