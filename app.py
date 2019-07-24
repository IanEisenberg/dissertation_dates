import argparse
import json
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import re
import seaborn as sns
import textwrap

# helper functions
def get_display_title(entry, max_length=30):
    txt = entry['title'] + ': %s refs' % len(entry['dates'])
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
        pub_date = int(entry['date'][-4:])
        if relative_date:
            f = lambda x: int(x)-pub_date
            entry['dates'] = list(map(f, dates))
        else:
            entry['dates'] = list(map(int, dates))
        entry['dates'] = [d for d in entry['dates'] if d <= pub_date]
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

# change area names
area_conversion = {name:name.upper()[0] for name in df.area.unique()}
df.area.replace(area_conversion, inplace=True)

# plot
colors = [np.array([230,159,0])/255,
          np.array([86,180,233])/255,
          np.array([0,114,178])/255]
sns.set_context('poster')
size=15
f = plt.figure(figsize=(size, size*.5))
diff_ax = f.add_axes([0,.1,.4,.8])
context_ax = f.add_axes([0,.1,.4,.4])
current_ax = f.add_axes([0,.5,.4,.4])
cum_ax = f.add_axes([.425,.1,.28,.85])
num_ax = f.add_axes([.75,.1,.25,.3])
misc_ax = f.add_axes([.8,.55,.2,.4])


# plot date distributions
min_date = math.floor(np.min(all_dates)/5)*5
max_date = math.ceil(np.max(all_dates)/5)*5
bins = range(min_date, max_date, 5)

current_bins = current_ax.hist(meta[focused]['dates'], bins=bins, color=colors[0], rwidth=.9)
context_bins = context_ax.hist(all_dates, bins=bins, color=colors[1], rwidth=.9)

# get normalized difference and plot
normed_diff = current_bins[0]/sum(current_bins[0]) - context_bins[0]/sum(context_bins[0])
diff_ax.bar(current_bins[1][:-1]+2.5,normed_diff*-1, width=4.3, alpha=.2, color='k')
diff_ax.set_ylim([-np.max(abs(normed_diff)), np.max(abs(normed_diff))])

# plot number of citationd distribution
num_cites = [len(x['dates']) for x in meta]
num_ax.hist(num_cites, rwidth=.9, color=colors[2], bins=len(num_cites)//5)
sns.boxplot('area', 'cite_count', data=df, ax=misc_ax, palette=sns.hls_palette())

# plot date averages
sns.rugplot(averages, ax=cum_ax, color='k')
# plot CDFs
for i, cdf in enumerate(cdfs):
    if i == focused:
        cum_ax.plot(date_bins[:-1], cdf, color=colors[0], zorder=10)
    else:
        cum_ax.plot(date_bins[:-1], cdf, color=colors[1], alpha=.2)
    

# set up axes
current_ax.patch.set_facecolor('None')
context_ax.patch.set_facecolor('None')

current_ax.tick_params(bottom=False, labelbottom=False,
                       labelleft=False, left=False)
context_ax.tick_params(labelleft=False, left=False, labelsize=size*1.5)
cum_ax.tick_params(labelleft=False, left=False, labelsize=size*1.5)
num_ax.tick_params(labelleft=False, left=False, labelsize=size*1.5)
misc_ax.tick_params(labelsize=size*1.5,
                    length=size/2, width=1)
context_ax.invert_yaxis()
for ax in f.get_axes():
    sns.despine(ax=ax, offset=size, left=True)
sns.despine(ax=current_ax, bottom=True, left=True)

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
current_ax.text(.1,.8, 'Focused Dissertation', fontsize=size*1.5,
                transform=current_ax.transAxes, color=colors[0])
current_ax.text(.1,.7, get_display_title(meta[focused]), 
                fontsize=size*1.25,
                transform=current_ax.transAxes, color=colors[0], va='top')
context_ax.text(.1,.2, 'All Dissertations', fontsize=size*1.5,
                transform=context_ax.transAxes, color=colors[1])
cum_ax.text(.2,.8, 'Date CDFs', fontsize=size*1.5,
                transform=cum_ax.transAxes, color='k')
cum_ax.set_title('Distribution of Dissertation Dates',
          fontweight='bold', fontsize=size*2, y=1.1)
f.tight_layout()
plt.show()

