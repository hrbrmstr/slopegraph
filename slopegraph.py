# slopegraph.py
#
# Author: Bob Rudis (@hrbrmstr)
#
# Basic Python skeleton to do simple two value slopegraphs
# with output to PDF (most useful form for me...Cairo has tons of options)
#
# Find out more about & download Cairo here:
# http://cairographics.org/
#
# 2012-05-28 - 0.5 - Initial github release. Still needs some polish
# 2012-05-20 - 0.6 - Value labels now align; Added object colors; Changed example to use serif
#

import csv
import cairo

# original data source: http://www.calvin.edu/~stob/data/television.csv

# get a CSV file to work with 

slopeReader = csv.reader(open('television.csv', 'rb'), delimiter=',', quotechar='"')

starts = {} # starting "points"/
ends = {} # ending "points"

# Need to refactor label max width into font calculations
# as there's no guarantee the longest (character-wise)
# label is the widest one

startLabelMaxLen = 0
endLabelMaxLen = 0
begMax = 0
endMax = 0
longestBeg = ""
longestEnd = ""

# build a base pair array for the final plotting
# wastes memory, but simplifies plotting

pairs = []

for row in slopeReader:

	# add chosen values (need start/end for each CSV row)
	# to the final plotting array. Try this sample with 
	# row[1] (average life span) instead of row[5] to see some
	# of the scaling in action
	
	lab = row[0] # label
	beg = row[5] # male life span
	end = row[4] # female life span
	
	pairs.append( (float(beg), float(end)) )

	# combine labels of common values into one string
	# also (as noted previously, inappropriately) find the
	# longest one

	if beg in starts:
		starts[beg] = starts[beg] + "; " + lab
	else:
		starts[beg] = lab
	
	if ((len(starts[beg]) + len(beg)) > startLabelMaxLen):
		startLabelMaxLen = len(starts[beg]) + len(beg)
		s1 = starts[beg]

	if len(beg) > begMax : longestBeg = beg ;


	if end in ends:
		ends[end] = ends[end] + "; " + lab
	else:
		ends[end] = lab
	
	if ((len(ends[end]) + len(end)) > endLabelMaxLen):
		endLabelMaxLen = len(ends[end]) + len(end)
		e1 = ends[end]
		
	if len(end) > endMax : longestEnd = end ;

# sort all the values (in the event the CSV wasn't) so
# we can determine the smallest increment we need to use
# when stacking the labels and plotting points

startSorted = [(k, starts[k]) for k in sorted(starts)]
endSorted = [(k, ends[k]) for k in sorted(ends)]

startKeys = sorted(starts.keys())
delta = max(startSorted)
for i in range(len(startKeys)):
	if (i+1 <= len(startKeys)-1):
		currDelta = float(startKeys[i+1]) - float(startKeys[i])
		if (currDelta < delta):
			delta = currDelta
			
endKeys = sorted(ends.keys())
for i in range(len(endKeys)):
	if (i+1 <= len(endKeys)-1):
		currDelta = float(endKeys[i+1]) - float(endKeys[i])
		if (currDelta < delta):
			delta = currDelta

# we also need to find the absolute min & max values
# so we know how to scale the plots

lowest = min(startKeys)
if (min(endKeys) < lowest) : lowest = min(endKeys)

highest = max(startKeys)
if (max(endKeys) > highest) : highest = max(endKeys)

# just making sure everything's a number
# probably should move some of this to the csv reader section

delta = float(delta)
lowest = float(lowest)
highest = float(highest)
startLabelMaxLen = float(startLabelMaxLen)
endLabelMaxLen = float(endLabelMaxLen)

# setup line width and font-size for the Cairo
# you can change these and the constants should
# scale the plots accordingly

FONT_SIZE = 9
LINE_WIDTH = 0.5

# there has to be a better way to get a base "surface"
# to do font calculations besides this. we're just making
# this Cairo surface to we know the max pixel width 
# (font extents) of the labels in order to scale the graph
# accurately (since width/height are based, in part, on it)

filename = 'slopegraph.pdf'
surface = cairo.PDFSurface (filename, 8.5*72, 11*72)
cr = cairo.Context (surface)
cr.save()
cr.select_font_face("Serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
cr.set_font_size(FONT_SIZE)
cr.set_line_width(LINE_WIDTH)
xbearing, ybearing, sWidth, sHeight, xadvance, yadvance = (cr.text_extents(s1))
xbearing, ybearing, eWidth, eHeight, xadvance, yadvance = (cr.text_extents(e1))
xbearing, ybearing, spaceWidth, spaceHeight, xadvance, yadvance = (cr.text_extents(" "))
xbearing, ybearing, startMaxLabelWidth, startMaxLabelHeioght, xadvance, yadvance = (cr.text_extents(longestBeg))
xbearing, ybearing, endMaxLabelWidth, endMaxLabelHeioght, xadvance, yadvance = (cr.text_extents(longestEnd))
cr.restore()
cr.show_page()
surface.finish()

# setup some more constants for plotting
# all of these are malleable and should cascade nicely

X_MARGIN = 10
Y_MARGIN = 10
SLOPEGRAPH_CANVAS_SIZE = 200
spaceWidth = 5
LINE_HEIGHT = 15
PLOT_LINE_WIDTH = 0.5

width = X_MARGIN + sWidth + spaceWidth + startMaxLabelWidth + spaceWidth + SLOPEGRAPH_CANVAS_SIZE + spaceWidth + endMaxLabelWidth + spaceWidth + eWidth + X_MARGIN ;
height = (Y_MARGIN * 2) + (((highest - lowest + 1) / delta) * LINE_HEIGHT)

# create the real Cairo surface/canvas

filename = 'slopegraph.pdf'
surface = cairo.PDFSurface (filename, width, height)
cr = cairo.Context (surface)

cr.save()

cr.select_font_face("Serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
cr.set_font_size(FONT_SIZE)

cr.set_line_width(LINE_WIDTH)

BG_R = (254.0/255.0)
BG_G = (249.0/255.0)
BG_B = (229.0/255.0)

cr.set_source_rgb(BG_R,BG_G,BG_B)
cr.rectangle(0,0,width,height)
cr.fill()

# draw start labels at the correct positions
# cheating a bit here as the code doesn't (yet) line up 
# the actual data values

LAB_R = (140.0/255.0)
LAB_G = (31.0/255.0)
LAB_B = (40.0/255.0)

VAL_R = (198.0/255.0)
VAL_G = (107.0/255.0)
VAL_B = (26.0/255.0)

for k in sorted(startKeys):

	label = starts[k]
	xbearing, ybearing, lWidth, lHeight, xadvance, yadvance = (cr.text_extents(label))
	xbearing, ybearing, kWidth, kHeight, xadvance, yadvance = (cr.text_extents(k))

	val = float(k)

	cr.set_source_rgb(LAB_R,LAB_G,LAB_B)
	cr.move_to(X_MARGIN + (sWidth - lWidth), Y_MARGIN + (highest - val) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.show_text(label)
	
	cr.set_source_rgb(VAL_R,VAL_G,VAL_B)
	cr.move_to(X_MARGIN + sWidth + spaceWidth + (startMaxLabelWidth - kWidth), Y_MARGIN + (highest - val) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.show_text(k)
	
	cr.stroke()

# draw end labels at the correct positions
# cheating a bit here as the code doesn't (yet) line up 
# the actual data values


for k in sorted(endKeys):

	label = ends[k]
	xbearing, ybearing, lWidth, lHeight, xadvance, yadvance = (cr.text_extents(label))

	val = float(k)
		
	cr.set_source_rgb(VAL_R,VAL_G,VAL_B)
	cr.move_to(width - X_MARGIN - spaceWidth - eWidth - spaceWidth - endMaxLabelWidth, Y_MARGIN + (highest - val) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.show_text(k)

	cr.set_source_rgb(LAB_R,LAB_G,LAB_B)
	cr.move_to(width - X_MARGIN - spaceWidth - eWidth, Y_MARGIN + (highest - val) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.show_text(label)

	cr.stroke()

# do the actual plotting

LINE_R = (198.0/255.0)
LINE_G = (182.0/255.0)
LINE_B = (180.0/255.0)

cr.set_line_width(PLOT_LINE_WIDTH)
cr.set_source_rgb(LINE_R, LINE_G, LINE_B) # need to make this a constant

#width = X_MARGIN + sWidth + spaceWidth + startMaxLabelWidth + spaceWidth + SLOPEGRAPH_CANVAS_SIZE + spaceWidth + endMaxLabelWidth + spaceWidth + eWidth + X_MARGIN ;

for s1,e1 in pairs:
	cr.move_to(X_MARGIN + sWidth + spaceWidth + 20, Y_MARGIN + (highest - s1) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.line_to(width - X_MARGIN - eWidth - spaceWidth - 20, Y_MARGIN + (highest - e1) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.stroke()

cr.restore()
cr.show_page()
surface.finish()

