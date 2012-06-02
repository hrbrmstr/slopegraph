#!/usr/bin/python
#
# slopegraph.py
#
# Author: Bob Rudis (@hrbrmstr)
#
# Basic Python skeleton to do simple two value slopegraphs
#
# Find out more about & download Cairo here: http://cairographics.org/
#
# 2012-05-28 - 0.5.0 - Initial github release. Still needs some polish
# 2012-05-29 - 0.6.0 - Value labels now align; Added object colors; Changed example to use serif
# 2012-05-30 - 0.7.0 - Corrected slope start/end points; calculates label widths accurately now
#                      Also tossed in some data set "anomalies" for testing purposes
# 2012-05-31 - 0.7.1 - New sample data file to play with; new theme sample; formatting tweaks & fixes
#                      Added hashbang; moved font family to variable in prep for refactor
# 2012-06-02 - 0.8.0 - Refactored into a more pythonic format; it's now "config"-file based
#                      (see the README for details) and part of that also allows for sprintf-like
#                      formatting of the value part of the label as well as being able to specify
#                      the theme colors in the standard RGB hex string format. The code now assumes
#                      LABEL,COL1VAL,COL2VAL as the CSV input in preparation for an arbitrary # of
#                      columns (though I suspect 4 might be the most useful max). Without hacking the
#                      code directly, it still only supports PDF output and you'll have to remove the
#                      background fill code if you want a transparent background. Those options are
#                      coming.
#

import csv
import cairo
import argparse
import json
	
def split(input, size):
	return [input[start:start+size] for start in range(0, len(input), size)]

class Slopegraph:

	SLOPEGRAPH_CANVAS_SIZE = 300

	starts = {} # starting "points"
	ends = {} # ending "points"
	pairs = [] # base pair array for the final plotting
	
	def readCSV(self, filename):
	
		slopeReader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"')
	
		for row in slopeReader:
		
			# add chosen values (need start/end for each CSV row) to the final plotting array.
			
			lab = row[0] # label
			beg = float(row[1]) # left vals
			end = float(row[2]) # right vals
			
			self.pairs.append( (float(beg), float(end)) )
		
			# combine labels of common values into one string
		
			if beg in self.starts:
				self.starts[beg] = self.starts[beg] + "; " + lab
			else:
				self.starts[beg] = lab
			
		
			if end in self.ends:
				self.ends[end] = self.ends[end] + "; " + lab
			else:
				self.ends[end] = lab


	def sortKeys(self):
	
		# sort all the values (in the event the CSV wasn't) so
		# we can determine the smallest increment we need to use
		# when stacking the labels and plotting points
		
		self.startSorted = [(k, self.starts[k]) for k in sorted(self.starts)]
		self.endSorted = [(k, self.ends[k]) for k in sorted(self.ends)]
		
		self.startKeys = sorted(self.starts.keys())
		self.delta = max(self.startSorted)
		for i in range(len(self.startKeys)):
			if (i+1 <= len(self.startKeys)-1):
				currDelta = float(self.startKeys[i+1]) - float(self.startKeys[i])
				if (currDelta < self.delta):
					self.delta = currDelta
					
		self.endKeys = sorted(self.ends.keys())
		for i in range(len(self.endKeys)):
			if (i+1 <= len(self.endKeys)-1):
				currDelta = float(self.endKeys[i+1]) - float(self.endKeys[i])
				if (currDelta < self.delta):
					self.delta = currDelta


	def findExtremes(self):
	
		# we also need to find the absolute min & max values
		# so we know how to scale the plots
		
		self.lowest = min(self.startKeys)
		if (min(self.endKeys) < self.lowest) : self.lowest = min(self.endKeys)
		
		self.highest = max(self.startKeys)
		if (max(self.endKeys) > self.highest) : self.highest = max(self.endKeys)
		
		self.delta = float(self.delta)
		self.lowest = float(self.lowest)
		self.highest = float(self.highest)

	
	def calculateExtents(self, filename, format, valueFormatString):
	
		surface = cairo.PDFSurface (filename, 8.5*72, 11*72)
		cr = cairo.Context (surface)
		cr.save()
		cr.select_font_face(self.FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		cr.set_font_size(self.FONT_SIZE)
		cr.set_line_width(self.LINE_WIDTH)
		
		# find the *real* maximum label width (not just based on number of chars)
		
		maxLabelWidth = 0
		maxNumWidth = 0
		
		for k in sorted(self.startKeys):
			s1 = self.starts[k]
			xbearing, ybearing, self.sWidth, self.sHeight, xadvance, yadvance = (cr.text_extents(s1))
			if (self.sWidth > maxLabelWidth) : maxLabelWidth = self.sWidth
			xbearing, ybearing, self.startMaxLabelWidth, startMaxLabelHeight, xadvance, yadvance = (cr.text_extents(valueFormatString % (k)))
			if (self.startMaxLabelWidth > maxNumWidth) : maxNumWidth = self.startMaxLabelWidth
		
		self.sWidth = maxLabelWidth
		self.startMaxLabelWidth = maxNumWidth
		
		maxLabelWidth = 0
		maxNumWidth = 0
		
		for k in sorted(self.endKeys):
			e1 = self.ends[k]
			xbearing, ybearing, self.eWidth, eHeight, xadvance, yadvance = (cr.text_extents(e1))
			if (self.eWidth > maxLabelWidth) : maxLabelWidth = self.eWidth
			xbearing, ybearing, self.endMaxLabelWidth, endMaxLabelHeight, xadvance, yadvance = (cr.text_extents(valueFormatString % (k)))
			if (self.endMaxLabelWidth > maxNumWidth) : maxNumWidth = self.endMaxLabelWidth
		
		self.eWidth = maxLabelWidth
		self.endMaxLabelWidth = maxNumWidth	
		
		cr.restore()
		cr.show_page()
		surface.finish()
		
		self.width = self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + self.startMaxLabelWidth + self.SPACE_WIDTH + self.SLOPEGRAPH_CANVAS_SIZE + self.SPACE_WIDTH + self.endMaxLabelWidth + self.SPACE_WIDTH + self.eWidth + self.X_MARGIN ;
		self.height = (self.Y_MARGIN * 2) + (((self.highest - self.lowest) / self.delta) * self.LINE_HEIGHT)
		
		
	def makeSlopegraph(self, filename, config):
	
		(lab_r,lab_g,lab_b) = split(config["label_color"],2)
		(val_r,val_g,val_b) = split(config["value_color"],2)
		(line_r,line_g,line_b) = split(config["slope_color"],2)
		(bg_r,bg_g,bg_b) = split(config["background_color"],2)
		
		LAB_R = (int(lab_r, 16)/255.0)
		LAB_G = (int(lab_g, 16)/255.0)
		LAB_B = (int(lab_b, 16)/255.0)
		
		VAL_R = (int(val_r, 16)/255.0)
		VAL_G = (int(val_g, 16)/255.0)
		VAL_B = (int(val_b, 16)/255.0)
		
		LINE_R = (int(line_r, 16)/255.0)
		LINE_G = (int(line_g, 16)/255.0)
		LINE_B = (int(line_b, 16)/255.0)
		
		BG_R = (int(bg_r, 16)/255.0)
		BG_G = (int(bg_g, 16)/255.0)
		BG_B = (int(bg_b, 16)/255.0)

		surface = cairo.PDFSurface (filename, self.width, self.height)
		cr = cairo.Context(surface)
		
		cr.save()
		
		cr.select_font_face(self.FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		cr.set_font_size(self.FONT_SIZE)
		
		cr.set_line_width(self.LINE_WIDTH)
		
		cr.set_source_rgb(BG_R,BG_G,BG_B)
		cr.rectangle(0,0,self.width,self.height)
		cr.fill()
		
		# draw start labels at the correct positions
		
		valueFormatString = config["value_format_string"]
		
		for k in sorted(self.startKeys):
		
			val = float(k)
			label = self.starts[k]
			xbearing, ybearing, lWidth, lHeight, xadvance, yadvance = (cr.text_extents(label))
			xbearing, ybearing, kWidth, kHeight, xadvance, yadvance = (cr.text_extents(valueFormatString % (val)))
		
			cr.set_source_rgb(LAB_R,LAB_G,LAB_B)
			cr.move_to(self.X_MARGIN + (self.sWidth - lWidth), self.Y_MARGIN + (self.highest - val) * self.LINE_HEIGHT * (1/self.delta))
			cr.show_text(label)
			
			cr.set_source_rgb(VAL_R,VAL_G,VAL_B)
			cr.move_to(self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + (self.startMaxLabelWidth - kWidth), self.Y_MARGIN + (self.highest - val) * self.LINE_HEIGHT * (1/self.delta))
			cr.show_text(valueFormatString % (val))
			
			cr.stroke()
		
		# draw end labels at the correct positions
		
		for k in sorted(self.endKeys):
		
			val = float(k)
			label = self.ends[k]
			xbearing, ybearing, lWidth, lHeight, xadvance, yadvance = (cr.text_extents(label))
				
			cr.set_source_rgb(VAL_R,VAL_G,VAL_B)
			cr.move_to(self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth - self.SPACE_WIDTH - self.endMaxLabelWidth, self.Y_MARGIN + (self.highest - val) * self.LINE_HEIGHT * (1/self.delta))
			cr.show_text(valueFormatString % (val))
		
			cr.set_source_rgb(LAB_R,LAB_G,LAB_B)
			cr.move_to(self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth, self.Y_MARGIN + (self.highest - val) * self.LINE_HEIGHT * (1/self.delta))
			cr.show_text(label)
		
			cr.stroke()
		
		# do the actual plotting
		
		cr.set_line_width(self.LINE_WIDTH)
		cr.set_source_rgb(LINE_R, LINE_G, LINE_B)
		
		for s1,e1 in self.pairs:
			cr.move_to(self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + self.startMaxLabelWidth + self.LINE_START_DELTA, self.Y_MARGIN + (self.highest - s1) * self.LINE_HEIGHT * (1/self.delta) - self.LINE_HEIGHT/4)
			cr.line_to(self.width - self.X_MARGIN - self.eWidth - self.SPACE_WIDTH - self.endMaxLabelWidth - self.LINE_START_DELTA, self.Y_MARGIN + (self.highest - e1) * self.LINE_HEIGHT * (1/self.delta) - self.LINE_HEIGHT/4)
			cr.stroke()
		
		cr.restore()
		cr.show_page()
		surface.finish()	
		
	
	def __init__(self, config):
	
		# a couple methods need these so make them local to the class
	
		self.FONT_FAMILY = config["font_family"]
		self.LINE_WIDTH = float(config["line_width"])
		self.X_MARGIN = float(config["x_margin"])
		self.Y_MARGIN = float(config["y_margin"])
		self.FONT_SIZE = float(config["font_size"])
		self.SPACE_WIDTH = self.FONT_SIZE / 2.0
		self.LINE_HEIGHT = self.FONT_SIZE + (self.FONT_SIZE / 2.0)
		self.LINE_START_DELTA = 1.5*self.SPACE_WIDTH
		
		OUTPUT_FILE = config["output"] + "." + config["format"]
		
		# process the values & make the slopegraph
		
		self.readCSV(config["input"])
		self.sortKeys()
		self.findExtremes()
		self.calculateExtents(OUTPUT_FILE, config["format"], config["value_format_string"])
		self.makeSlopegraph(OUTPUT_FILE, config)
		

def main():

	parser = argparse.ArgumentParser(description="Creates a slopegraph from a CSV source")
	parser.add_argument("--config",required=True,
					help="config file name to use for  slopegraph creation",)
	args = parser.parse_args()

	if args.config:
	
		json_data = open(args.config)
		config = json.load(json_data)
		json_data.close()
		
		Slopegraph(config)

	return(0)
	
if __name__ == "__main__":
	main()
