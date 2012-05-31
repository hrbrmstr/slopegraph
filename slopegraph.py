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
# 2012-05-29 - 0.6 - Value labels now align; Added object colors; Changed example to use serif
# 2012-05-30 - 0.7 - Corrected slope start/end points; calculates label widths accurately now
#                    Also tossed in some data set "anomalies" for testing purposes
#

import csv
import cairo

# original data source: http://www.calvin.edu/~stob/data/television.csv

# get a CSV file to work with 

slopeReader = csv.reader(open('television.csv', 'rb'), delimiter=',', quotechar='"')

starts = {} # starting "points"/
ends = {} # ending "points"

# setup line width and font-size for the Cairo
# you can change these and the constants should
# scale the plots accordingly

FONT_SIZE = 20
LINE_WIDTH = 0.5

# setup some more constants for plotting
# all of these are malleable and should cascade nicely

X_MARGIN = 20
Y_MARGIN = 30
SLOPEGRAPH_CANVAS_SIZE = 300
spaceWidth = FONT_SIZE / 2.0
LINE_HEIGHT = FONT_SIZE + (FONT_SIZE / 2.0)
PLOT_LINE_WIDTH = 0.5

# colors

LAB_R = (140.0/255.0)
LAB_G = (31.0/255.0)
LAB_B = (40.0/255.0)

VAL_R = (198.0/255.0)
VAL_G = (107.0/255.0)
VAL_B = (26.0/255.0)

LINE_R = (198.0/255.0)
LINE_G = (182.0/255.0)
LINE_B = (180.0/255.0)

BG_R = (254.0/255.0)
BG_G = (249.0/255.0)
BG_B = (229.0/255.0)

# build a base pair array for the final plotting

pairs = []

for row in slopeReader:

	# add chosen values (need start/end for each CSV row)
	# to the final plotting array. Try this sample with 
	# row[1] (average life span) instead of row[5] to see some
	# of the scaling in action
	
	lab = row[0] # label
	beg = float(row[5]) # male life span
	end = float(row[4]) # female life span
	
	pairs.append( (float(beg), float(end)) )

	# combine labels of common values into one string

	if beg in starts:
		starts[beg] = starts[beg] + "; " + lab
	else:
		starts[beg] = lab
	

	if end in ends:
		ends[end] = ends[end] + "; " + lab
	else:
		ends[end] = lab
			

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

sWidth = 0
eWidth = 0

# there has to be a better way to get a base "surface"
# to do font calculations besides this. we're just making
# this Cairo surface to we know the max pixel width 
# (font extents) of the labels in order to scale the graph
# accurately (since width/height are based, in part, on it)

#filename = 'slopegraph.ps'
filename = 'slopegraph.pdf'
#surface = cairo.PSSurface (filename, 8.5*72, 11*72)
#surface.set_eps(True)
surface = cairo.PDFSurface (filename, 8.5*72, 11*72)
cr = cairo.Context (surface)
cr.save()
cr.select_font_face("Serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
cr.set_font_size(FONT_SIZE)
cr.set_line_width(LINE_WIDTH)

# find the *real* maximum label width (not just based on number of chars)

maxLabelWidth = 0
maxNumWidth = 0

for k in sorted(startKeys):
	s1 = starts[k]
	xbearing, ybearing, sWidth, sHeight, xadvance, yadvance = (cr.text_extents(s1))
	if (sWidth > maxLabelWidth) : maxLabelWidth = sWidth
	xbearing, ybearing, startMaxLabelWidth, startMaxLabelHeight, xadvance, yadvance = (cr.text_extents(str(k)))
	if (startMaxLabelWidth > maxNumWidth) : maxNumWidth = startMaxLabelWidth

sWidth = maxLabelWidth

maxWidth = 0
maxNumWidth = 0

for k in sorted(endKeys):
	e1 = ends[k]
	xbearing, ybearing, eWidth, eHeight, xadvance, yadvance = (cr.text_extents(e1))
	if (eWidth > maxLabelWidth) : maxLabelWidth = eWidth
	xbearing, ybearing, endMaxLabelWidth, endMaxLabelHeight, xadvance, yadvance = (cr.text_extents(str(k)))
	if (endMaxLabelWidth > maxNumWidth) : maxNumWidth = endMaxLabelWidth

eWidth = maxLabelWidth
	

cr.restore()
cr.show_page()
surface.finish()

width = X_MARGIN + sWidth + spaceWidth + startMaxLabelWidth + spaceWidth + SLOPEGRAPH_CANVAS_SIZE + spaceWidth + endMaxLabelWidth + spaceWidth + eWidth + X_MARGIN ;
height = (Y_MARGIN * 2) + (((highest - lowest + 1) / delta) * LINE_HEIGHT)

# create the real Cairo surface/canvas

filename = 'slopegraph.pdf'
#filename = 'slopegraph.ps'
surface = cairo.PDFSurface (filename, width, height)
#surface = cairo.PSSurface (filename, width, height)
#surface.set_eps(True)
cr = cairo.Context (surface)

cr.save()

cr.select_font_face("Serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
cr.set_font_size(FONT_SIZE)

cr.set_line_width(LINE_WIDTH)

cr.set_source_rgb(BG_R,BG_G,BG_B)
cr.rectangle(0,0,width,height)
cr.fill()

# draw start labels at the correct positions

for k in sorted(startKeys):

	label = starts[k]
	xbearing, ybearing, lWidth, lHeight, xadvance, yadvance = (cr.text_extents(label))
	xbearing, ybearing, kWidth, kHeight, xadvance, yadvance = (cr.text_extents(str(k)))

	val = float(k)

	cr.set_source_rgb(LAB_R,LAB_G,LAB_B)
	cr.move_to(X_MARGIN + (sWidth - lWidth), Y_MARGIN + (highest - val) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.show_text(label)
	
	cr.set_source_rgb(VAL_R,VAL_G,VAL_B)
	cr.move_to(X_MARGIN + sWidth + spaceWidth + (startMaxLabelWidth - kWidth), Y_MARGIN + (highest - val) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.show_text(str(k))
	
	cr.stroke()

# draw end labels at the correct positions

for k in sorted(endKeys):

	label = ends[k]
	xbearing, ybearing, lWidth, lHeight, xadvance, yadvance = (cr.text_extents(label))

	val = float(k)
		
	cr.set_source_rgb(VAL_R,VAL_G,VAL_B)
	cr.move_to(width - X_MARGIN - spaceWidth - eWidth - spaceWidth - endMaxLabelWidth, Y_MARGIN + (highest - val) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.show_text(str(k))

	cr.set_source_rgb(LAB_R,LAB_G,LAB_B)
	cr.move_to(width - X_MARGIN - spaceWidth - eWidth, Y_MARGIN + (highest - val) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.show_text(label)

	cr.stroke()

# do the actual plotting

cr.set_line_width(PLOT_LINE_WIDTH)
cr.set_source_rgb(LINE_R, LINE_G, LINE_B)

for s1,e1 in pairs:
	cr.move_to(X_MARGIN + sWidth + spaceWidth + startMaxLabelWidth + 1.5*spaceWidth, Y_MARGIN + (highest - s1) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.line_to(width - X_MARGIN - eWidth - spaceWidth - endMaxLabelWidth - 1.5*spaceWidth, Y_MARGIN + (highest - e1) * LINE_HEIGHT * (1/delta) + LINE_HEIGHT/2)
	cr.stroke()

cr.restore()
cr.show_page()
surface.finish()

