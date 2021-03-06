import os
import time
import csv
import shutil
import subprocess
import random
import errno
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup


autoPath = "/home/mecore/Desktop/timp/fastq-automation/src/"
keepPath = "/mnt/heisenberg/"
archivePath = "/mnt/heisenberg/ARCHIVE/"
bigBirdPath = "/mnt/bigbird/"

def archiveMover (myRun) :
	
	takeMeToBigBirdLogger(0, "The FASTQ files of %s are being added to the ARCHIVE on Heisenberg" % myRun["runName"], 1)
	
	#p1 is run folder path
	#p2 is run name
	p1 = myRun["Path"]
	p3 = myRun["outputFolderLocation"]

	#if not os.path.isdir(p2):
	#	os.mkdir(p2)
	
	#print(p2)
	
	
	try:
		archiveMovePath = os.path.join(archivePath, myRun["runInstrument"], myRun["runName"], "")
		moveCheck3 = subprocess.run(["scp", "-r", myRun["outputFolderLocation"], archiveMovePath])
		moveCheck4 = subprocess.run(["scp", "-r", os.path.join(myRun["Path"], "Interop"), archiveMovePath])
		os.rename(os.path.join(archiveMovePath, "Interop", ""), os.path.join(archiveMovePath, "Interop_" + myRun["runName"], ""))
		takeMeToBigBirdLogger(0, 'FASTQ Files are in ARCHIVE', 2)
	except Exception as e:
		takeMeToBigBirdLogger(0, 'There was an issue moving the FASTQ files to the ARCHIVE on Heisenberg: %s' % e, 2)

	return myRun

def bcl2fastqRun ( myRun ):
	
	myRun = textCheckGenerator(myRun)
	
	myRun = sampleSheetReader(myRun)
	myRun = runInfoReader(myRun)
	
	archiveFolderPath = os.path.join(archivePath, myRun["runInstrument"], myRun["runName"])
	
	try:
    		os.mkdir(archiveFolderPath)
	except OSError as exc:
    		if exc.errno != errno.EEXIST:
        		raise
    		pass
	
	#takeMeToBigBirdLogger(0, "Making a copy of %s" % myRun["Path"], 1)
	
	#shutil.copytree(myRun["Path"], os.path.join(keepPath, "ARCHIVE", myRun["runInstrument"], myRun[""""))
	dashboardUpdater('currently_running', 'Backing up run folder to ARCHIVE...', myRun)
	subprocess.run(["scp", "-r", "-v", myRun["Path"], archiveFolderPath])

	myRun["outputFolderLocation"] = os.path.join(myRun["Path"],"FASTQ_Files_" + myRun["runName"], "")
	
	try:
    		os.mkdir(myRun["outputFolderLocation"])
	except OSError as exc:
    		if exc.errno != errno.EEXIST:
        		raise
    		pass
	
	dashboardUpdater('currently_running', 'Running bcl2fastq...', myRun)
	if myRun["libraryType"] == "10x":

		successOrNot = bcl2fastqHelper(myRun, readLength = "8")
	else:
		successOrNot = bcl2fastqHelper(myRun)

	
	if successOrNot.returncode != 0:
		successOrNot = bcl2fastqHelper(myRun, barcodeMismatches = "0", loggerMessage =  "RUN FAILED, RUNNING AGAIN WITH FEWER ALLOWED MISMATCHES")

	successOrNot = postRunIndexChecker(myRun, successOrNot)
	
	
	return successOrNot.returncode

def bcl2fastqHelper(myRun, readLength = "35", barcodeMismatches = "1", sampleSheetName = 'SampleSheet.csv', loggerMessage = "STARTING BCL2FASTQ RUN on %s"):
	
	try:
		loggerMessage = loggerMessage % myRun["Path"]
	except:
		pass
	
	takeMeToBigBirdLogger(1, loggerMessage, 1)

	if not isinstance(readLength, str):
		readLength = str(readLength)
		
	
	bcl2fastqCheck = open(os.path.join(myRun["Path"], "bcl2fastqCheck.txt"), 'a+')
	
	successOrNot = subprocess.run(["bcl2fastq", "-R", myRun["Path"],  "--sample-sheet", os.path.join(myRun["Path"], sampleSheetName), "--ignore-missing-bcls", "--ignore-missing-filter", "--ignore-missing-positions", "--ignore-missing-controls", "--find-adapters-with-sliding-window", "--adapter-stringency", "0.9", "--mask-short-adapter-reads", readLength, "--minimum-trimmed-read-length", readLength, "--barcode-mismatches", barcodeMismatches, "-o", myRun["outputFolderLocation"]], stdout=bcl2fastqCheck, stderr=subprocess.STDOUT)
	
	bcl2fastqCheck.close()
	
	return successOrNot

def bigBirdMover ( myRun ):
	
	takeMeToBigBirdLogger(1, "The directory is being taken to Big Bird", 1)
	
	#p1 is run folder path
	#p2 is run name
	p2 = os.path.join(bigBirdPath,myRun["runInstrument"],myRun["runName"], "")
	p1 = myRun["Path"]
	p3 = myRun["outputFolderLocation"]
	archiveMovePath = os.path.join(archivePath, myRun["runInstrument"], myRun["runName"], "")

	if not os.path.isdir(p2):
		os.mkdir(p2)
	
	#print(p2)
	
	try:
		moveCheck2 = subprocess.run(["scp", "-r", myRun["outputFolderLocation"], p2])
		if moveCheck2.returncode == 0:
			try:
				shutil.rmtree(p3)
			except:
				pass
		moveCheck1 = subprocess.run(["scp", "-r","-v", myRun["Path"], p2])
		moveCheck3 = subprocess.run(["scp", "-r", os.path.join(archiveMovePath, "Interop_"+myRun["runName"], ""), p2])
	except:
		pass
		

	if moveCheck2.returncode == 0:
		try:
			shutil.rmtree(p3)
		except:
			pass
	


	moveCheck = moveCheck1.returncode == 0 and moveCheck2.returncode == 0 and moveCheck3.returncode == 0
	
		
	if moveCheck:
		
		myRun["Path"] = os.path.join(p2, myRun["folderName"], "")
		myRun["outputFolderLocation"] = os.path.join(p2, "FASTQ_Files_" + myRun["runName"], "")
		oldFolder = os.path.join(myRun["Path"], "FASTQ_Files_" + myRun["runName"], "")
		takeMeToBigBirdLogger(0, "The directory should be in Big Bird at %s" % myRun["Path"], 2)
		
		shutil.rmtree(p1)
	
	else:
		takeMeToBigBirdLogger(0, "There was an issue moving the directory to Big Bird.", 2)
	
	return myRun

def complementMaker(seqString):

	complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
	reverse_complement = "".join(complement.get(base, base) for base in reversed(seqString))
	
	return reverse_complement
	
def csvIndexRipper(myRun, listOfUnknowns):

	#listOfUnknowns = list(set(listOfUnknowns))

	with open(os.path.join(myRun["Path"], "SampleSheet.csv"), 'r') as csvOpened:
		csvReads = csv.reader(csvOpened,delimiter=',', quotechar='|')
		sampleSheet = []
		index_1 = 0
		index_2 = 0
		indexFails = 0
		totalIndices = 0


		marker = False
		dualIndex = False
		indexFailed = False

		for row in enumerate(csvReads):

			if marker and not dualIndex:
				break
			elif marker:
				
				totalIndices += 1
				
				sheet_i7 = row[1][index_1]
				sheet_i5 = row[1][index_2]
				'''
				for unknownIndex in listOfUnknowns:
					print(unknownIndex)
					if sheet_i7 == unknownIndex[0] and sheet_i5 == complementMaker(unknownIndex[1]):
						indexFailed += 1
						print("YES: ", unknownIndex, complementMaker(row[1][index_2]))
						row[1][index_2] = complementMaker(row[1][index_2])
						continue
				'''
				
				if [sheet_i7, complementMaker(sheet_i5)] in listOfUnknowns:
					indexFailed = True
					print("Yes: ", sheet_i7, sheet_i5)
					row[1][index_2] = complementMaker(row[1][index_2])

			if row[1] and row[1][0] == "Sample_ID":

					for index, value in enumerate(row[1]):
						
						if value == 'index':
							index_1 = index 
						elif value == 'index2':
							dualIndex = True
							index_2 = index

					marker = True

			#print(row[1])
			sampleSheet.append(row[1])

	if indexFailed:
		print("CorrectedSampleSheet.csv")
		newName = "CorrectedSampleSheet.csv"

		with open(os.path.join(myRun["Path"], newName), 'w', newline='', encoding='utf-8') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
			
			for row in sampleSheet:
				spamwriter.writerow(row)

	return(indexFailed)

def dashboardUpdater ( str1, str2, myRun ):
	
	dashboard_path_list = ["/mnt/heisenberg/dashboard.html", "/mnt/bigbird/fangtest/dashboard.html"]

	for dashboard_path in dashboard_path_list:

		with open(dashboard_path, 'r') as f:

			contents = f.read()

			soup = BeautifulSoup(contents, 'lxml')

			if str1 == 'currently_running':
				current_task = soup.find('span', {'id' : 'current_task'})
				current_task.string = str2
				
				run_or_time = soup.find('span', {'id' : 'run_or_time'})
				run_or_time.string = 'CURRENT RUN: '
				
				current_run = soup.find('span', {'id' : 'current_run_or_time'})
				current_run.string = myRun["runName"]
				
			elif str1 == "currently_waiting":
			
				current_task = soup.find('span', {'id' : 'current_task'})
				current_task.string.replace_with(str2)
				
				run_or_time = soup.find('span', {'id' : 'run_or_time'})
				run_or_time.string = 'NEXT CHECK TIME: '
				
				current_run = soup.find('span', {'id' : 'current_run_or_time'})
				current_run.string = myRun["runName"]
			
			elif str1 == 'run_checks':
				runblock2 = soup.find(id='runblock')
				#print(type(runblock2))
				run_list = runblock2.find('span', {'class' : 'runfolder'})
				#print("run_list: ", run_list)

				new_tag = soup.new_tag('span', **{'class':'runfolder'}, id=myRun["folderName"])
				new_tag.string= myRun["folderName"] + ": " + str2
				new_tag.append(soup.new_tag('br'))

				runblock2.insert(4, new_tag)
				
				current_run = soup.find('span', {'id' : 'current_run_or_time'})
				current_run.string = myRun["folderName"]

			elif str1 == 'run_clear':
				elements = soup.find_all("span", **{'class':'runfolder'})

				for element in elements:
					element.decompose()


		with open(dashboard_path, 'w') as f:
			f.write(str(soup))
	
	return

def fastQCRunner ( myRun ):

	bcl2fastqCheck = open(os.path.join(myRun["Path"], "bcl2fastqCheck.txt"), 'a+')

	takeMeToBigBirdLogger(1, "Running FastQC and multiQC...", 1)
	
	#keepPath = "/mnt/heisenberg/ARCHIVE/Fangs_Special_Test_Folder/fastqc_tests/MW59_basespace_unpacked/"
	Results = os.path.join(myRun["outputFolderLocation"], "FASTQC_Results")

	try:
		os.mkdir(Results)
	except:
		pass
	
	numbEr = 16

	allFastqFiles = [ f.path for f in os.scandir(os.path.join(myRun["outputFolderLocation"], myRun["runName"])) if not f.is_dir() ]
	littleContainer = []
	bigContainer = []

	for index, fastqPath in enumerate(allFastqFiles):
	
		littleContainer.append(fastqPath)
	
		if index % numbEr == numbEr - 1:
			bigContainer.append(littleContainer)
			littleContainer = []
		
	
	if littleContainer:
		bigContainer.append(littleContainer)
		
	for index, fastqFiles in enumerate(bigContainer):
		
		command = ["fastqc", "-q", "--threads", str(numbEr + 8), "--outdir", Results]
		commands = command + fastqFiles
	
		subprocess.run(commands, stdout=bcl2fastqCheck, stderr=subprocess.STDOUT)
	
	multiqcCommands = ["/home/mecore/.local/bin/multiqc", Results, "-o", os.path.join(myRun["outputFolderLocation"], "MultiQC_results")]
	subprocess.run(multiqcCommands, stdout=bcl2fastqCheck, stderr=subprocess.STDOUT)
	
	bcl2fastqCheck.close()
	takeMeToBigBirdLogger(0, "FastQC and multiQC done!", 2)
	
	return

def runInfoReader ( myRun ):

	#print("I'm reading %s" % pth)
	
	runInstrument = ""

	runInfoTree = ET.parse(os.path.join(myRun["Path"], "RunInfo.xml"))
	runInfoRoot = runInfoTree.getroot()
	instrumentIdent = runInfoRoot[0][1].text.strip()
	myRun["FlowcellID"] = runInfoRoot[0][0].text.strip()
	
	if instrumentIdent == "MN00206":
		myRun["runInstrument"] = "MiniSeq"
	elif instrumentIdent == "NB501662":
		myRun["runInstrument"] = "NextSeq"
	elif instrumentIdent == "A01113":
		myRun["runInstrument"] = "NovaSeq"
	elif instrumentIdent == "M01562":
		myRun["runInstrument"] = "MiSeq"
	elif instrumentIdent == "FS10000715":
		myRun["runInstrument"] = "iSeq"
	else:
		myRun["runInstrument"] = "UNKNOWN"

	takeMeToBigBirdLogger(0,"It was performed by the %s" % myRun["runInstrument"], 1)

	#print ("This is run on %s" % runInstrument);
	return myRun

def postRunIndexChecker(myRun, successOrNot):
	listOfUnknowns = unknownBarcodesRipper(myRun)
	indexComplementFail = csvIndexRipper(myRun, listOfUnknowns)

	if indexComplementFail:

		if myRun["libraryType"] == "10x":
			readLength = "8"
		else:
			readLength = "35"

		successOrNot = bcl2fastqHelper(myRun, readLength, sampleSheetName = "CorrectedSampleSheet.csv", loggerMessage = "Rerunning bcl2fastq on %s because of index complement issue.")


	return successOrNot

def sampleSheetReader ( myRun ):

	sampleSheetPath = os.path.join(myRun["Path"], "SampleSheet.csv")
	
	sampleSheetArray = []
	sampleStart = 0
	
	with open(sampleSheetPath, newline='') as csvFile:
		spamreader = csv.reader(csvFile, delimiter=',', quotechar='|')
		for index, row in enumerate(spamreader):

			if row:
				if row[0] == '[Data]':
					sampleStart = index + 1
		
			sampleSheetArray.append(row)
	
	
	myRun = tenXIndexCheck(sampleSheetArray, sampleSheetPath, sampleStart, myRun)

		
	
	
	secondRow = sampleSheetArray[2]
	runName = secondRow[1]
	runName = runName.strip()
	
	myRun["runName"] = runName
	
	takeMeToBigBirdLogger(1, "The run I'm copying into the archive is called %s" % runName, 1)
	return myRun

def takeMeToBigBirdLogger( num2, massagers, num1 ):

	nowTime = datetime.now()
	date_time = nowTime.strftime("%m/%d/%Y, %H:%M:%S>> ")

	logLine = date_time + massagers
	for i in range(num1):
		logLine = logLine + "\n"
		
	for i in range(num2):
		logLine = "\n" + logLine
	
	with open(os.path.join(archivePath, "takeMeToBigBird_logs", "takeMeToBigBirdLog.txt"), "a+") as text_file:
		text_file.write(logLine)
	
	return

def tenXIndexCheck (sampleSheetArray, sampleSheetPath, sampleStart, myRun):

	#tenx_path
	jsonFilePath = os.path.join(autoPath, "bcl2fastqRunner", "10x_indices.json")

	with open(jsonFilePath, 'r', encoding='utf-8') as f:
    		dict_of_indices = json.load(f)
	
	#print(sampleSheetArray)
	I7_Index_ID = sampleSheetArray[sampleStart].index('I7_Index_ID')
	I5_Index_ID = sampleSheetArray[sampleStart].index('I5_Index_ID')
	index2 = sampleSheetArray[sampleStart].index('index2')
	index1 = sampleSheetArray[sampleStart].index('index')
	
	tenx_test = sampleSheetArray[sampleStart + 1]
	
	try:
		if [tenx_test[index1]] in dict_of_indices:
			takeMeToBigBirdLogger(0, 'I think this maybe a 10x run. Generating workflow_b indices for sample sheet.', 1)
			myRun["libraryType"] = "10x"
			
			for ooh in range(sampleStart + 1, len(sampleSheetArray)):
				gash = sampleSheetArray[ooh]
				
				if gash[index1] in dict_of_indices:
					sampleSheetArray[ooh][I5_Index_ID] = dict_of_indices[gash[index1]]
					sampleSheetArray[ooh][index2] = dict_of_indices[gash[index1]]


			#print(sampleSheetArray)

			with open(sampleSheetPath, 'w', newline='', encoding='utf-8') as csvfile:
				spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
			
				for row in sampleSheetArray:
					print(sampleSheetPath, row)
					spamwriter.writerow(row)
	except:
		pass
	
	return myRun


def textCheckGenerator ( myRun ):
	
	pth = myRun["Path"]
	textName = os.path.join(pth, "bcl2fastqCheck.txt")
	"""
	slashIndex = [i for i, char in enumerate(pth) if char == "/"]
	weirdID = pth[slashIndex[-1]+1:]
	myRun["folderName"] = weirdID
	"""
	
	weirdID = myRun["folderName"]
	
	nowTime = datetime.now()
	date_time = nowTime.strftime("%m/%d/%Y, %H:%M:%S > ")
	
	with open(textName, "a+") as textFile:
		textFile.write(date_time + weirdID + "\n")
		
	return myRun

def unknownBarcodesRipper(myRun):
	with open(os.path.join(myRun["outputFolderLocation"], "Stats", "Stats.json"), 'r') as openJson:
		demuxStats = json.load(openJson)

	listOfUnknowns = []

	for listHold in demuxStats["UnknownBarcodes"]:
		if listHold["Barcodes"]:
			listOfUnknowns.extend(list(listHold['Barcodes'])[0:10])

	listOfUnknowns = [n.split("+") for n in listOfUnknowns]

	return listOfUnknowns

def main() :
	'''
	subjectRun = {"Path": "/mnt/bigbird/NovaSeq/BX02/210930_A01113_0043_AHLJFNDRXY", "folderName":"210930_A01113_0043_AHLJFNDRXY", "runName": "BX02", "runInstrument":"NovaSeq", "FlowcellID":"", "outputFolderLocation":"/mnt/bigbird/NovaSeq/BX02/FASTQ_Files_BX02", "libraryType":"10x", "outputErrors":[]}

	runCheck = postRunIndexChecker(subjectRun, True)
	'''
	'''
	print(runCheck)
	
	fastQCRunner(subjectRun)
	directoryMover(subjectRun)
	
	return
	'''
main()
