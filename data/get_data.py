# Script for generating a complete dataset. Takes a long time!

import argparse
import pybedtools
import gzip
from multiprocessing import Pool
import os
import requests
import time
import shutil
import statistics
import StringIO
import subprocess
import urllib2
import sys

parser = argparse.ArgumentParser()
# Input Arguments
parser.add_argument(
	'--data-dir',
	help='Must contain a data/ directory for output csvs. ./ if unspecified',
)
parser.add_argument(
	'--rpkm',
	help='Local path for rpkm file. Used for testing.',
)
parser.add_argument(
	'--provide-tagaligns',
	help='The tmp_tagalign folder will be manually created. Used for testing',
	action='store_true'
)

args = parser.parse_args()

DATA_DIR = args.data_dir if len(sys.argv) > 1 else "./"
if not DATA_DIR.endswith("/"):
	DATA_DIR = DATA_DIR + "/"

if not os.path.isdir("./data"):
	print "Please run from the root directory."
	sys.exit()
	
start_time = time.time()
def _time_elapsed():
	return str(time.time() - start_time)

RPKM_URL = "http://egg2.wustl.edu/roadmap/data/byDataType/rna/expression/57epigenomes.RPKM.pc.gz"

print "Downloading RPKM file..."
if args.rpkm == None:	
	response = urllib2.urlopen(RPKM_URL)
	compressedFile = StringIO.StringIO()
	compressedFile.write(response.read())
	compressedFile.seek(0)
	decompressedFile = gzip.GzipFile(fileobj=compressedFile, mode='rb')
else:
	decompressedFile = open(args.rpkm)

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

del decompressedFile
del lines

print "Done. Time elapsed: " + _time_elapsed()
print "Creating BED file..."

BED_PATH = DATA_DIR + "tmp_bed.bed"

ensembl_server = "http://rest.ensembl.org"
ext_pre = "/lookup/id/"
ext_post = "?expand=1"
deprecated_genes = []

with open(BED_PATH, "w+") as bed_file:
	for gene in all_genes:
		request_url = ensembl_server + ext_pre + gene + ext_post
		request = requests.get(request_url, 
			headers={ "Content-Type" : "application/json"})
		if not request.ok:
			# Some genes are deprecated. We ignore for now.
			# TODO: Confirm we can skip these.
			print " -- Skipping gene: " + gene
			deprecated_genes.append(gene)
			continue
		response = request.json()
		# We are interested in the area +- 5000 BP from TSS of start.
		start_area = max(int(response["start"]) - 5000, 0)
		end_area = int(response["start"]) + 5000 # check if too long?
		count = 0
		new_example = []
		for i in range(start_area, end_area, 100):
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

BASE_TAGALIGN_URL = "http://egg2.wustl.edu/roadmap/data/byFileType/alignments/consolidated/"
MODIFICATIONS = ["H3K4me3", "H3K4me1", "H3K36me3", "H3K9me3", "H3K27me3"]
TAGALIGN_DIR = DATA_DIR + "tmp_tagalign/"

if not args.provide_tagaligns:
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

print "Done. Time elapsed: " + _time_elapsed()
print "Processing tagalign files..."

BAM_DIR = DATA_DIR + "tmp_bam/"

os.makedirs(BAM_DIR)
for filename in os.listdir(TAGALIGN_DIR):
	if not filename.endswith(".tagAlign"):
		continue
	print " -- Processing " + filename
	bam_path = BAM_DIR + filename.split(".")[0] + ".bam"
	cmd = "bedtools bedtobam -i " + TAGALIGN_DIR + filename + " -g hg19chrom.sizes"
	output, error = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE).communicate()
	with open(bam_path, "w") as bam_file:
		bam_file.write(output)

	cmd = "samtools index " + bam_path
	subprocess.Popen(cmd.split())
	# The docs say we should sort the bam file, but multicov seems to work 
	# without this.

print "Done. Time elapsed: " + _time_elapsed()
print "Creating intermediary CSVs..."

CSV_DIR = DATA_DIR + "tmp_csvs/"
os.makedirs(CSV_DIR)

num_genes_per_dataset = len(all_genes) / 3
training_genes = all_genes[0 : num_genes_per_dataset]
validation_genes = all_genes[num_genes_per_dataset: num_genes_per_dataset * 2]
testing_genes = all_genes[num_genes_per_dataset * 2:]

# Order the bams lexicographically by epigenome, then modification.
ordered_bams = []
for epigenome in all_epigenomes:
	for modification in MODIFICATIONS:
		path = BAM_DIR + epigenome + "-" + modification + ".bam"
		if not os.path.isfile(path):
			print " -- No bam file: " + path
			continue
		ordered_bams.append(path)


def process(bams):
	# Takes a set of bams with the same epigenome, runs multicov, and outputs 
	# results in an appropriate csv file.
	print  " -- Starting new process for " + str(bams[0])

	cmd = "bedtools multicov -bams " + " ".join(bams) + " -bed " + BED_PATH

	output, error = subprocess.Popen(cmd.split(), 
		stdout=subprocess.PIPE).communicate()
	output_matrix = [line.split("\t") for line in output.split("\n")]
	# Last element is empty line
	output_matrix.pop()

	print " ---- multicov complete. Adding to csvs"
	total_count = 0
	for i in range(len(output_matrix) / 100):
		section = output_matrix[i * 100 : i * 100 + 100]

		if not all([len(s) == len(section[0]) for s in section]):
			print "ERROR: multicov partition has different lengths"
			sys.exit()

		gene_array = [j[3] for j in section]
		if not all([gene == gene_array[0] for gene in gene_array]):
			print("ERROR: multicov partition has different genes: " + 
				str(gene_array))
			sys.exit()
		gene = gene_array[0]
		csv_lines = []
		for j in range(4, len(section[0]), 5):
			epigenome_index = (j - 4) / 5
			gene_index = all_genes.index(gene)

			example = [row[j : j + 5] for row in section]
			label = expression_matrix[gene_index][epigenome_index]
			example_lines = ""
			for row in example:
				example_lines += str(total_count / 100) + ","
				example_lines += str(total_count % 100) + ","
				example_lines += ",".join(row)
				example_lines += "," + str(label) + "\n"
				total_count += 1
			csv_lines.append(example_lines.rstrip())
		epigenome_names = [bam.split("/")[2].split("-")[0] for bam in bams]
		if not all(epigenome_name == epigenome_names[0] for epigenome_name in epigenome_names):
			print "ERROR: mismatching epigenome names: " + str(epigenome_names)
		epigenome_name = epigenome_names[0]
		with open(CSV_DIR + epigenome_name + "-" + gene + ".csv", "a") as csv_file:
			csv_file.write("\n".join(csv_lines) + "\n")

		print  " -- Ending process for " + str(bams[0])

# This is costly, so run asynchronously on batches of 5.
if not len(ordered_bams) % 5 == 0:
	print "ERROR: incorrect number of bams: " + str(len(ordered_bams))
num_pools = len(ordered_bams) / 5
pool = Pool(processes=num_pools)
bam_partitions = [ordered_bams[i*5 : i*5+5] for i in range(num_pools)]
pool.map(process, bam_partitions)


print "Done. Time elapsed: " + _time_elapsed()
print "Concatenating CSVs..."

for filename in os.listdir(CSV_DIR):
	if not filename.endswith(".csv"):
		continue
	gene = filename.split("-")[1].split(".")[0]
	if gene in training_genes:
		csv_dir = DATA_DIR + "data/training_data.csv"
	elif gene in validation_genes:
		csv_dir = DATA_DIR + "data/validation_data.csv"
	elif gene in testing_genes:
		csv_dir = DATA_DIR + "data/testing_data.csv"

	with open(csv_dir, "a") as final_csv:
		with open(CSV_DIR + filename, "r") as intermediary_csv:
			final_csv.write(intermediary_csv.read())

print "Done. Time elapsed: " + _time_elapsed()
print "Cleaning up..."

# os.remove(BED_PATH)	
# shutil.rmtree(TAGALIGN_DIR)
# shutil.rmtree(BAM_DIR)

print "Done. Total time elapsed: " + _time_elapsed()
