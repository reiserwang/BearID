#! /usr/bin/python

import sys
import xml.etree.cElementTree as ET
import pdb
import random
import logging
import xml.dom.minidom
import argparse
import xml_explore as xe
import os
import datetime
from xml.dom import minidom
from copy import deepcopy
from collections import namedtuple
from collections import defaultdict
from os import walk
import numpy as np
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


g_x = 0
g_y = 1
g_unused = 2
g_small_img = 3
g_verbosity = 0
g_filetype = ''
g_stats_few = []
g_stats_many = []
g_argv = ''
g_exec_name = 'bearID v0.1'

##------------------------------------------------------------
##  add indentations to xml content for readability
##------------------------------------------------------------
def prettify(elem) :
    # pdb.set_trace ()
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = xml.dom.minidom.parseString(rough_string)
    pretty_print = '\n'.join(
        [line for line in reparsed.toprettyxml(indent=' '*2).split('\n')
        if line.strip()])
    return pretty_print

##------------------------------------------------------------
##  add indentations
##------------------------------------------------------------
def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem

##------------------------------------------------------------
##  set global verbosity
##------------------------------------------------------------
def set_verbosity  (verbosity) :
	global g_verbosity
	g_verbosity = verbosity

##------------------------------------------------------------
##  get global verbosity
##------------------------------------------------------------
def get_verbosity () :
	return g_verbosity

##------------------------------------------------------------
##  set global filetype
##------------------------------------------------------------
def set_filetype  (filetype) :
	global g_filetype
	g_filetype = filetype

##------------------------------------------------------------
##  get global filtype
##------------------------------------------------------------
def get_filetype () :
	return g_filetype

##------------------------------------------------------------
##  set global exec name
##------------------------------------------------------------
def set_exec_name  (exec_name) :
	global g_exec_name
	g_exec_name = exec_name

##------------------------------------------------------------
##  get global filtype
##------------------------------------------------------------
def get_exec_name () :
	return g_exec_name

##------------------------------------------------------------
##------------------------------------------------------------
def set_argv (argv) :
	global g_argv
	g_argv = ' '.join (argv)

##------------------------------------------------------------
##------------------------------------------------------------
def get_argv () :
	return g_argv

##------------------------------------------------------------
##  load xml into dictionary of <string><element_list>
##  ex:  d["b-032"] = ["<Element 'chip' at 0x123,..,<Element 'chip' at 0x43]
##       d["b-747"] = ["<Element 'chip' at 0x987,..,<Element 'chip' at 0x65]
##------------------------------------------------------------
def load_objs (root, d_objs, filetype) :
	## print "loading chips"

	objects = []
	global g_stats_few
	global g_stats_many
	if filetype == 'chips' :
		for chip in root.findall ('./chips/chip'):
			label_list = chip.findall ('label')
			chipfile = chip.attrib.get ('file')
			if len (label_list) < 1 :
				g_stats_few.append (chipfile)
				print "no labels: ", label_list
				continue
			if len (label_list) > 1 :
				g_stats_many.append (chipfile)
				print "too many labels: ", label_list
				continue
			label = label_list[0].text
			objects.append (chipfile)
			d_objs[label].append(chip)
	elif filetype == 'faces' :
		# pdb.set_trace ()
		for image in root.findall ('./images/image'):
			box = image.findall ('box')
			facefile = image.attrib.get ('file')
			if len (box) == 0 :
				g_stats_few.append (facefile)
				continue
			if len (box) > 1 :
				g_stats_many.append (facefile)
				print "too many boxes (faces) : ", len (box)
				continue
			label_list = box[0].findall ('label')
			label = label_list[0].text
			objects.append (facefile)
			d_objs[label].append(image)
	elif filetype == 'pairs' :
		matched = 0
		unmatched = 1
		matched_cnt = 0
		unmatched_cnt = 0
		# pdb.set_trace ()
		for pair in root.findall ('./chips/pair_matched'):
			labels = pair.findall ('./chip/label')
			if len (labels) != 2 :
				print 'error: expecting only 2 chips in pair, got: ', labels
				continue
			if labels[0].text != labels[1].text :
				print 'error: labels should match: ', labels
			matched_cnt += 1
			d_objs[matched].append(labels[0])
		objects.append (d_objs[matched])
		for pair in root.findall ('./chips/pair_unmatched'):
			labels = pair.findall ('./chip/label')
			if len (labels) != 2 :
				print 'error: expecting only 2 chips in pair, got: ', labels
				continue
			if labels[0].text == labels[1].text :
				print 'error: labels should not match: ', labels
			unmatched_cnt += 1
			d_objs[unmatched].append(labels)
		objects.append (d_objs[unmatched])
	else :
		print 'Error: unknown filetype.  Expected one of "faces" or "chips" or "pairs.'
	return objects


##------------------------------------------------------------
##
##------------------------------------------------------------



##------------------------------------------------------------
##  print dictionary
##------------------------------------------------------------
def print_dict (chips_d) :
	for key, value in chips_d.items():
		print(key)
		print(value)

##------------------------------------------------------------
##  ^^^^^^^^^^ START COMMENT ^^^^^^^^^^^^^^^^^^^^^^
##  ^^^^^^^^^^ END COMMENT ^^^^^^^^^^^^^^^^^^^^^^

##------------------------------------------------------------
##  partition all files into x and y percent
##------------------------------------------------------------
def generate_partitions (files, x, y, output, shuffle=True, img_cnt_min=0, test_min=0, image_size_min=0, filetype="chips") :
	# print "partitioning chips into: ", x, " ", y
	# pdb.set_trace ()
	# detect if chips file or faces file

	chips_d = defaultdict(list)
	load_objs_from_files (files, chips_d, filetype)
	chunks = partition_chips (chips_d, x, y, shuffle, img_cnt_min, test_min, image_size_min, filetype)
	# pdb.set_trace ()
	file_x = output + "_" + str(x) + ".xml"
	file_y = output + "_" + str(y) + ".xml"
	file_small_img = file_unused = None
	if len (chunks[g_unused]) > 0 :
		file_unused = output + "_unused" + ".xml"
	if len (chunks[g_small_img]) > 0 :
		file_small_img = output + "_small_faceMeta" + ".xml"
	filenames = [file_x, file_y, file_unused, file_small_img]
	generate_partition_files (chunks, filenames, filetype)

##------------------------------------------------------------
##  remove chips with resolution below min
##  returns list of tiny chips
##------------------------------------------------------------
def remove_tiny_chips (chips, image_size_min) :
	small_chips = []
	for i in range (len (chips)-1, 0, -1) :
		res = chips[i].find ('resolution')
		if int (res.text) < image_size_min :
			small_chips.append (chips.pop (i))
	return small_chips

##------------------------------------------------------------
##  given list of chips, return list of face images
##------------------------------------------------------------
def make_images_from_chips (chips) :
	faces = [chip.find ('source') for chip in chips] 
	for face in faces :
		face.tag = 'image'
	return faces

##------------------------------------------------------------
##  partition chips into x and y percent
##------------------------------------------------------------
def partition_chips (chips_d, x, y, shuffle=True, img_cnt_min=0, test_minimum=0, image_size_min=0, filetype="chips") :
	# print "partitioning chips into: ", x, " ", y
	# pdb.set_trace ()
	chunks = []
	if (shuffle == True) :  ## concat all labels, then split
		## TODO check for image_size_min
		all_chips=[]
		for label, chips in chips_d.items():
			all_chips.extend (chips)
		if image_size_min != 0 :
			small_chips = remove_tiny_chips (all_chips, image_size_min)
		random.shuffle (all_chips)
		partition = int(round(len(all_chips) * float (x) / float (100)))
		# print "partition value : ", partition
		chunks.append (all_chips[:partition])
		chunks.append (all_chips[partition:])
		print "\nmixed partition of ", x, ", len : ", len (chunks[0])
		print "shuffled partition of ", y, ", len : ", len (chunks[1])
		print "shuffled total of ", len (chunks[0]) + len (chunks[1])
		# print "chips count: ", len (all_chips)
	else :				## split per label, then combine into chunks
		# pdb.set_trace ()
		chunks_x = []
		chunks_y = []
		chunks_few = []
		labels_few = []
		small_images_chips = []
		chip_cnt = 0
		for label, chips in chips_d.items():
			# remove chips below size minimum
			if image_size_min != 0 :
				small_images_chips.extend (remove_tiny_chips (chips, image_size_min))
			if len (chips) < img_cnt_min :
				chunks_few.extend (chips)
				labels_few.append (label)
				continue
			random.shuffle (chips)
			chip_cnt += len (chips)
			partition = int(round(len(chips) * float (x) / float (100)))
			chunks_x.extend (chips[:partition])
			chunks_y.extend (chips[partition:])
		chunks.append (chunks_x)
		chunks.append (chunks_y)
		print
		print len (chunks_x), ' chips in individual partition of', x
		print len (chunks_y), ' chips in individual partition of', y
		print chip_cnt, 'total', filetype
		print
		if len (labels_few) > 0 :
			chunks.append (chunks_few)
			print len (labels_few), 'unused labels, each with less than ', img_cnt_min, 'images'
			# print labels_few
		else :
			print 'All labels used.'
			chunks.append ([])
		if len (small_images_chips) :
			# files_small = [chip.attrib.get ('file') for chip in small_images_chips]
			# img_list = '\n   '.join (files_small)
			# print img_list
			print len (small_images_chips), 'images unused due to size below', image_size_min
			small_images_faces = make_images_from_chips (small_images_chips) 
			chunks.append (small_images_faces)
		else :
			print 'All chips used.\n'
			chunks.append ([])

	# pdb.set_trace ()
	return chunks

##------------------------------------------------------------
##  split defaultdict<string><list> into n equal random parts
##  returns array  (list of n lists)
##  By default, all labels are combined, shuffled, then split.
##	If shuffle is False, shuffle each label, split, then added to chunks
##
##------------------------------------------------------------
def split_chips_into_n (chips_d, n, shuffle_mode) :
	chips_d_items = chips_d.items ()
	all_chips_cnt = sum ([len (chips) for label, chips in chips_d_items])
	mode_text = ''
	if shuffle_mode == 0 :  ## concat all labels, then split
		chunks=[]
		all_chips=[]
		for label, chips in chips_d_items :
			all_chips.extend (chips)
		random.shuffle (all_chips)
		chunk_size = len(all_chips) / float (n)
		print "\nshuffled fold size : ", int (chunk_size)
		print "chips count: ", all_chips_cnt
		mode_text = 'All chips are mixed together then divided info each fold.'
		for i in range (n):
			start = int(round(chunk_size * i))
			end = int(round(chunk_size * (i+1)))
			# print "start : ", start
			# print "end : ", end
			chunks.append (all_chips[start:end])
	elif shuffle_mode == 1 :  ## split per label, then combine into chunks
		# pdb.set_trace ()
		chunks = [[] for i in range(n)]		# create n empty lists
		mode_text = '      chips of each label are split evenly into each fold.'
		for label, chips in chips_d_items :
			random.shuffle (chips)
			chunk_size = len(chips) / float (n)
			j = range (n)
			# randomize order of fold assignment since many labels
			# have few chips.  prevents single chips from all being
			# in same fold.
			random.shuffle (j)
			for i in range (n):
				start = int(round(chunk_size * i))
				end = int(round(chunk_size * (i+1)))
				chunks[j[i]].extend (chips[start:end])
	else :				## split across labels
		##  TODO : split labels here
		chunks = [[] for i in range(n)]		# create n empty lists
		random.shuffle (chips_d_items)
		# randomize order of fold assignment
		j = range (n)
		random.shuffle (j)
		chunk_size = len (chips_d_items) / float (n)
		# pdb.set_trace ()
		for i in range (n):
			start = int(round(chunk_size * i))
			end = int(round(chunk_size * (i+1)))
			labels_list = chips_d_items[start:end]
			for label, chips in labels_list :
				chunks[j[i]].extend (chips)
		print len (chips_d), 'total labels, split into', n, 'folds = ~', int (len (chips_d) / float (n))

	print all_chips_cnt, 'total chips, split into', n, 'folds = ~', int (all_chips_cnt / float (n))
	print '     ', mode_text
	folds_cnt = [len (fold) for fold in chunks]
	labels_cnt = [[] for i in range (n)]
	for i in range (n) :
		labels = [(chip.find ('label')).text for chip in chunks[i]]
		labels_cnt[i] = len (set (labels))
	print 'count per fold:'
	print '     ', folds_cnt, 'sum: ', sum (folds_cnt)
	print 'labels per fold:'
	print '     ', labels_cnt
	# pdb.set_trace ()
	return chunks

##------------------------------------------------------------
##  create n sets of trees of train & validate content
##  then write xml files
##------------------------------------------------------------
def generate_folds_files (train_list, validate_list, filename) :
	n = len (train_list)
	# write 2 files for each fold

	print "\nGenerated", n, "sets of folds files: "
	for i in range(n) :
		t_root, t_chips = create_new_tree_w_element ()
		for j in range (len (train_list[i])) :
			chip = train_list[i][j]
			t_chips.append (chip)
		v_root, v_chips = create_new_tree_w_element ()
		for j in range (len (validate_list[i])) :
			chip = validate_list[i][j]
			v_chips.append (chip)
		tree_train = ET.ElementTree (t_root)
		tree_validate = ET.ElementTree (v_root)
		t_name = filename + "_train_" + str(i) + ".xml"
		v_name = filename + "_validate_" + str(i) + ".xml"
		indent (t_root)
		indent (v_root)
		tree_train.write (t_name)
		tree_validate.write (v_name)
		print "\t", t_name, "\n\t", v_name
	print ""

##------------------------------------------------------------
##  create each xml tree for x and y partition
##  then write xml files
##------------------------------------------------------------
def generate_partition_files (chunks, filenames, filetype="chips") :
	list_x = chunks[g_x]
	list_y = chunks[g_y]
	file_x = filenames[g_x]
	file_y = filenames[g_y]
	file_unused = filenames[g_unused]
	file_small_img = filenames[g_small_img]

	root_x, chips_x = create_new_tree_w_element (filetype)
	for i in range(len(list_x)):
		chips_x.append (list_x[i])
	root_y, chips_y = create_new_tree_w_element (filetype)
	for i in range(len(list_y)):
		chips_y.append (list_y[i])

	indent (root_x)
	indent (root_y)
	tree_x = ET.ElementTree (root_x)
	tree_y = ET.ElementTree (root_y)
	tree_x.write (file_x)
	tree_y.write (file_y)
	print "\nGenerated partition files: \n\t", file_x, "\n\t", file_y
	print ""

	if file_unused :
		list_unused = chunks[g_unused]
		root_unused, chips_unused = create_new_tree_w_element (filetype)
		for chip in list_unused :
			chips_unused.append (chip)
		indent (root_unused)
		tree_unused = ET.ElementTree (root_unused)
		tree_unused.write (file_unused)
		print '\t', len (list_unused), 'labels unused due to less than minimum # of images, written to file : \n\t', file_unused, '\n'
		print
	if file_small_img :
		list_small_img = chunks[g_small_img]
		root_small, chips_small = create_new_tree_w_element ('faces')
		for i in range(len(list_small_img)):
			chips_small.append (list_small_img[i])
		indent (root_small)
		tree_small = ET.ElementTree (root_small)
		tree_small.write (file_small_img)
		print len (list_small_img), 'unused chips below min size written to file : \n\t', file_small_img, '\n'
	print

##------------------------------------------------------------
##  create n sets of train & validate files
##  split list into n chunks
##  foreach i in n: chunks[n] is in validate, the rest in train
##  returns list of train content and list of validate content
##     to be consumed by generate_folds_files
##------------------------------------------------------------
def generate_folds_content (chips_d, n_folds, shuffle=True) :
	n = int (n_folds)
	validate_list = []
	train_list = [[] for i in range(n)]
	chunks = split_chips_into_n (chips_d, n, shuffle)
	for i in range (n):
		validate_list.append (chunks[i])
		# pdb.set_trace()
		for j in range (n):
			if (j == i):
				continue
			train_list[i].extend (chunks[j])
	return train_list, validate_list

##------------------------------------------------------------
##  creates new tree, add standard file heading, 
##    then add specified element.  returns root and new element
##------------------------------------------------------------
def create_new_tree_w_element (filetype="chips") :
	r = ET.Element ('dataset')
	r_c = ET.SubElement (r, 'comment').text = 'generated by ' + g_exec_name
	curtime = datetime.datetime.now().strftime("%Y%m%d:%H%M")
	ET.SubElement (r, 'date').text = filetype + ' file generated at ' + curtime
	ET.SubElement (r, 'command').text = get_argv ()
	ET.SubElement (r, 'filetype').text = get_filetype ()
	if filetype == "faces" :
		elem_name = "images"
	else :
		elem_name = "chips"
	r_elem = ET.SubElement (r, elem_name)
	return r, r_elem

##------------------------------------------------------------
##   create copy of xml file of particular label
##------------------------------------------------------------
def write_file_with_label (xml_file_in, xml_file_out, key):
	tree_i = ET.parse (xml_file)
	root_i = tree.getroot()

	for chip in root_i.findall ('./chips/chip'):
		label_list = chip.findall ('label')
		if len (label_list) > 1 :
			print "too many labels: ", label_list
			continue
		label = label_list[0].text
		if label != key :
			root.remove (chip)
	indent (root_i)
	tree_i.write (xml_file_out)

##------------------------------------------------------------
##
##------------------------------------------------------------
def unpath_chips (xml_files, append):
	# pdb.set_trace ()
	for xml_file in xml_files:
		root, tree = xe.load_file (xml_file)
		for chip in root.findall ('./chips/chip'):
			label_list = chip.findall ('label')
			pathed_chipfile = chip.attrib.get ('file')
			unpathed_chipfile = os.path.basename (pathed_chipfile)
			# pdb.set_trace ()
			chip.set ('file', unpathed_chipfile)
			# print "   ", pathed_chipfile
			# print "  --->  ", unpathed_chipfile
		basename, ext = os.path.splitext(xml_file)
		if append:
			xml_file_unpathed = xml_file + "_unpathed"
		else:
			xml_file_unpathed = basename + "_unpathed" + ext
		# pdb.set_trace ()
		if get_verbosity () > 1 :
			print "\n\twriting unpath chips to file: ", xml_file_unpathed, "\n"
		indent (root)
		tree.write (xml_file_unpathed)

##------------------------------------------------------------
##   return flattened list of all xml files
##------------------------------------------------------------
def generate_xml_file_list (inputfiles):
	f = []
	for i in inputfiles :
		if os.path.isdir (i) :
			files =  get_xml_files (i)
			f.extend (files)
		else :
			f.append (i)
	return f

##------------------------------------------------------------
##  load objs from list of files into objs_d
##    if filename is directory, load all its xml files
##------------------------------------------------------------
def load_objs_from_files (filenames, objs_d, filetype="chips"):
	chipfiles = []
	# print "in load_objs_from_files"
	# pdb.set_trace ()
	## load all chips into objs_d
	print "\nLoading", filetype, "for files: "
	for file in filenames:
		print "\t", file
		# pdb.set_trace()
		root, tree = xe.load_file (file)
		chipfiles.extend (load_objs (root, objs_d, filetype))
	# pdb.set_trace()
	return chipfiles

##------------------------------------------------------------
##  filter chips :
##	  given list of chip files, and circle defined by
##    pt and distance, return chips with nose in circle
##------------------------------------------------------------
def filter_chips (infiles, pt, distance, outfile):
	chips_d = defaultdict(list)
	objfiles = load_objs_from_files (infiles, chips_d)
	l_eye, r_eye, nose, noses = get_chip_face_stats (chips_d)
	# pdb.set_trace ()
	if (pt[0] == 0) and (pt[1] == 0):
		nose_x = noses[0]
		nose_y = noses[1]
	else:
		nose_x = pt[0]
		nose_y = pt[1]
	if distance == 0: ## use 1/2 distance between eyes
		distance = (l_eye[0]-r_eye[0])/2
	chips_list, x_list, y_list, label_count = get_chips_noses_in_circle (
	    chips_d, nose_x, nose_y, distance)
	y_list_flip = []
	for y in y_list :
		y_list_flip.append (0-y)
	have_display = "DISPLAY" in os.environ
	if have_display:
		# plt.autoscale(enable=True, axis='both', tight=None)
		plt.axis('equal')
		plt.axis('off')
		plt.scatter (l_eye[0], 0-l_eye[1], c='blue', s=64)
		plt.scatter (r_eye[0], 0-r_eye[1], c='blue', s=64)
		plt.scatter (x_list, y_list_flip, c='green', s=16)
		plt.scatter (nose_x, 0-nose_y, c='red', s=128)
		#plt.imsave ("noses.jpg", format="png")
		plt.savefig ("nose_fig.png")
		plt.show ()
	write_chip_file (chips_list, outfile)
	print '----------------------------------'
	print 'eyes:', r_eye, l_eye
	print 'center:', nose_x, nose_y
	print 'radius:', distance
	print '----------------------------------'
	print len (x_list), 'chips matched from', chips_count (chips_d)
	print 'with', label_count, 'labels from original', len (chips_d)
	print '  chips written to file:', outfile
	print ''
	# pdb.set_trace ()

##------------------------------------------------------------
##  return count of chips in dict
##------------------------------------------------------------
def chips_count (chips_d):
	count = 0
	for key, chips in sorted(chips_d.items()): ## list of chips
		count += len (chips)
	return count

##------------------------------------------------------------
##  return chips with noses within
## 	 circle of radius d, centered at x,y
##------------------------------------------------------------
def get_chips_noses_in_circle (chips_d, pt_x, pt_y, distance):
	x_list = []
	y_list = []
	filtered_chips = []
	# pdb.set_trace ()
	## comparing with squares since sqrt is slow
	distance = distance**2
	label_count = 0
	for key, chips in sorted(chips_d.items()): ## list of chips
		chip_count = 0
		for chip in chips:
			for part in chip.findall ('part'):
				name = part.attrib.get ('name')
				if name == "nose" :
					nose_x = int (part.attrib.get ('x'))
					nose_y = int (part.attrib.get ('y'))
					## check to see if within specified dist
					d = (pt_x-nose_x)**2 + (pt_y-nose_y)**2
					if d <= distance:
						x_list.append (nose_x)
						y_list.append (nose_y)
						filtered_chips.append (chip)
						chip_count = 1
		if chip_count > 0:
			label_count += 1
	return filtered_chips, x_list, y_list, label_count

##------------------------------------------------------------
##  given chip list, write to xml file
##------------------------------------------------------------
def write_chip_file (chips, outfile):
	root, chips_elem = create_new_tree_w_element ()
	for chip in chips:
		chips_elem.append (chip)
	indent (root)
	tree = ET.ElementTree (root)
	tree.write (outfile)

##------------------------------------------------------------
##  get chip face stats :
##       nose (x, y), eye1 (x,y), eye2 (x, y), eye dist
##    collect all nose_x, nose_y, get average
##    get first chip, extract eye1, eye2, get distance
##------------------------------------------------------------
def chip_face_stats (filenames):
	chips_d = defaultdict(list)
	objfiles = load_objs_from_files (filenames, chips_d)
	l_eye, r_eye, nose, noses = get_chip_face_stats (chips_d)
	have_display = "DISPLAY" in os.environ
	if not have_display:
		return
	display_hist_heat (noses)
	display_hist (noses)
	band_width, bands = get_dist_hist (noses)
	default_dist = (l_eye[0] - r_eye[0]) / 2
	display_dist_hist (bands, band_width, default_dist)
	plt.show ()

##------------------------------------------------------------
##  plot nose dist histogram
##------------------------------------------------------------
def display_dist_hist (bands, band_width, default_dist=0, label_x='', label_y='', title=''):
	band_label = [(x+1) * band_width for x in range(len(bands))]
	# pdb.set_trace ()
	# plt.autoscale(enable=True, axis='both', tight=None)
	# plt.axis('equal')
	fig3 = plt.figure()
	if not title :
		plt.title ('distance histogram. default @' + str (default_dist))
	plt.axis('on')
	if not label_y :
		plt.ylabel('face count')
	if not label_x :
		plt.xlabel('distance')
	plt.bar (band_label, bands, 7, color='green')
	if default_dist :
		plt.bar (default_dist, max(bands), 7, color='red')
	# plt.scatter (band_label, bands, c='green', s=16)
	# plt.savefig ("nose_fig.png")

##------------------------------------------------------------
##  plot histogram heatmap
##------------------------------------------------------------
def display_hist_heat (noses):
	x = noses[0]
	y = noses[1]
	# Plot data
	fig1 = plt.figure()
	plt.title ('nose histogram.')
	plt.plot(x,y,'.r')
	plt.xlabel('x')
	plt.ylabel('y')

	# Estimate the 2D histogram
	nbins = 10
	H, xedges, yedges = np.histogram2d(x,y,bins=nbins)

	# H needs to be rotated and flipped
	H = np.rot90(H)
	H = np.flipud(H)

	# Mask zeros
	Hmasked = np.ma.masked_where(H==0,H) # Mask pixels with a value of zero

	# Plot 2D histogram using pcolor
	fig2 = plt.figure()
	plt.title ('nose histogram heat map: ' + str (nbins) + ' bins.')
	plt.pcolormesh(xedges,yedges,Hmasked)
	plt.xlabel('x')
	plt.ylabel('y')
	cbar = plt.colorbar()
	cbar.ax.set_ylabel('Counts')
	# plt.show ()

##------------------------------------------------------------
## return list of paired tuple
##------------------------------------------------------------
def create_tuple_pair (label1, image1, label2, image2):
	return ((label1, image1), (label2, image2))

##------------------------------------------------------------
## generate all possible index pairs of images of given label
## return list of list.  one list per label of all combination
##		for that label
##------------------------------------------------------------
def gen_all_matched_obj_pairs  (chips_d):
	matched_lists = []
	matched_pairs = []
	chips_list = sorted(chips_d.items())
	label_count = len (chips_list)
	for label1 in range (label_count) :		# for each label
		matched_pairs = []
		chip1s_cnt = len (chips_list[label1][1])
		# pdb.set_trace ()
		for i in range (chip1s_cnt) :		# iterate thru images
			for j in range (i+1, chip1s_cnt) :
				pairs = create_tuple_pair (label1, i, label1, j)
				matched_pairs.append (pairs)
		# pdb.set_trace ()
		matched_lists.append (matched_pairs)
	return matched_lists

##------------------------------------------------------------
## generate all possible index pairs of images of different labels
## return array of lists.  List indices >= to first index will be null.
## i.e. len (lists[4][2]) = 0 . len (lists [2][4] = unmatched pairs
##      for bear 2 and bear 4
##   e.g. unmatched images for labels 5, 3 ##   will be in lists[3][5]
## Need to have this table to counter labels with lots of images.
##   If we were to only generate list of unmatched images for a
##   label, it would be weighted towards the labels with greater
##   images.  To use this table, select a random label1, then a 
##   random label2, then select random entry of list in this table.
##------------------------------------------------------------
def gen_all_unmatched_obj_pairs  (chips_d):
	unmatched_lists = []
	unmatched_sublist = []
	unmatchted_pairs = []
	chips_list = sorted(chips_d.items())
	label_count = len (chips_list)
	for label1 in range (label_count) :
		unmatched_sublist = []
		for x in range (label1+1) : # empty out lower indices
			unmatched_sublist.append ('')
		chip1s_cnt = len (chips_list[label1][1])
		for label2 in range (label1+1, label_count) :
			unmatched_pairs = []
			chip2s_cnt = len (chips_list[label2][1])
			for i in range (chip1s_cnt) :
				for j in range (chip2s_cnt) :
					pairs = create_tuple_pair (label1, i, label2, j)
					unmatched_pairs.append (pairs)
			unmatched_sublist.append (unmatched_pairs)
		# pdb.set_trace ()
		unmatched_lists.append (unmatched_sublist)
	return unmatched_lists

##------------------------------------------------------------
## write out N pairs of matched pairs and M pairs of unmatched pairs
##------------------------------------------------------------
def generate_chip_pairs (input_files, matched_cnt, unmatched_cnt, triplets, output):
	chips_d = defaultdict(list)
	load_objs_from_files (input_files, chips_d)
	if triplets > 0 :
		unmatched_cnt = matched_cnt = triplets
	selected_matched_indices, selected_unmatched_indices = get_selected_pair_indices (chips_d, matched_cnt, unmatched_cnt, triplets)
	matched_chips = create_chip_list (chips_d, selected_matched_indices)
	unmatched_chips = create_chip_list (chips_d, selected_unmatched_indices)

	## create xml content
	root, chips = create_new_tree_w_element ('pairs')
	elem_name = "pair_matched"
	for i in range (0, len (matched_chips), 2) :
		# create new matched pair element, then put 2 chips under it
		pair = ET.SubElement (chips, elem_name)
		pair.append (matched_chips[i])
		pair.append (matched_chips[i+1])
	elem_name = "pair_unmatched"
	for i in range (0, len (unmatched_chips), 2) :
		# create new matched pair element, then put 2 chips under it
		pair = ET.SubElement (chips, elem_name)
		pair.append (unmatched_chips[i])
		pair.append (unmatched_chips[i+1])

	# pdb.set_trace ()
	if matched_cnt == 0 :
		matched_cnt = len (selected_matched_indices)
	if unmatched_cnt == 0 :
		unmatched_cnt = len (selected_unmatched_indices)
	## write out file
	print '\nWriting', matched_cnt, 'matched pairs and', unmatched_cnt, 'unmatched pairs to file:'
	print '\t', output, '\n'
	indent (root)
	tree = ET.ElementTree (root)
	tree.write (output)

##------------------------------------------------------------
##  return two lists of pairs for matched and unmatched
##    generate a list of all possible indices for matching and 
##    unmatching pairs for each label.  store in table of labels
##    select random label, then select random un/matching pair of label
##------------------------------------------------------------
def get_selected_pair_indices (chips_d, matched_cnt, unmatched_cnt, triplet=0) :
	all_matched_pairs_arr = gen_all_matched_obj_pairs (chips_d)
	all_unmatched_pairs_3arr = gen_all_unmatched_obj_pairs (chips_d)
	selected_matched_list = []
	selected_unmatched_list = []
	label_cnt = len (chips_d)
	max_matched_cnt = sum ([len (pairs_list) for pairs_list in all_matched_pairs_arr])
	max_unmatched_cnt = sum ([len (pairs_list) for pairs_arr in all_unmatched_pairs_3arr for pairs_list in pairs_arr])

	# pdb.set_trace ()
	if matched_cnt == 0 :
		matched_cnt = max_matched_cnt
	if matched_cnt > max_matched_cnt :
		print '  *** requesting more matched pairs than exists.'
		print '  *** creating max number of matched pairs.'
		matched_cnt = max_matched_cnt
	if unmatched_cnt == 0 :
		unmatched_cnt = max_unmatched_cnt
	if unmatched_cnt > max_unmatched_cnt :
		print '  *** requesting more unmatched pairs than exists.'
		print '  *** creating max number of unmatched pairs.'
		unmatched_cnt = max_unmatched_cnt
	# pdb.set_trace ()
	# need to start with matched set to ensure there is a set
	i = 0
	if matched_cnt == max_matched_cnt :  # getting ALL matched pairs
		selected_matched_list = [pair for pair_list in all_matched_pairs_arr for pair in pair_list]
		i = matched_cnt
	while i < matched_cnt :
		x = random.randint(0,label_cnt-1)
		img_cnt = len (all_matched_pairs_arr[x])
		if img_cnt == 0 :
			continue
		label_list = all_matched_pairs_arr[x]
		z = random.randint(0,img_cnt-1)
		# if looking for triplet, find unmatched set now
		if triplet > 0 :
			w = random.randint(0, 1)  # pick one of 2 sets
			set1 = label_list[z][w]	  # anchor
			label_y = label_x = set1[0]
			while label_y == label_x :
				label_y = random.randint(0,label_cnt-1)
			if label_x > label_y :
				label_list_u = all_unmatched_pairs_3arr[label_y][label_x]
			else :
				label_list_u = all_unmatched_pairs_3arr[label_x][label_y]
			img_cnt_u = len (label_list_u)
			#   need to find anchor set1 then move entry to selected
			found_match = False
			for u in range (img_cnt_u-1) :
				# pdb.set_trace ()
				if set1 in label_list_u[u]:  # take first match rather than find all and random select
					selected_unmatched_list.append (label_list_u.pop(u))
					found_match = True
					break
			if not found_match :
				print 'Unable to find unmatch set for anchor', set1, ', trying again.'
				continue
		selected_matched_list.append (label_list.pop(z))
		i += 1
	if triplet > 0 :
		return selected_matched_list, selected_unmatched_list
	i = 0
	if unmatched_cnt == max_unmatched_cnt :  # getting ALL unmatched pairs
		selected_unmatched_list = [pair for pairs_arr in all_unmatched_pairs_3arr for pair_list in pairs_arr for pair in pair_list]
		i = unmatched_cnt
	while i < unmatched_cnt :
		y = x = random.randint(0,label_cnt-1)
		while y == x :
			y = random.randint(0,label_cnt-1)
		if x > y :
			label_list = all_unmatched_pairs_3arr[y][x]
		else :
			label_list = all_unmatched_pairs_3arr[x][y]
		# pdb.set_trace ()
		img_cnt = len (label_list)
		if img_cnt == 0 :
			continue
		z = random.randint(0,img_cnt-1)
		# move entry to selected
		selected_unmatched_list.append (label_list.pop(z))
		i += 1
	return selected_matched_list, selected_unmatched_list

##------------------------------------------------------------
##  create lists of chips pairs given indices in the form:
##    [ ((l1, image1), (l2, image2)), ... ]
##------------------------------------------------------------
def create_chip_list (chips_d, indices) :
	chips_list = sorted (chips_d.items())
	chips = []
	#  label, chips in chips_d.items():
	for pair in indices :
		l1 = pair[0][0]
		i1 = pair[0][1]
		l2 = pair[1][0]
		i2 = pair[1][1]
		# print '((', l1, i1, '), (', l2, i2, '))'
		# l, 1, i : is to access the list of (label,chips)
		chip1 = chips_list[l1][1][i1]
		chip2 = chips_list[l2][1][i2]
		chips.append (chip1)
		chips.append (chip2)
	return chips

##------------------------------------------------------------
##  plot histogram of points, of nxn bins
##------------------------------------------------------------
def display_hist (noses):
	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	# x, y = np.random.rand(2, 100) * 4
	x = noses[0]
	y = noses[1]
	nbins = 10
	hist, xedges, yedges = np.histogram2d(x, y, bins=nbins)

	# Note: np.meshgrid gives arrays in (ny, nx) so we use 'F' to flatten xpos,
	# ypos in column-major order. For numpy >= 1.7, we could instead call meshgrid
	# with indexing='ij'.
	# xpos, ypos = np.meshgrid(xedges[:-1] + 0.25, yedges[:-1] + 0.25)
	plt.title ('nose histogram : ' + str (nbins) + ' bins.')
	xpos, ypos = np.meshgrid(xedges[:-1] + 1.0, yedges[:-1] + 1.0)
	xpos = xpos.flatten('F')
	ypos = ypos.flatten('F')
	zpos = np.zeros_like(xpos)

	# Construct arrays with the dimensions for the 16 bars.
	#dx = 0.5 * np.ones_like(zpos)
	dx = 1.0 * np.ones_like(zpos)
	dy = dx.copy()
	dz = hist.flatten()

	ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color='y', zsort='average')
	# plt.show()

##------------------------------------------------------------
##  plot distance histogram from mean.
##------------------------------------------------------------
def get_dist_hist (noses, band_width=0):
	x_list = noses[0]
	y_list = noses[1]
	sorted_x = sorted (x_list)
	sorted_y = sorted (y_list)
	nose_x = sum (x_list) / len (x_list)
	nose_y = sum (y_list) / len (y_list)
	band_count = 30
	if band_width == 0 :
		x_dist = sorted_x[-1] - sorted_x[0]
		y_dist = sorted_y[-1] - sorted_y[0]
		dist = math.sqrt (x_dist**2 + y_dist**2)
		band_width = int (dist/band_count)
	bands = [0] * (band_count + 1)
	# pdb.set_trace ()
	for i in range (len (y_list)) :
		pt_x = x_list[i]
		pt_y = y_list[i]
		d = math.sqrt ((pt_x-nose_x)**2 + (pt_y-nose_y)**2)
		band = int (d/band_width)
		bands[band] += 1
	print 'nose count: ', len (x_list)
	end = len (bands) - 1
	# pdb.set_trace ()
	for i in range (end, 0, -1) :
		if bands[i] :
			end = i+1
			break
	cnt = 0
	for i in range (len(bands)) :
		print '---   ', i, ':', bands[i]
		cnt += bands[i]
	print '# bands : ', end
	print 'band width     : ', band_width
	print 'total in bands : ', cnt
	return band_width, bands[:end]

##------------------------------------------------------------
##  given dict of chips, return eyes and list of noses
##------------------------------------------------------------
def get_chip_face_stats (chips_d, verbose=1):
	x_list = []
	y_list = []
	# pdb.set_trace ()
	get_reye = True
	get_leye = True
	all_chips = sorted(chips_d.items())
	for key, chips in all_chips :  ## list of chips
		for chip in chips :
			for part in chip.findall ('part'):
				name = part.attrib.get ('name')
				if get_leye :
					if name == "leye" :
						leye_x = int (part.attrib.get ('x'))
						leye_y = int (part.attrib.get ('y'))
						get_leye = False
						continue
				if get_reye :
					if name == "reye" :
						reye_x = int (part.attrib.get ('x'))
						reye_y = int (part.attrib.get ('y'))
						get_reye = False
						continue
				if name == "nose" :
					x = int (part.attrib.get ('x'))
					y = int (part.attrib.get ('y'))
					x_list.append (x)
					y_list.append (y)
	nose_x = sum (x_list) / len (x_list)
	nose_y = sum (y_list) / len (y_list)
	if verbose > 0 :
		print 'average nose : ', nose_x, nose_y
		print 'median  nose : ', np.median (x_list), np.median (y_list)
		print 'reye : ', reye_x, reye_y
		print 'leye : ', leye_x, leye_y
	return [leye_x, leye_y], [reye_x, reye_y], [nose_x, nose_y], [x_list, y_list]

##------------------------------------------------------------
##  print pairs stats
##------------------------------------------------------------
def print_pairs_stats (objs_d) :
	matched = 0
	unmatched = 1
	matched_list = objs_d[matched]
	unmatched_list = objs_d[unmatched]

	# get unique list of entries, then show count
	matched_labels = [label.text for label in matched_list]
	unmatched_labels = [(label[0].text, label[1].text) for label in unmatched_list]

	flatten_unmatched = [label for tupl in unmatched_labels for label in tupl]
	# pdb.set_trace ()
	for i in set (matched_labels):
		print i, ':', matched_labels.count (i)
	print '------------------------'
	print 'total : ', len (matched_labels)

	print '------------------------'
	print 'unmatched stats:'
	for i in set (flatten_unmatched):
		print i, ':', flatten_unmatched.count (i)
	print 'unmatched pairs: ', len (unmatched_labels)

##------------------------------------------------------------
##  return label stats in file
##------------------------------------------------------------
def get_obj_stats (filenames, print_files=False, filetype="chips", verbosity=1, write_stats=False):
	objs_d = defaultdict(list)
	objfiles = load_objs_from_files (filenames, objs_d, filetype)
	if filetype == "pairs" :
		print_pairs_stats (objs_d)
		return
	print ''
	# pdb.set_trace ()
	all_objs = sorted(objs_d.items())
	img_cnt_per_label = [len (objs) for key, objs in all_objs]
	obj_count = sum (img_cnt_per_label)
	if get_verbosity () > 1 :
		for label, chips in all_objs :
			print label, '	:', len (chips)
	u_combos = 0
	chips_count_list = img_cnt_per_label
	diff_chip_count  = obj_count
	for i in range (len (chips_count_list)-1) : 	# all labels
		i_count = len (all_objs[i][1])			# count of ith label
		diff_chip_count -= i_count				# count of different labels
		u_combos += (i_count * diff_chip_count)

	print '-----------------------------'
	print '            total', filetype, ':', obj_count
	print '                # bears :', len (objs_d)
	print ' average', filetype, 'per bear :', obj_count / len (objs_d)
	combos = sum ([(n*(n-1)/2) for n in img_cnt_per_label if n > 1])
	print '  median', filetype, 'per bear :', np.median (img_cnt_per_label)
	print '  possible matched sets :', combos
	print 'possible unmatched sets :', u_combos
	# display_dist_hist (img_cnt_per_label, 2, 0, 'bear index', '# images')
	have_display = "DISPLAY" in os.environ
	if (get_verbosity () > 2) :
		if have_display:
			#plt.hist(img_cnt_per_label, len(objs_d)/5, facecolor='blue', alpha=0.5)
			hist_info = plt.hist(img_cnt_per_label, 20, facecolor='blue', alpha=0.5)
			plt.title('histogram of ' + filetype + ' count per bear')
			plt.xlabel('# chips per bear (total=' + str (obj_count) + ')')
			plt.ylabel('# bears (total=' + str (len (objs_d)) + ')')
			hist_obj_cnt_file = 'hist_obj_cnt.png'
			plt.savefig (hist_obj_cnt_file)
			print '\n--- histogram of image count written to: ', hist_obj_cnt_file, '\n'
			plt.show ()
			if filetype == 'chips' :
				chip_sizes = [math.sqrt (int (res.text)) for key, chips in all_objs \
					for chip in chips for res in chip.findall ('resolution')]
				print '\naverage face size (NxN): ', int (sum (chip_sizes)/len (chip_sizes))
				print 'median face size  (NxN): ', int (np.median (chip_sizes))
				plt.title ('histogram of of face sizes')
				plt.xlabel ('N (image size=NxN)')
				plt.ylabel ('# chips (total=' + str (obj_count) + ')' )
				hist_info = plt.hist (chip_sizes, 20, facecolor='green', alpha=0.5)
				hist_chip_sizes_file = 'hist_chip_sizes.png'
				plt.savefig (hist_chip_sizes_file)
				print '\n--- histogram of chip sizes written to: ', hist_chip_sizes_file, '\n'
				plt.show ()
				tiny_chips = [chip for key, chips in all_objs \
					for chip in chips for res in chip.findall ('resolution') if int (res.text) < 22500]
				chip.attrib.get ('file')
				tiny_chips_names = [chip.attrib.get ('file') for chip in tiny_chips]
				# pdb.set_trace ()

		else :
			print '\n  ***  unable to show histogram: no access to display.  *** \n'

	if filetype == 'faces':
		print_faces_stats (write_stats)
	if print_files :
		objfiles.sort ()
		for objfile in objfiles:
			print '\t', objfile

##------------------------------------------------------------
##
##------------------------------------------------------------


##------------------------------------------------------------
##
##------------------------------------------------------------
def print_faces_stats (write_unused_images) :
	print "-----------------------------"
	print "....files with no faces : ", len (g_stats_few)
	print "....files with multiple faces: ", len (g_stats_many)
	# pdb.set_trace ()
	if write_unused_images:
		if len (g_stats_few) :
			stats_name = datetime.datetime.now().strftime("stats_few_%Y%m%d_%H%M")
			stats_fp = open (stats_name, "w")
			for face in g_stats_few:
				stats_fp.write (face + '\n')
			stats_fp.close ()
			print "... generated file:", stats_name
		if len (g_stats_many) :
			stats_name = datetime.datetime.now().strftime("stats_many_%Y%m%d_%H%M")
			stats_fp = open (stats_name, "w")
			for face in g_stats_many:
				stats_fp.write (face + '\n')
			stats_fp.close ()
			print "... generated file:", stats_name
	print ''

##------------------------------------------------------------
##  return xml files in directory
##------------------------------------------------------------
def get_xml_files (dir) :
	xml_files = []
	for dirname, dirs, files in os.walk (dir):
		# print "files: ", files
		for file in files:
			if (file.endswith ('.xml')):
				xml_files.append (os.path.join(dirname, file))
				# print "file: ", file
			# pdb.set_trace ()
	return xml_files

##------------------------------------------------------------
##   
##------------------------------------------------------------
def get_image_label_text (face) :
	box = face.findall ('box')
	label_list = box[0].findall ('label')
	label = label_list[0].text
	return label

##------------------------------------------------------------
##  get_new_face (face,faces_orig_d).  find matching file name
##------------------------------------------------------------
def get_new_face (face, faces_new_d) :
	imagefile_old = face.attrib.get ('file')
	label_old = get_image_label_text (face)
	pdb.set_trace ()
	for label_new, faces in faces_new_d.items () :
		if label_old != label_new :
			continue;
		# look for file name
		for face in faces :
			imagefile_new = face.attrib.get ('file')
			if imagefile_new == imagefile_old :
				return face
	return None


##------------------------------------------------------------
##  validate_file - create new file with only valid chip files
##------------------------------------------------------------
def validate_file (xml_file, output_file) :
	chips_d = defaultdict (list)
	filetype = 'chips'
	objfiles = load_objs_from_files ([xml_file], chips_d, filetype)
	valid_chips = []
	print ''
	for key, chips in chips_d.items () :  ## iterate through all chips
		for chip in chips :
			# pdb.set_trace ()
			chipfile = chip.attrib.get ('file')
			if os.path.exists (chipfile) :
				valid_chips.append (chip)
			else :
				print '\t...unable to find file: ', chipfile
	print '\n\tGenerated valid chip file: ', output_file
	print ''
	root, tree = create_new_tree_w_element (filetype)
	for chip in valid_chips :
		tree.append (chip)
	indent (root)
	tree = ET.ElementTree (root)
	tree.write (output_file)

##------------------------------------------------------------
##  replicate_file - create file of same list of images with new data
##------------------------------------------------------------
def replicate_file (orig_file, new_files, output_file) :
	faces_orig_d = defaultdict(list)
	faces_new_d = defaultdict(list)
	filetype = "faces"
	objfiles1 = load_objs_from_files (orig_file, faces_orig_d, filetype)
	objfiles2 = load_objs_from_files (new_files, faces_new_d, filetype)
	newfaces = []
	for key, faces in faces_orig_d.items () :  ## iterate through old list of tests
		for face in faces :
			# pdb.set_trace ()
			newface = get_new_face (face, faces_new_d) ## get new data for same file
			if newface :
				newfaces.append (newface)
			else :
				print 'unable to match file:  ', face.attrib.get ('file')
	root, tree = create_new_tree_w_element (filetype)
	for face in newfaces :
		tree.append (face)
	indent (root)
	tree = ET.ElementTree (root)
	tree.write (output_file)

##------------------------------------------------------------
##   main code
##------------------------------------------------------------
def do_generate_folds (input_files, n_folds, output_file, shuffle=True) :
	chips_d = defaultdict(list)
	load_objs_from_files (input_files, chips_d)
	## print "printing chips dictionary ... "
	## print_dict (chips_d)
	train_list, validate_list = generate_folds_content (chips_d, n_folds, shuffle)
	generate_folds_files (train_list, validate_list, output_file)

##------------------------------------------------------------
##  can be called with:
##    partition_files 80 20 -out xxx *.xml dirs
##    generate_folds 5 -out yyy *.xml dirs
##------------------------------------------------------------
def main (argv) :
    parser = argparse.ArgumentParser(description='Generate data for training.',
        formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
    parser.add_argument ('--partition', default=80,
        help='Parition data in two. Defaults to 80.')
    parser.add_argument ('--folds', default=5,
        help='Generate n sets of train/validate files. Defaults to 5.')
    parser.add_argument ('--output', default="",
        help='Output file basename.')
    parser.add_argument ('--verbosity', type=int, default=1,
        choices=[0, 1, 2], help="increase output verbosity")


if __name__ == "__main__":
	main (sys.argv)


## test split/partition.  use count with remainders
## import datetime
## datetime.datetime.now().strftime("%Y%m%d_%H%M")
## split x y (x+y=100)
## split n
## generate_partition_files 80 20 [xml_file_or_dir]+
## generate_folds_files 5 [xml_file_or_dir]+
