from django.conf import settings

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'walkthedinosaur.settings'

from batchsql import models
from django.core.mail import send_mail
import connection
from sqlalchemy.orm import sessionmaker
from uuid import uuid1
import csv
from unidecode import unidecode
import time
import threading
import socket
import config
import urllib
import re

local = config.get_config('config.ini')['local']
IP_ADDRESS = ""
FILESERVER_PORT = config.get_config('config.ini')['port']
if local:
    IP_ADDRESS = socket.gethostbyname(socket.gethostname())
else:
    f = urllib.urlopen("http://www.canyouseeme.org/")
    html_doc = f.read()
    f.close()
    m = re.search('(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)',html_doc)
    IP_ADDRESS = m.group(0)

Session = sessionmaker(bind=connection.engine)
session = Session()

def create_output(job, result):
    filename = 'finished_jobs/'+str(uuid1())
    if job.requested_format == 'CSV':
        filename += '.csv'
        w = csv.writer(open(filename, 'w'))
        for row in result:
            row = filter(lambda x: x, row)
            row = [unidecode(unicode(x)) for x in row]
            w.writerow(row)
    elif job.requested_format == 'TSV':
        filename += '.tsv'
        w = csv.writer(open(filename, 'w'), delimiter='\t')
        for row in result:
            row = filter(lambda x: x, row)
            row = [unidecode(unicode(x)) for x in row]
            w.writerow(row)
    return filename

def get_job():
    conn = connection.engine.connect()
    if models.QueuedJob.objects.count() > 0:
        return models.QueuedJob.objects.all().order_by('id')[0]
    return None

def run_job(job):
    query = job.query_string
    result = session.execute(query)
    filename = create_output(job, result)
    return filename

def update_job_listing(job, filename):
    cj = models.CompletedJob.create(job, filename, 'Completed')
    models.QueuedJob.objects.filter(pk=job.id).delete()
    cj.save()

EMAIL_TEMPLATE = """
Hello,

Your Batch SQL job {0} running the query "{1}" has finished. Please download at {2}.

If you do not wish to recive further emails, please notify us at fungpat@berkeley.edu
or fierro@eecs.berkeley.edu.

- Fung Institute Patent Group (run_jobs.py) 
"""

def send_notification(job, filename):
    subject = 'Job {0} has finished'.format(job.id)
    port = FILESERVER_PORT
    url = "http://{0}:{1}/{2}".format(IP_ADDRESS, port, filename[14:])
    if not local:
        url = "http://{0}/{1}".format(IP_ADDRESS, filename)
    message = EMAIL_TEMPLATE.format(job.id, job.query_string, url)
    from_email = 'fungpatdatabaseinterface@gmail.com'
    to_email = [job.destination_email]
    print to_email
    send_mail(subject, message, from_email, to_email, fail_silently=False)
    #mail_thread = threading.Thread(target = send_mail, args=(subject, message, from_email, to_email), kwargs={"fail_silently":False})
    #mail_thread.start()
    #mail_thread.join()

while True:
    print 'Attempting to get job...'
    job = get_job()
    if job:
        print 'Got job', job.id
        print 'Running job', job.id
        job.job_status = 'Executing'
        job.save()
        filename = run_job(job)
        print 'Finished running job', job.id
        print 'Notifying user...'
        send_notification(job, filename)
        print 'Updating job listing...'
        update_job_listing(job, filename)
        print 'Finished'
    else:
        print 'Could not find job. Retrying in 5...'
        time.sleep(5)
