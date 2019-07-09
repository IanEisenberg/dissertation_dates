import argparse
import json
import matplotlib.pyplot as plt
import numpy as np
import os
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
args = parser.parse_args()

meta = json.load(open('dissertation_refs/meta.json','r'))


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
    


colors = ['r','b']
sns.set_context('poster')
size=8
f = plt.figure(figsize=(size, size*.66))
context_ax = f.add_axes([0,.1,.5,.4])
current_ax = f.add_axes([0,.55,.5,.4])
cum_ax = f.add_axes([.55,.1,.45,.8])

# plot date distributions
sns.distplot(meta[focused]['dates'], ax=current_ax, bins=20, 
             hist_kws={'rwidth':.9}, color=colors[0])
sns.distplot(all_dates, ax=context_ax, bins=20, 
             hist_kws={'rwidth':.9}, color=colors[1])
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
current_ax.text(.2,.8, 'Focused Dissertation', fontsize=size*1.5,
                transform=current_ax.transAxes, color=colors[0])
current_ax.text(.2,.7, get_display_title(meta[focused]['title']), 
                fontsize=size*1.25,
                transform=current_ax.transAxes, color=colors[0], va='top')
context_ax.text(.2,.2, 'All Dissertations', fontsize=size*1.5,
                transform=context_ax.transAxes, color=colors[1])
cum_ax.text(.2,.8, 'Date CDFs', fontsize=size*1.5,
                transform=cum_ax.transAxes, color='k')
plt.title('Distribution of Dissertation Dates',
          fontweight='bold', fontsize=size*2)
f.tight_layout()
plt.show()

