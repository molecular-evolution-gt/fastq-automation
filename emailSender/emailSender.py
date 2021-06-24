import os
import lxml.etree
import lxml.html
from lxml.cssselect import CSSSelector
import xml.etree.ElementTree as ET
from lxml.html import builder as BXC
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.message import EmailMessage

bigBirdPathTest = "/home/mecore/Desktop/timp/automation/testfolder_site/fakeBigBird/"
bigBirdPath = "/run/user/1000/gvfs/smb-share:server=bigbird.ibb.gatech.edu,share=ngs/"
subjectRun = {"Path": "", "folderName": "", "runName": "", "runInstrument":"", "FlowcellID":"", "outputFolderLocation":""}

def cssHunter ( str1, parsedFile ):

	mySelector = CSSSelector(str1)
	selectorElement = mySelector(parsedFile)
	
	return selectorElement

def bcl2fastqHTMLScraper ( myRun ):
	"""
	if os.path.isdir(os.path.join(bigBirdPath, myRun["runInstrument"], myRun["runName"], "FASTQ_Output", "")):
		indexPath = os.path.join(bigBirdPath, myRun["runInstrument"], myRun["runName"], "FASTQ_Output", "Reports", "html", myRun["FlowcellID"], "all", "all", "all", "lane.html")
	elif os.path.isdir(os.path.join(bigBirdPath, myRun["runInstrument"], myRun["runName"], myRun["folderName"], "FASTQ_Output", "")):
		indexPath = os.path.join(bigBirdPath, myRun["runInstrument"], myRun["runName"], myRun["folderName"], "FASTQ_Output", "Reports", "html", myRun["FlowcellID"], "all", "all", "all", "lane.html")
	else:
		indexPath = bigBirdPathTest
	"""
	indexPath = os.path.join(myRun["outputFolderLocation"], "Reports", "html", myRun["FlowcellID"], "all", "all", "all", "lane.html")
	
	laneFile = HTMLFileParse(indexPath)
	
	tableAll = cssHunter( 'table', laneFile )
	
	table1 = tableAll[1]
	
	print(lxml.html.tostring(table1, pretty_print = True, encoding = "unicode"))
	
	table2 = tableAll[2]

	return [table1, table2]
	
def emailDrafter( myRun ): 
	
	tableBcl2fastq = bcl2fastqHTMLScraper(myRun)
	
	myEmail = BXC.HTML(
			BXC.BODY(
				BXC.P(BXC.I("The run %s, which was run on %s, has been processed.\n\n\n" % (myRun["runName"], myRun["runInstrument"])), 
				BXC.BR(), BXC.I("You should be able to find the folder on Big Bird."),
				BXC.BR(), BXC.I("Please see the drafted email for customers below:")),
				
				BXC.P("Hello,",
				BXC.BR(),
				BXC.BR(), "Thank you for choosing the Molecular Evolution Core's Next-Generation Sequencing facilities for your samples. \
				Your sequencing run has finished and your samples have been converted into FASTQ files for your own analysis. \
				Please follow the link below to access your sample data.",
				BXC.BR(), BXC.BR(), "[INSERT RESILIO LINK HERE]", 
				BXC.BR(), 
				BXC.BR(), "Here is a sequencing data report for the entire flowcell:", 
				
				BXC.BR(), BXC.BR(), BXC.B("Flowcell summary")),
				tableBcl2fastq[0],
				#"\n",
				BXC.P(BXC.B("Lane summary")),
				
				tableBcl2fastq[1],
				
				BXC.BR(),
				BXC.P("Attached to this document is a general statistical summary of the run generated using ", 
				BXC.A("MultiQC", href="https://multiqc.info/"), 
				" which consolidates the results of our quality control software ", BXC.A("FASTQC", 
				href="https://www.bioinformatics.babraham.ac.uk/projects/fastqc/"),".",
				BXC.BR(),
				BXC.BR(),  "Please let us know if you have any questions!"),
				
				BXC.P("Thanks so much,",
				BXC.BR(),
				BXC.BR(), "Molecular Evolution Core",
				BXC.BR(),),
				BXC.P(BXC.BR(),"Parker H. Petit Institute for Bioengineering and Bioscience",
				BXC.BR(), "950 Atlantic Drive, N.W., Krone Engineered Biosystems Building 2034",
				BXC.BR(), "Atlanta, Georgia 30332",
				BXC.BR(),
				BXC.BR(), "Office - 404.385.4749",
				BXC.BR(), "ngs@ibb.gatech.edu",
				BXC.BR(), "http://www.petitinstitute.gatech.edu/research/molecular-evolution-core",
				style="font-size: 75%")
				
				
			)
		)
	"""
	if os.path.isdir(os.path.join(bigBirdPath, myRun["runInstrument"], myRun["runName"], "FASTQ_Output", "")):
		indexPath = os.path.join(bigBirdPath, myRun["runInstrument"], myRun["runName"], "FASTQ_Output", "Reports")
	elif os.path.isdir(os.path.join(bigBirdPath, myRun["runInstrument"], myRun["runName"], myRun["folderName"], "FASTQ_Output", "")):
		indexPath = os.path.join(bigBirdPath, myRun["runInstrument"], myRun["runName"], myRun["folderName"], "FASTQ_Output", "Reports")
	else:
		indexPath = bigBirdPathTest
	"""
	indexPath = os.path.join(myRun["outputFolderLocation"], "Reports",)
	
	myEmail = HTMLWriter(myEmail, indexPath)
	
	return indexPath

def emailSender(onePath, myRun):
	
	msg = MIMEMultipart()
	
	with open(os.path.join(onePath, "emailDraft.html")) as html:
		emailDrafted = MIMEText(html.read(), "html")
	
	msg.attach(emailDrafted)

	fileName = os.path.join(myRun["outputFolderLocation"], "MultiQC_results", "multiqc_report.html")
	filesRealName = "MultiQC_Report_%s.html" % myRun["runName"]
	
	with open(fileName, "rb") as attachment:
		multiQCReport = MIMEApplication(attachment.read())
		multiQCReport.add_header('Content-Disposition', 'attachment', filename=filesRealName)
	
	msg.attach(multiQCReport)
	
	recipientEmails = ["fangshi75@gmail.com", "fangshi@gatech.edu"]
	ccEmails = ["fangshi90@gmail.com"]
	msg["Subject"] = 'Sequencing Results Available: ' + myRun["runName"]
	msg["From"] = "molecular.evolution@outlook.com"
	msg["To"] = ','.join(recipientEmails)
	msg["CC"] = ",".join(ccEmails)

	port = 587
	password = "MolEvol1@GT"
	
	context = ssl.create_default_context()
	
	with smtplib.SMTP("smtp.office365.com", port) as server:
		server.starttls(context=context)
		server.login("molecular.evolution@outlook.com", password)
		server.send_message(msg)
	
	
	
def HTMLFileParse ( str1 ):

	r = lxml.html.parse(str1).getroot();
	
	return r
	
def HTMLWriter ( myObj, folderPath ):

	outPut = lxml.html.tostring(myObj, pretty_print = True, encoding = "unicode")
	emailPath = os.path.join(folderPath, "emailDraft.html")
	
	with open(emailPath, "w") as text_file:
		text_file.write(outPut)
	
	return outPut

"""
def multiQCScraper ( myRun ):

	indexPath = os.path.join(bigBirdPath, myRun["runInstrument"], myRun["runName"], "FASTQ_Output", "MultiQC_results", "multiqc_report.html")
	
	laneFile = HTMLFileParse(indexPath)
	
	specialTable = laneFile.get_element_by_id("general_stats_table_container");
	#print(lxml.html.tostring(specialTable))
	
	#tableAll = cssHunter( 'div.general_stats', laneFile )

	return specialTable
"""
	
def emailSendingWrapper( myRun ):
	
	emailLocation = emailDrafter(myRun)
	emailSender(emailLocation, myRun)
	
	return
	
def main():
	
	"""
	subjectRunTest = {"Path": "", "runName": "EH08", "runInstrument":"NovaSeq", "FlowcellID":"H5KWGDRXY", "outputFolderLocation":""}
	subjectRunTest["outputFolderLocation"] = "/run/user/1000/gvfs/smb-share:server=bigbird.ibb.gatech.edu,share=ngs/NovaSeq/EH08/FASTQ_Output/"
	emailSendingWrapper(subjectRunTest)
	"""
	
	"""
	subjectRunTest = {"Path": "", "runName": "EH08", "runInstrument":"NovaSeq", "FlowcellID":"H5KWGDRXY"}
	emailLocation emailDrafter(myRun)
	emailSender()
	"""
	
	"""
	inDexh = "/home/mecore/Desktop/timp/automation/testfolder_site/html/HGNTLBGXJ/MW58/all/all/lane.html"

	r = HTMLFileParse(inDexh)
	print(type(r))

	sel = CSSSelector('table')
	ok = sel(r)[2]

	sel2 = CSSSelector('h2')
	okx = sel(r)[2]

	ok9 = lxml.html.tostring(ok, pretty_print=True, encoding="unicode")
	print(type(ok))
	"""
	
		
main()