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
# If you do end up using this code, pls send a tweet to @hrbrmstr :-)
# 
########################################################################
#
# Copyright (c) 2012 Bob Rudis, @hrbrmstr, http://rud.is/
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
########################################################################
# 
# 2012-05-28 - 0.5.0 - Initial github release. Still needs some polish
#                      
# 2012-05-29 - 0.6.0 - Value labels now align; Added object colors; 
#                      Changed example to use serif
#                      
# 2012-05-30 - 0.7.0 - Corrected slope start/end points; calculates 
#                      label widths accurately now
#                      Also tossed in some data set "anomalies" for 
#                      testing purposes
#                      
# 2012-05-31 - 0.7.1 - New sample data file to play with; new theme 
#                      sample; formatting tweaks & fixes
#                      Added hashbang; moved font family to variable in 
#                      prep for refactor
#                      
# 2012-06-02 - 0.8.0 - Refactored into a more pythonic format; it's now 
#                      "config"-file based (see the README for details)
#                      and part of that also allows for sprintf-like
#                      formatting of the value part of the label as well 
#                      as being able to specify the theme colors in the 
#                      standard RGB hex string format. The code now
#                      assumes LABEL,COL1VAL,COL2VAL as the CSV input in 
#                      preparation for an arbitrary # of columns (though 
#                      I suspect 4 might be the most useful max). Without 
#                      hacking the code directly, it still only supports 
#                      PDF output and you'll have to remove the background
#                      fill code if you want a transparent background. 
#                      Those options are coming.
#                     
# 2012-06-05 - 0.9.0 - Output to SVG/PS/PDF/PNG ; allow for
#                      "background_color" : "transparent";
#                      Added header labels/theming; added MIT license
#
# 2012-06-05 - 0.9.1 - Bugfix. I keep forgetting Python isn't as cool as
#                      Perl when it comes to dictionaries/associative arrays
#
# 2012-06-05 - 0.9.2 - Tweaked config files; created Makefile (for
#                      examples); added "slope_up_color" &
#                      "slope_down_color" configuration options and a
#                      new test config
#
# 2012-06-06 - 0.9.3 - Changed main class name to "PySlopegraph";
#                      added "log_scale" option to use log scales for 
#                      slopegraph axes; added "round_precision" option 
#                      to make it  easier to "play" with axes value scaling
#
# 2012-06-08 - 0.9.4 - Experimental Raphael support (http://raphaeljs.com/)
#

import csv
import cairo
import argparse
import json
import math

NULL_PATH = "/dev/null"

def split(input, size):
	return [input[start:start+size] for start in range(0, len(input), size)]

class PySlopegraph:

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
			
			if self.ROUND_PRECISION != None:
				beg = round(beg,self.ROUND_PRECISION)
				end = round(end,self.ROUND_PRECISION)
			
			self.pairs.append( (float(beg), float(end), (float(end) - float(beg))) )
		
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

				if self.LOG_SCALE:
					currDelta = math.log(float(self.startKeys[i+1])) - math.log(float(self.startKeys[i]))
				else:
					currDelta = float(self.startKeys[i+1]) - float(self.startKeys[i])

				if (currDelta < self.delta): self.delta = currDelta
					
		self.endKeys = sorted(self.ends.keys())
		for i in range(len(self.endKeys)):
		
			if (i+1 <= len(self.endKeys)-1):

				if self.LOG_SCALE:
					currDelta = math.log(float(self.endKeys[i+1])) - math.log(float(self.endKeys[i]))
				else:
					currDelta = float(self.endKeys[i+1]) - float(self.endKeys[i])
				
				if (currDelta < self.delta): self.delta = currDelta


	def findExtremes(self):
	
		# we also need to find the absolute min & max values
		# so we know how to scale the plots
				
		if self.LOG_SCALE:
			self.lowest = math.log(min(self.startKeys))
			if (math.log(min(self.endKeys)) < self.lowest) : self.lowest = math.log(min(self.endKeys))
			
			self.highest = math.log(max(self.startKeys))
			if (math.log(max(self.endKeys)) > self.highest) : self.highest = math.log(max(self.endKeys))
		else:
			self.lowest = min(self.startKeys)
			if (min(self.endKeys) < self.lowest) : self.lowest = min(self.endKeys)
			
			self.highest = max(self.startKeys)
			if (max(self.endKeys) > self.highest) : self.highest = max(self.endKeys)
			
		self.delta = float(self.delta)
		self.lowest = float(self.lowest)
		self.highest = float(self.highest)
	
	def calculateExtents(self, filename, format, valueFormatString):
	
		if (format == "pdf"):
			surface = cairo.PDFSurface (filename, self.TMP_W, self.TMP_H)
		elif (format == "ps"):
			surface = cairo.PSSurface(filename, self.TMP_W, self.TMP_H)
			surface.set_eps(True)
		elif (format == "svg"):
			surface = cairo.SVGSurface (filename, self.TMP_W, self.TMP_H)
		elif (format == "png"):
			surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, int(self.TMP_W), int(self.TMP_H))
		elif (format == "js"):
			surface = cairo.SVGSurface (NULL_PATH, self.TMP_W, self.TMP_H)
		else:
			surface = cairo.PDFSurface (filename, self.TMP_W, self.TMP_H)

		cr = cairo.Context(surface)
		cr.save()
		cr.select_font_face(self.LABEL_FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		cr.set_font_size(self.LABEL_FONT_SIZE)
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
		
		self.width = self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + self.startMaxLabelWidth + self.SPACE_WIDTH + self.SLOPE_LENGTH + self.SPACE_WIDTH + self.endMaxLabelWidth + self.SPACE_WIDTH + self.eWidth + self.X_MARGIN ;
		self.height = (self.Y_MARGIN * 2) + (((self.highest - self.lowest) / self.delta) * self.LINE_HEIGHT)
		
		self.HEADER_SPACE = 0.0
		if (self.HEADER_FONT_FAMILY != None):
			self.HEADER_SPACE = self.HEADER_FONT_SIZE + 2*self.LINE_HEIGHT
			self.height += self.HEADER_SPACE
		
		
	def makeSlopegraph(self, filename, config):
	
		(lab_r,lab_g,lab_b) = split(self.LABEL_COLOR,2)		
		LAB_R = (int(lab_r, 16)/255.0)
		LAB_G = (int(lab_g, 16)/255.0)
		LAB_B = (int(lab_b, 16)/255.0)
		
		(val_r,val_g,val_b) = split(self.VALUE_COLOR,2)
		VAL_R = (int(val_r, 16)/255.0)
		VAL_G = (int(val_g, 16)/255.0)
		VAL_B = (int(val_b, 16)/255.0)
		
		(line_r,line_g,line_b) = split(self.SLOPE_COLOR,2)
		LINE_R = (int(line_r, 16)/255.0)
		LINE_G = (int(line_g, 16)/255.0)
		LINE_B = (int(line_b, 16)/255.0)
		
		(line_up_r,line_up_g,line_up_b) = split(self.SLOPE_UP_COLOR,2)
		LINE_UP_R = (int(line_up_r, 16)/255.0)
		LINE_UP_G = (int(line_up_g, 16)/255.0)
		LINE_UP_B = (int(line_up_b, 16)/255.0)
		
		(line_down_r,line_down_g,line_down_b) = split(self.SLOPE_DOWN_COLOR,2)
		LINE_DOWN_R = (int(line_down_r, 16)/255.0)
		LINE_DOWN_G = (int(line_down_g, 16)/255.0)
		LINE_DOWN_B = (int(line_down_b, 16)/255.0)
		
		if (self.BACKGROUND_COLOR != "transparent"):
			(bg_r,bg_g,bg_b) = split(self.BACKGROUND_COLOR,2)
			BG_R = (int(bg_r, 16)/255.0)
			BG_G = (int(bg_g, 16)/255.0)
			BG_B = (int(bg_b, 16)/255.0)

		if (config['format'] == "pdf"):
			surface = cairo.PDFSurface (filename, self.width, self.height)
		elif (config['format'] == "ps"):
			surface = cairo.PSSurface(filename, self.width, self.height)
			surface.set_eps(True)
		elif (config['format'] == "svg"):
			surface = cairo.SVGSurface (filename, self.width, self.height)
		elif (config['format'] == "js"):
			surface = cairo.SVGSurface (NULL_PATH, self.width, self.height)
			paper = """
<html>
   <head>
        <title></title>
        <script type="text/javascript" src="raphael-min.js"></script>
        <style type="text/css">
            #surface {
                width: %d;
            }
        </style>
        <script>
			window.onload = function() {  
			
				var surface = new Raphael(document.getElementById('surface'), %d, %d);
				var headers = new Array();
				var lines = new Array();
				var labels = new Array() ;
				var values = new Array() ;
""" % (self.width, self.width, self.height)

		elif (config['format'] == "png"):
			surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, int(self.width), int(self.height))
		else:
			surface = cairo.PDFSurface (filename, self.width, self.height)
			
		cr = cairo.Context(surface)
		
		cr.save()
		
		cr.set_line_width(self.LINE_WIDTH)

		if (self.BACKGROUND_COLOR != "transparent"):
			cr.set_source_rgb(BG_R,BG_G,BG_B)
			cr.rectangle(0,0,self.width,self.height)
			cr.fill()
			if (config['format'] == 'js'):
				paper += "				surface.rect(0,0,%s,%s).attr({fill:'#%s',stroke:'#%s'});\n" % (self.width,self.height,self.BACKGROUND_COLOR,self.BACKGROUND_COLOR)
			
		# draw headers (if present)
		
		if (self.HEADER_FONT_FAMILY != None):
			
			(header_r,header_g,header_b) = split(self.HEADER_COLOR,2)		
			HEADER_R = (int(header_r, 16)/255.0)
			HEADER_G = (int(header_g, 16)/255.0)
			HEADER_B = (int(header_b, 16)/255.0)
			
			cr.save()
			
			cr.select_font_face(self.HEADER_FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
			cr.set_font_size(self.HEADER_FONT_SIZE)
			cr.set_source_rgb(HEADER_R,HEADER_G,HEADER_B)
			
			xbearing, ybearing, hWidth, hHeight, xadvance, yadvance = (cr.text_extents(config["labels"][0]))			
			cr.move_to(self.X_MARGIN + self.sWidth - hWidth, self.Y_MARGIN + self.HEADER_FONT_SIZE)
			cr.show_text(config["labels"][0])
			
			xbearing, ybearing, hWidth, hHeight, xadvance, yadvance = (cr.text_extents(config["labels"][1]))			
			cr.move_to(self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth, self.Y_MARGIN + self.HEADER_FONT_SIZE)
			cr.show_text(config["labels"][1])
	
			cr.stroke()
	
			cr.restore()
			
			if (config['format'] == 'js'):
				paper += "				headers[0] = surface.text(%d, %d, '%s').attr({'font':'%spx %s','font-family':'%s','font-size':'%d','font-weight':'bold','fill':'#%s','text-anchor':'end'});\n" % (self.X_MARGIN + self.sWidth, self.Y_MARGIN + self.HEADER_FONT_SIZE, config["labels"][0], self.HEADER_FONT_SIZE, self.HEADER_FONT_FAMILY, self.HEADER_FONT_FAMILY, self.HEADER_FONT_SIZE, self.HEADER_COLOR)
				paper += "				headers[1] = surface.text(%d, %d, '%s').attr({'font':'%spx %s','font-family':'%s','font-size':'%d','font-weight':'bold','fill':'#%s','text-anchor':'start'});\n" % (self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth, self.Y_MARGIN + self.HEADER_FONT_SIZE, config["labels"][1], self.HEADER_FONT_SIZE, self.HEADER_FONT_FAMILY, self.HEADER_FONT_FAMILY, self.HEADER_FONT_SIZE,self.HEADER_COLOR)

				
		# draw start labels at the correct positions
		
		cr.select_font_face(self.LABEL_FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		cr.set_font_size(self.LABEL_FONT_SIZE)
		
		valueFormatString = config["value_format_string"]
		
		for k in sorted(self.startKeys):
		
			val = float(k)
			label = self.starts[k]
			xbearing, ybearing, lWidth, lHeight, xadvance, yadvance = (cr.text_extents(label))
			xbearing, ybearing, kWidth, kHeight, xadvance, yadvance = (cr.text_extents(valueFormatString % (val)))
		
			cr.set_source_rgb(LAB_R,LAB_G,LAB_B)
			if self.LOG_SCALE:
				cr.move_to(self.X_MARGIN + (self.sWidth - lWidth), self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(val)) * self.LINE_HEIGHT * (1/self.delta))
				if (config['format'] == 'js'):
					paper += "				surface.text(%d, %d, '%s').attr({'font':'%dpx %s','font-family':'%s','font-size':'%d','fill':'#%s','text-anchor':'end'});\n" % (self.X_MARGIN + self.sWidth , self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(val)) * self.LINE_HEIGHT * (1/self.delta), label, self.LABEL_FONT_SIZE, self.LABEL_FONT_FAMILY, self.LABEL_FONT_FAMILY, self.LABEL_FONT_SIZE, self.LABEL_COLOR)
			else:
				cr.move_to(self.X_MARGIN + (self.sWidth - lWidth), self.Y_MARGIN + self.HEADER_SPACE + (self.highest - val) * self.LINE_HEIGHT * (1/self.delta))
				if (config['format'] == 'js'):
					paper += "				surface.text(%d, %d, '%s').attr({'font':'%dpx %s','font-family':'%s','font-size':'%d','fill':'#%s','text-anchor':'end'});\n" % (self.X_MARGIN + self.sWidth, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - val) * self.LINE_HEIGHT * (1/self.delta), label, self.LABEL_FONT_SIZE, self.LABEL_FONT_FAMILY, self.LABEL_FONT_FAMILY, self.LABEL_FONT_SIZE, self.LABEL_COLOR)
			cr.show_text(label)
			
			cr.set_source_rgb(VAL_R,VAL_G,VAL_B)
			if self.LOG_SCALE:
				cr.move_to(self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + (self.startMaxLabelWidth - kWidth), self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(val)) * self.LINE_HEIGHT * (1/self.delta))
				if (config['format'] == 'js'):
					paper += "				surface.text(%d, %d, '%s').attr({'font':'%dpx %s','font-family':'%s','font-size':'%d','fill':'#%s','text-anchor':'end'});\n" % (self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + self.startMaxLabelWidth, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(val)) * self.LINE_HEIGHT * (1/self.delta), (valueFormatString % (val)), self.LABEL_FONT_SIZE, self.LABEL_FONT_FAMILY, self.LABEL_FONT_FAMILY, self.LABEL_FONT_SIZE, self.VALUE_COLOR)
			else:
				cr.move_to(self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + (self.startMaxLabelWidth - kWidth), self.Y_MARGIN + self.HEADER_SPACE + (self.highest - val) * self.LINE_HEIGHT * (1/self.delta))
				if (config['format'] == 'js'):
					paper += "				surface.text(%d, %d, '%s').attr({'font':'%dpx %s','font-family':'%s','font-size':'%d','fill':'#%s','text-anchor':'end'});\n" % (self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + self.startMaxLabelWidth , self.Y_MARGIN + self.HEADER_SPACE + (self.highest - (val)) * self.LINE_HEIGHT * (1/self.delta), (valueFormatString % (val)), self.LABEL_FONT_SIZE, self.LABEL_FONT_FAMILY, self.LABEL_FONT_FAMILY, self.LABEL_FONT_SIZE, self.VALUE_COLOR)
			cr.show_text(valueFormatString % (val))
			
			cr.stroke()
		
		# draw end labels at the correct positions
		
		for k in sorted(self.endKeys):
		
			val = float(k)
			label = self.ends[k]
			xbearing, ybearing, lWidth, lHeight, xadvance, yadvance = (cr.text_extents(label))
				
			cr.set_source_rgb(VAL_R,VAL_G,VAL_B)
			if self.LOG_SCALE:
				cr.move_to(self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth - self.SPACE_WIDTH - self.endMaxLabelWidth, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(val)) * self.LINE_HEIGHT * (1/self.delta))
				if (config['format'] == 'js'):
					paper += "				surface.text(%d, %d, '%s').attr({'font':'%dpx %s','font-family':'%s','font-size':%s,'fill':'#%s','text-anchor':'start'});\n" % (self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth - self.SPACE_WIDTH - self.endMaxLabelWidth, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(val)) * self.LINE_HEIGHT * (1/self.delta), (valueFormatString % (val)), self.LABEL_FONT_SIZE, self.LABEL_FONT_FAMILY, self.LABEL_FONT_FAMILY, self.LABEL_FONT_SIZE, self.VALUE_COLOR)
			else:
				cr.move_to(self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth - self.SPACE_WIDTH - self.endMaxLabelWidth, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - val) * self.LINE_HEIGHT * (1/self.delta))
				if (config['format'] == 'js'):
					paper += "				surface.text(%d, %d, '%s').attr({'font':'%dpx %s','font-family':'%s','font-size':%s,'fill':'#%s','text-anchor':'start'});\n" % (self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth - self.SPACE_WIDTH - self.endMaxLabelWidth, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - val) * self.LINE_HEIGHT * (1/self.delta), (valueFormatString % (val)), self.LABEL_FONT_SIZE, self.LABEL_FONT_FAMILY, self.LABEL_FONT_FAMILY, self.LABEL_FONT_SIZE, self.VALUE_COLOR)
			cr.show_text(valueFormatString % (val))
		
			cr.set_source_rgb(LAB_R,LAB_G,LAB_B)
			if self.LOG_SCALE:
				cr.move_to(self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(val)) * self.LINE_HEIGHT * (1/self.delta))
				if (config['format'] == 'js'):
					paper += "				surface.text(%d, %d, '%s').attr({'font':'%dpx %s','font-family':'%s','font-size':%s,'fill':'#%s','text-anchor':'start'});\n" % (self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth , self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(val)) * self.LINE_HEIGHT * (1/self.delta), label, self.LABEL_FONT_SIZE, self.LABEL_FONT_FAMILY, self.LABEL_FONT_FAMILY, self.LABEL_FONT_SIZE, self.LABEL_COLOR)
			else:
				cr.move_to(self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - val) * self.LINE_HEIGHT * (1/self.delta))
				if (config['format'] == 'js'):
					paper += "				surface.text(%d, %d, '%s').attr({'font':'%dpx %s','font-family':'%s','font-size':%s,'fill':'#%s','text-anchor':'start'});\n" % (self.width - self.X_MARGIN - self.SPACE_WIDTH - self.eWidth , self.Y_MARGIN + self.HEADER_SPACE + (self.highest - val) * self.LINE_HEIGHT * (1/self.delta), label, self.LABEL_FONT_SIZE, self.LABEL_FONT_FAMILY, self.LABEL_FONT_FAMILY, self.LABEL_FONT_SIZE, self.LABEL_COLOR)
			cr.show_text(label)
		
			cr.stroke()
		
		# do the actual plotting
		
		cr.set_line_width(self.LINE_WIDTH)
		cr.set_source_rgb(LINE_R, LINE_G, LINE_B)
		
		slopeColor = self.SLOPE_COLOR
		
		lineCount = 0 
		for s1,e1,slope_val in self.pairs:
		
			if (slope_val > 0):
				cr.set_source_rgb(LINE_UP_R, LINE_UP_G, LINE_UP_B)
				slopeColor = self.SLOPE_UP_COLOR
			elif (slope_val < 0):
				cr.set_source_rgb(LINE_DOWN_R, LINE_DOWN_G, LINE_DOWN_B)
				slopeColor = self.SLOPE_DOWN_COLOR
			else:
				cr.set_source_rgb(LINE_R, LINE_G, LINE_B)
				slopeColor = self.SLOPE_COLOR

			if self.LOG_SCALE:
				cr.move_to(self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + self.startMaxLabelWidth + self.LINE_START_DELTA, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(s1)) * self.LINE_HEIGHT * (1/self.delta) - self.LINE_HEIGHT/4)
				cr.line_to(self.width - self.X_MARGIN - self.eWidth - self.SPACE_WIDTH - self.endMaxLabelWidth - self.LINE_START_DELTA, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(e1)) * self.LINE_HEIGHT * (1/self.delta) - self.LINE_HEIGHT/4)
				if (config['format'] == 'js'):
					paper += "				lines[%s] = surface.path('M %s %s L %s %s').attr({'stroke-width':%s,stroke:'#%s'});\n" % (lineCount, self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + self.startMaxLabelWidth + self.LINE_START_DELTA, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(s1)) * self.LINE_HEIGHT * (1/self.delta) - self.LINE_HEIGHT/8, self.width - self.X_MARGIN - self.eWidth - self.SPACE_WIDTH - self.endMaxLabelWidth - self.LINE_START_DELTA,self.Y_MARGIN + self.HEADER_SPACE + (self.highest - math.log(e1)) * self.LINE_HEIGHT * (1/self.delta) - self.LINE_HEIGHT/8,	1,slopeColor)				
			else:
				cr.move_to(self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + self.startMaxLabelWidth + self.LINE_START_DELTA, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - s1) * self.LINE_HEIGHT * (1/self.delta) - self.LINE_HEIGHT/4)
				cr.line_to(self.width - self.X_MARGIN - self.eWidth - self.SPACE_WIDTH - self.endMaxLabelWidth - self.LINE_START_DELTA, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - e1) * self.LINE_HEIGHT * (1/self.delta) - self.LINE_HEIGHT/4)
				if (config['format'] == 'js'):
					paper += "				lines[%s] = surface.path('M %s %s L %s %s').attr({'stroke-width':%s,stroke:'#%s'});\n" % (lineCount, self.X_MARGIN + self.sWidth + self.SPACE_WIDTH + self.startMaxLabelWidth + self.LINE_START_DELTA, self.Y_MARGIN + self.HEADER_SPACE + (self.highest - (s1)) * self.LINE_HEIGHT * (1/self.delta) - self.LINE_HEIGHT/8, self.width - self.X_MARGIN - self.eWidth - self.SPACE_WIDTH - self.endMaxLabelWidth - self.LINE_START_DELTA,self.Y_MARGIN + self.HEADER_SPACE + (self.highest - (e1)) * self.LINE_HEIGHT * (1/self.delta) - self.LINE_HEIGHT/8,	1,slopeColor)

			lineCount += 1

			cr.stroke()
		
		cr.restore()
		cr.show_page()
		
		if (config['format'] == "png"):
			surface.write_to_png(filename)
		elif (config['format'] == 'js'):

			paper += """			}  
        </script>
    </head>
    <body>
        <div id="surface"></div>
    </body>
</html>
"""
			with open(filename+".html", 'w') as f:
				f.write(paper)
		
		surface.finish()	
	
	def __init__(self, config):
	
		# since some methods need these, make them local to the class
	
		# height/width of page for extents calc (tmp surface)
		self.TMP_W = 8.5 * 72
		self.TMP_H = 11.0 * 72
		
		self.LABEL_FONT_FAMILY = config["label_font_family"]
		self.LABEL_FONT_SIZE = float(config["label_font_size"])
		
		self.LABEL_COLOR = config["label_color"]
		self.VALUE_COLOR = config["value_color"]
		self.BACKGROUND_COLOR = config["background_color"]
		
		if "header_font_family" in config:
			self.HEADER_FONT_FAMILY = config["header_font_family"]
			self.HEADER_FONT_SIZE = float(config["header_font_size"])
			self.HEADER_COLOR = config["header_color"]
		else:
			self.HEADER_FONT_FAMILY = None
			self.HEADER_FONT_SIZE = None
			self.HEADER_COLOR = None

		self.SLOPE_COLOR = config["slope_color"]

		if "slope_up_color" in config:
			self.SLOPE_UP_COLOR = config["slope_up_color"]
		else:
			self.SLOPE_UP_COLOR = config["slope_color"]
		
		if "slope_down_color" in config:
			self.SLOPE_DOWN_COLOR = config["slope_down_color"]
		else:
			self.SLOPE_DOWN_COLOR = config["slope_color"]
			
		self.X_MARGIN = float(config["x_margin"])
		self.Y_MARGIN = float(config["y_margin"])
		self.LINE_WIDTH = float(config["line_width"])

		if "slope_length" in config:
			self.SLOPE_LENGTH = float(config["slope_length"])
		else:
			self.SLOPE_LENGTH = 300
			
		if "round_precision" in config:
			self.ROUND_PRECISION = int(config["round_precision"])
		else:
			self.ROUND_PRECISION = None
			
		if "log_scale" in config:
			self.LOG_SCALE = True
		else:
			self.LOG_SCALE = False

		self.SPACE_WIDTH = self.LABEL_FONT_SIZE / 2.0
		self.LINE_HEIGHT = self.LABEL_FONT_SIZE + (self.LABEL_FONT_SIZE / 2.0)
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
					help="config file name to use for slopegraph creation",)
	args = parser.parse_args()

	if args.config:
	
		json_data = open(args.config)
		config = json.load(json_data)
		json_data.close()
		
		PySlopegraph(config)

	return(0)
	
if __name__ == "__main__":
	main()
