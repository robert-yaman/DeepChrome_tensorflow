import gzip
import numpy as np
import os
import urllib2
import StringIO

# EPIGENOMES = ["E000", "E003", "E004", "E005", "E006", "E007", "E011", "E012",
# 			  "E013", "E016", "E024", "E027", "E028", "E037", "E038", "E047", 
# 			  "E050", "E053", "E054", "E055", "E056", "E057", "E058", "E059", 
# 			  "E061", "E062", "E065", "E066", "E070", "E071", "E079", "E082",
# 			  "E084", "E085", "E087", "E094", "E095", "E096", "E097", "E098",
# 			  "E100", "E104"]

MODIFICATIONS = ["H3K4me3", "H3K4me1", "H3K36me3", "H3K9me3", "H3K27me3"]

BASE_TAGALIGN_URL = "http://egg2.wustl.edu/roadmap/data/byFileType/alignments/consolidated/"
RPKM_URL = "http://egg2.wustl.edu/roadmap/data/byDataType/rna/expression/57epigenomes.RPKM.pc.gz"

print "Downloading RPKM file..."
response = urllib2.urlopen(RPKM_URL)
compressedFile = StringIO.StringIO()
compressedFile.write(response.read())
compressedFile.seek(0)
decompressedFile = gzip.GzipFile(fileobj=compressedFile, mode='rb')

print "Done."
print "Processing RPKM..."

lines = decompressedFile.read().split("\n")
all_epigenomes = lines.pop(0).split("\t")[1:]

all_genes = []
expression_matrix = []

for line in lines:
	if line == '':
		continue
	elements = line.split("\t")
	all_genes.append(elements.pop(0))
	if elements[-1] == '':
		elements.pop()
	elements = [float(e) for e in elements]
	expression_matrix.append(elements)
expression_matrix = np.matrix(expression_matrix)

del response
del decompressedFile
del compressedFile
del lines

for j in range(expression_matrix.shape[1]):
	column = expression_matrix[:,j]
	median = np.median(column[0])
	for i in range(expression_matrix.shape[0]):
		expression_matrix[i,j] = 1 if expression_matrix[i,j] > median else 0

print"Done."
print "Creating BED file..."



# Create BED file
	# Create an array of all the genese
	# for each gene, get the starting point, then create an entry in the bed file

# Create temp folder
# Download all the files
	# data/tagalign
# Index/process all the files
	# data/bam
# create three csv files
# run multicov for each bam file and att to csv

# remove temp tagalign folder (don't actually do this until script is done)