import os
import shutil
import subprocess

# Copy over tagaligns from tagaligns since tmp_ folders will be cleaned up by 
# the script
os.makedirs("data_test/tmp_tagalign")
for tagalign_path in os.listdir("data_test/tagaligns/"):
	shutil.copyfile("data_test/tagaligns/" + tagalign_path, 
		"data_test/tmp_tagalign/" + tagalign_path)

cmd = "python data/get_data.py --data-dir data_test/ --rpkm data_test/test_rpkm.RPKM.pc --provide-tagaligns"

subprocess.Popen(cmd.split(), stdout=subprocess.PIPE).communicate()

csvs = ["testing_data.csv", "training_data.csv", "validation_data.csv"]
for csv in csvs:
	failed = False
	with open("data_test/data/" + csv) as test_file:
		with open("data_test/answer_data/" + csv) as answer_file:
			if test_file.read() == answer_file.read():
				print csv + " OKAY"
			else:
				print "TEST FAILED FOR " + csv
				failed = True
	if not failed:
		os.remove("data_test/data/" + csv)	

os.remove("data_test/tmp_bed.bed")	
shutil.rmtree("data_test/tmp_bam/")
shutil.rmtree("data_test/tmp_tagalign/")
