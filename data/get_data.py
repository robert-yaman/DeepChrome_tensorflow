"""
Script for generating a complete dataset. The second argument is the location to store 
the dataset (very big).
"""

import gzip
import linecache
import os
import requests
import time
import shutil
import statistics
import StringIO
import subprocess
import urllib2
import sys

DATA_DIR = sys.argv[1] if len(sys.argv) > 1 else "./"
if not os.path.isdir("./data"):
	print "Please run from the root directory."
	sys.exit()
	
start_time = time.time()
def _time_elapsed():
	return str(time.time() - start_time)

RPKM_URL = "http://egg2.wustl.edu/roadmap/data/byDataType/rna/expression/57epigenomes.RPKM.pc.gz"

print "Downloading RPKM file..."
response = urllib2.urlopen(RPKM_URL)
compressedFile = StringIO.StringIO()
compressedFile.write(response.read())
compressedFile.seek(0)
decompressedFile = gzip.GzipFile(fileobj=compressedFile, mode='rb')

print "Done. Time elapsed: " + _time_elapsed()
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

# Final labels.
for j in range(len(expression_matrix[0])):
	column = [row[j] for row in expression_matrix]
	median = statistics.median(column)
	for i in range(len(expression_matrix)):
		expression_matrix[i][j] = 1 if expression_matrix[i][j] > median else 0

del response
del decompressedFile
del compressedFile
del lines

print "Done. Time elapsed: " + _time_elapsed()
print "Creating BED file..."

BED_PATH = DATA_DIR + "tmp_bed.bed"

ensembl_server = "http://rest.ensembl.org"
ext_pre = "/lookup/id/"
ext_post = "?expand=1"
deprecated_genes = []

# 5 hours
with open(BED_PATH, "w+") as bed_file:
	for gene in all_genes:
		request_url = ensembl_server + ext_pre + gene + ext_post
		request = requests.get(request_url, 
			headers={ "Content-Type" : "application/json"})
		if not request.ok:
			# Some genes are deprecated. We ignore for now.
			# TODO: Confirm we can skip these.
			print " -- Skipping gene: " + gene
			deprecated_genes.append(deprecated_genes)
			continue
		response = request.json()
		# We are interested in the area +- 5000 BP from TSS of start.
		start_area = max(int(response["start"]) - 5000, 0)
		end_area = int(response["start"]) + 5000 # check if too long?
		count = 0
		new_example = []
		for i in range(start_area, end_area + 1, 100):
			newline = "\t".join([
				"chr" + response["seq_region_name"],
				str(i),
				str(i + 100),
				gene,
			])
			new_example.append(newline)
			count += 1
		bed_file.write("\n".join(new_example) + "\n")


print "Done. Time elapsed: " + _time_elapsed()
print "Downloading tagalign files..."

# TODO: parallelize this if it's slow.

BASE_TAGALIGN_URL = "http://egg2.wustl.edu/roadmap/data/byFileType/alignments/consolidated/"
MODIFICATIONS = ["H3K4me3", "H3K4me1", "H3K36me3", "H3K9me3", "H3K27me3"]
TAGALIGN_DIR = DATA_DIR + "tmp_tagalign/"

os.makedirs(TAGALIGN_DIR)
for epigenome in all_epigenomes:
	for modification in MODIFICATIONS:
		filename = epigenome + "-" + modification + ".tagAlign"
		filename_gz = filename + ".gz"
		print " -- Downloading " + filename + "..."
		url = BASE_TAGALIGN_URL + filename_gz
		try:
			response = urllib2.urlopen(url)
			compressed_tagalign = StringIO.StringIO()
			compressed_tagalign.write(response.read())
			compressed_tagalign.seek(0)
			print " -- writing..."
			with open(TAGALIGN_DIR + filename + ".gz", "w") as gz_file:
				gz_file.write(compressed_tagalign.read())

			cmd = "gunzip " + TAGALIGN_DIR + filename
			subprocess.Popen(cmd.split())
		except:
			print "ERROR: unable to download + " + filename_gz
			continue

## shutil.rmtree(TAGALIGN_DIR)

print "Done. Time elapsed: " + _time_elapsed()
print "Processing tagalign files..."

BAM_DIR = DATA_DIR + "tmp_bam/"

os.makedirs(BAM_DIR)
for filename in os.listdir(TAGALIGN_DIR):
	if not filename.endswith(".tagAlign"):
		continue
	print " -- Processing " + filename
	bam_path = BAM_DIR + filename.split(".")[0] + ".bam"
	cmd = "bedtools bedtobam -i " + TAGALIGN_DIR + filename + " -g data/hg19chrom.sizes"
	output, error = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE).communicate()
	with open(bam_path, "w") as bam_file:
		bam_file.write(output)

	cmd = "samtools index " + bam_path
	subprocess.Popen(cmd.split())
	# The docs say we should sort the bam file, but multicov seems to work without this.

print "Done. Time elapsed: " + _time_elapsed()
print "Creating temp column files..."

COLUMN_DIR = DATA_DIR + "tmp_cols/"

os.makedirs(COLUMN_DIR)

# Temporary files to hold the columns of the dataset.
# Takes about five minutes per.
for filename in os.listdir(BAM_DIR):
	if not filename.endswith(".bam"):
		continue
	print " -- Processing " + filename
	bam_path = BAM_DIR + filename.split(".")[0] + ".bam"
	column_path_no_ext = filename.split(".")[0]
	column_path = filename.split(".")[0] + ".txt"
	cmd = "bedtools multicov -bams " + bam_path + " -bed " + BED_PATH
	output, error = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE).communicate()
	for line in output.split("\n"):
		if len(line.split("\n")) < 2:
			continue
		path = COLUMN_DIR + column_path_no_ext + "-" + line.split("\t")[-2] + ".txt" # gene name
		with open(path, "a") as column_file:
			val = line.split("\t")[-1]
			column_file.write(val + "\n")

print "Done. Time elapsed: " + _time_elapsed()
print "Creating csvs..."

os.remove(BED_PATH)	
shutil.rmtree(BAM_DIR)

num_genes_per_dataset = len(all_genes) / 3
training_genes = all_genes[0 : num_genes_per_dataset]
validation_genes = all_genes[num_genes_per_dataset + 1 : num_genes_per_dataset * 2]
testing_genes = all_genes[num_genes_per_dataset * 2 + 1:]

total_count = 0
for gene in all_genes:
	for epigenome in all_epigenomes:
		paths = [COLUMN_DIR + epigenome + "-" + modification + "-" + gene + ".txt" 
			for modification in MODIFICATIONS]

		if not all([os.path.isfile(path) for path in paths]):
			if not gene in deprecated_genes:
				print "ERROR: Skipping non-deprecated gene: " + gene
			continue
		# 5 paths - 1 for each modification.
		for i in range(sum(1 for line in open(paths[0])) - 1):
			epigenome_index = all_epigenomes.index(epigenome)
			gene_index = all_genes.index(gene)

			line = ",".join([str(n).rstrip() for n in [
				total_count,
				i % 100, # Spot in example,
				linecache.getline(paths[0], i + 1),
				linecache.getline(paths[1], i + 1),
				linecache.getline(paths[2], i + 1),
				linecache.getline(paths[3], i + 1),
				linecache.getline(paths[4], i + 1),
				expression_matrix[gene_index][epigenome_index], # label
			]]) + "\n"
			if gene in training_genes:
				with open(DATA_DIR + "data/training_data.csv", "a") as training_file:
					training_file.write(line)
			elif gene in validation_genes:
				with open(DATA_DIR + "data/validation_data.csv", "a") as validation_file:
					validation_file.write(line)
			elif gene in testing_genes:
				with open(DATA_DIR + "data/testing_data.csv", "a") as testing_file:
					testing_file.write(line)
			else:
				print "ERROR with gene: " + gene + "\n -- epigenome: " + epigenome
		total_count += 1

shutil.rmtree(COLUMN_DIR)

print "Done. Total time elapsed: " + _time_elapsed()






