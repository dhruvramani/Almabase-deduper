import os
import re
import csv
import dedupe
from .models import File
from unidecode import unidecode
from django.http import HttpResponse
from django.views.static import serve
from django.shortcuts import render, redirect, get_object_or_404

BASE_DIR = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))

def touch(fname):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, 'a').close()

def preProcess(column):
    """
    Do a little bit of data cleaning with the help of Unidecode and Regex.
    Things like casing, extra spaces, quotes and new lines can be ignored.
    """
    try : # python 2/3 string differences
        column = column.decode('utf8')
    except AttributeError:
        pass
    column = unidecode(column)
    column = re.sub('  +', ' ', column)
    column = re.sub('\n', ' ', column)
    column = column.strip().strip('"').strip("'").lower().strip()
    # If data is missing, indicate that by setting the value to `None`
    if not column:
        column = None
    return column

def readData(filename):
    data_d = {}
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            clean_row = [(k, preProcess(v)) for (k, v) in row.items()]
            row_id = int(row['Id'])
            data_d[row_id] = dict(clean_row)

    return data_d

def unique(seq) :
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def index(request):
    if request.method == 'POST':
        fileObj = File()
        fileObj.name = request.POST.get('name', False)
        fileObj.desc = request.POST.get('desc', False)
        fileObj.file = request.FILES.get('file', False)
        fileObj.save()
        return redirect('page1', pk = fileObj.pk)

    if request.method == 'GET':
        return render(request,'main/fileUpload.html',None)

def page1(request, pk):
    fileObj = get_object_or_404(File, pk = pk)
    if request.method == 'GET':
        contents = list()
        f = open(BASE_DIR + '/data/training/' + str(fileObj.file.name), 'rt')
        contents = f.read().split('\n')[0].split(',')
        return render(request,'main/page1.html',{'name':fileObj.name ,'fields' : contents})

    if request.method == 'POST':
        count = int(request.POST.get('count', False))
        fields = list()

        for i in range(1,count+1):
            string = str(request.POST.get('section{}'.format(i), False))
            if string != 'False':
                fields.append(string)

        fileObj.attrList = ','.join(fields)
        fileObj.save()
        return redirect('page2', pk = pk)

flag = 0
deduper = None
fields = None
finished = False
uncertainPairLen = 0
uncertainPairCount = 0
uncertainPairs = None
mainCount = 0
data = None
data_d = None
labelsMatch = 0
labelsDistinct = 0

def page2(request, pk):
    global flag
    global deduper
    global finished
    global fields
    global uncertainPairLen
    global uncertainPairCount
    global uncertainPairs
    global mainCount
    global data
    global labelsDistinct
    global labelsMatch
    global data_d

    fileObj = get_object_or_404(File,pk = pk)
    data_d = readData(BASE_DIR + '/data/training/' + str(fileObj.file.name))
    if request.method == 'POST':
        inputF = request.POST.get('inputF')
        labelsDistinct =  int(request.POST.get('labelsDistinct'))
        labelsMatch = int(request.POST.get('labelsMatch'))
        
        if flag == 0:
            if finished == False:
                labels = {'distinct' : [], 'match' : []}
                if inputF == 'Y':
                    labels['match'].append(uncertainPairs[uncertainPairCount - 1])
                    labeled = True
                elif inputF == 'N':
                    labels['distinct'].append(uncertainPairs[uncertainPairCount - 1])
                    labeled = True
                else :
                    finished = True

                if labeled :
                    deduper.markPairs(labels)    
                labeled = False

                fieldLine = list()
                foo = uncertainPairs[uncertainPairCount - 1]
                for field in fields:
                    line = [field, foo[0][field], foo[1][field]]
                    fieldLine.append(line)
                uncertainPairs = deduper.uncertainPairs()
                data = {'labels' : [labelsDistinct, labelsMatch], 'tableData' : fieldLine, 'count' : len(fileObj.attrList.split(','))}
                if uncertainPairLen == 0 or uncertainPairCount == uncertainPairLen:
                    uncertainPairs = deduper.uncertainPairs()
                    uncertainPairLen = len(uncertainPairs)
                    uncertainPairCount = 0
                else :
                    uncertainPairCount = 1
            else :
                return redirect('page3', pk = pk)


        return HttpResponse(data, content_type = 'application/json')

    if request.method == 'GET':
        if finished == True:
            finished = False
            return redirect('page3', pk = pk)
        elif flag == 0:
            if mainCount == 0:
                fieldList = list()
                for i in fileObj.attrList.split(','):
                    fieldList.append({'field' : i, 'type' : 'String'})

                deduper = dedupe.Dedupe(fieldList)
                deduper.sample(data_d,15000)

                fields = unique(field.field for field in deduper.data_model.primary_fields)
                uncertainPairs = deduper.uncertainPairs()
                uncertainPairLen = len(uncertainPairs)
                uncertainPairCount = 0
                
                fieldLine = list()
                foo = uncertainPairs[0]
                for field in fields:
                    line = [field, foo[0][field], foo[1][field]]
                    fieldLine.append(line)
                data = {'labels' : [0,0], 'tableData' : fieldLine, 'count' : len(fileObj.attrList.split(','))}
                mainCount += 1
        return render(request, 'main/page2.html', data)

def page3(request, pk):
    global data_d
    global deduper
    fileObj = get_object_or_404(File,pk = pk)
    input_file = BASE_DIR + '/data/training/' + str(fileObj.file.name)
    output_file = BASE_DIR + '/data/output/output-' + str(fileObj.file.name).split('/')[-1]

    if os.path.isfile(output_file):
        return serve(request, os.path.basename(output_file), os.path.dirname(output_file))
    
    os.system("touch " + output_file)
    deduper.train()
    threshold = deduper.threshold(data_d, recall_weight=1)
    clustered_dupes = deduper.match(data_d, threshold)
    outputTo = len(clustered_dupes)

    cluster_membership = {}
    cluster_id = 0
    for (cluster_id, cluster) in enumerate(clustered_dupes):
        id_set, scores = cluster
        cluster_d = [data_d[c] for c in id_set]
        canonical_rep = dedupe.canonicalize(cluster_d)
        for record_id, score in zip(id_set, scores):
            cluster_membership[record_id] = {
                "cluster id" : cluster_id,
                "canonical representation" : canonical_rep,
                "confidence": score
            }
    singleton_id = cluster_id + 1

    with open(output_file, 'w') as f_output, open(input_file) as f_input:
        writer = csv.writer(f_output)
        reader = csv.reader(f_input)

        heading_row = next(reader)
        heading_row.insert(0, 'confidence_score')
        heading_row.insert(0, 'Cluster ID')
        canonical_keys = canonical_rep.keys()
        for key in canonical_keys:
            heading_row.append('canonical_' + key)

        writer.writerow(heading_row)

        for row in reader:
            row_id = int(row[0])
            if row_id in cluster_membership:
                cluster_id = cluster_membership[row_id]["cluster id"]
                canonical_rep = cluster_membership[row_id]["canonical representation"]
                row.insert(0, cluster_membership[row_id]['confidence'])
                row.insert(0, cluster_id)
                for key in canonical_keys:
                    row.append(canonical_rep[key].encode('utf8'))
            else:
                row.insert(0, None)
                row.insert(0, singleton_id)
                singleton_id += 1
                for key in canonical_keys:
                    row.append(None)
            writer.writerow(row)

    return serve(request, os.path.basename(output_file), os.path.dirname(output_file)) 