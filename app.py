import argparse
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import re
import seaborn as sns
import textwrap

# helper functions
def get_display_title(txt, max_length=30):
    wrapped = textwrap.wrap(txt, max_length, break_long_words=False)
    return '\n'.join(wrapped)

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('-focus_file', default=None)
parser.add_argument('-relative', action='store_true')
args = parser.parse_args()

meta = json.load(open('dissertation_refs/meta.json','r'))
relative_date = args.relative

to_delete = []
focused = 0
for i,entry in enumerate(meta):
    try:
        filey = open(os.path.join('dissertation_refs', entry['file']), 'r')
    except FileNotFoundError:
        print("Something went wrong, couldn't find %s" % entry['file'])
        to_delete.append(i)
        continue
    text = '\n'.join(filey.readlines())
    dates = re.findall('\(((?:19|20)\d\d)', text)
    if len(dates) == 0:
        print('Something went wrong, no dates found for %s' % entry['file'])
        to_delete.append(i)
    else:
        
        if relative_date:
            pub_date = int(entry['date'][-4:])
            f = lambda x: int(x)-pub_date
            entry['dates'] = list(map(f, dates))
        else:
            entry['dates'] = list(map(int, dates))
    if entry['file'] == args.focus_file:
        focused = i

for i in to_delete[::-1]:
    del meta[i]
    
# get date range
min_date = np.min([np.min(x['dates']) for x in meta])
max_date = np.max([np.max(x['dates']) for x in meta])
date_bins = np.linspace(min_date, max_date, 40)

# summaries
averages = []
all_dates = []
cdfs = []
for entry in meta:
    # get avererage
    averages.append(np.median(entry['dates']))
    all_dates += entry['dates']
    # get cdf
    values, base = np.histogram(entry['dates'], bins=date_bins)
    #evaluate the cumulative
    cumulative = np.cumsum(values) 
    cdfs.append(cumulative/np.sum(cumulative))
    
# additional changes
df = pd.DataFrame(meta)
df.loc[:,'cite_count'] = df.dates.apply(len)

# plot
colors = ['r','b']
sns.set_context('poster')
size=15
f = plt.figure(figsize=(size, size*.5))
context_ax = f.add_axes([0,.1,.4,.4])
current_ax = f.add_axes([0,.55,.4,.4])
cum_ax = f.add_axes([.425,.1,.3,.85])
num_ax = f.add_axes([.75,.1,.25,.3])
misc_ax = f.add_axes([.8,.55,.2,.4])

# plot date distributions
sns.distplot(meta[focused]['dates'], ax=current_ax, bins=20, 
             hist_kws={'rwidth':.9}, color=colors[0])
sns.distplot(all_dates, ax=context_ax, bins=20, 
             hist_kws={'rwidth':.9}, color=colors[1])
# plot number of citationd distribution
num_cites = [len(x['dates']) for x in meta]
sns.distplot(num_cites, ax=num_ax, kde=False,
             hist_kws={'rwidth':.9})
sns.boxplot('area', 'cite_count', data=df, ax=misc_ax)

# plot date averages
sns.rugplot(averages, ax=context_ax, color='k')
# plot CDFs
for i, cdf in enumerate(cdfs):
    if i == focused:
        cum_ax.plot(date_bins[:-1], cdf, color=colors[0], zorder=10)
    else:
        cum_ax.plot(date_bins[:-1], cdf, color=colors[1], alpha=.3)
    

# set up axes
current_ax.tick_params(bottom=False, labelbottom=False,
                       labelleft=False, left=False)
context_ax.tick_params(labelleft=False, left=False, labelsize=size*1.5)
cum_ax.tick_params(labelleft=False, left=False, labelsize=size*1.5)
num_ax.tick_params(labelleft=False, left=False, labelsize=size*1.5)
misc_ax.tick_params(bottom=False, labelbottom=False, 
                    labelsize=size*1.5,
                    length=size/2, width=1)
context_ax.invert_yaxis()
for ax in f.get_axes():
    sns.despine(ax=ax, offset=size, left=True)

# set xaxis
x_min = min(current_ax.get_xlim()[0], context_ax.get_xlim()[0])
x_max = min(current_ax.get_xlim()[1], context_ax.get_xlim()[1])
current_ax.set_xlim(x_min, x_max)
context_ax.set_xlim(x_min, x_max)
cum_ax.set_xlim(x_min, x_max)

# set xlabels
if relative_date:
    label = 'Date relative to publication'
else:
    label = 'Date'
context_ax.set_xlabel(label, fontsize=size*2)
cum_ax.set_xlabel(label, fontsize=size*2)
num_ax.set_xlabel('# of Citations', fontsize=size*2)

# set ylabels
misc_ax.set_ylabel('# of Citations', fontsize=size*2)

# add legends
current_ax.text(.2,.8, 'Focused Dissertation', fontsize=size*1.5,
                transform=current_ax.transAxes, color=colors[0])
current_ax.text(.2,.7, get_display_title(meta[focused]['title']), 
                fontsize=size*1.25,
                transform=current_ax.transAxes, color=colors[0], va='top')
context_ax.text(.2,.2, 'All Dissertations', fontsize=size*1.5,
                transform=context_ax.transAxes, color=colors[1])
cum_ax.text(.2,.8, 'Date CDFs', fontsize=size*1.5,
                transform=cum_ax.transAxes, color='k')
cum_ax.set_title('Distribution of Dissertation Dates',
          fontweight='bold', fontsize=size*2, y=1.1)
f.tight_layout()
plt.show()

