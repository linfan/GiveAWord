import sys
import re

class WordNode:
    def __init__(self, word):
        self.wd = word
        self.ex = ''
        self.eg = ''
        self.ps = ''
    def AddExplain(self, explain):
        self.ex += explain
        self.ex += ' ### '
    def AddExample(self, example):
        self.eg += example
        self.eg += ' ### '
    def AddPhonetic(self, phonetic):
        self.ps += phonetic
        self.ps += ' ### '

def help():
    print('Missing parameter, Usage:\ndsl2txt.py <dslFile> <txtFile>\n')
    sys.exit(1)

# output the word node
def writeNodeToFile(node, fileObj):
    explain = node.ex.rstrip('# ')
    example= node.eg.rstrip('# ')
    phonetic= node.ps.rstrip('# ')
    if explain != '':
        fileObj.write('@' + node.wd + ' ^1^ ' + explain + ' ^2^ ' + example + ' ^3^ ' + phonetic + '\n')

if len(sys.argv) < 3 :
    help()

dslFile = sys.argv[1]
txtFile = sys.argv[2]

# Open dsl file
try:
    dslFileObj = open(dslFile, 'r')
except IOError:
    print('[ ERROR ]: Cannot open dsl file ', dslFile)
    sys.exit(1)

# Open txt file
try:
    txtFileObj = open(txtFile, 'w')
except IOError:
    print('[ ERROR ]: Cannot open txt file ', txtFile)
    sys.exit(1)

# Analize content
wordBuf = []                                    # current word (one or more than one)

scLinePtn = re.compile(r'^[^ \t]')                             # section begin
dwLinePtn = re.compile(r'^([a-zA-Z]+)[\r\n]*$')                # word
exLinePtn = re.compile(r'^[^\[]*\[m1\].*?\{\{d\}\}(.+)')        # explain
psLinePtn = re.compile(r'.*\[c darkcyan\]\\\[(.+)\\\]\[/c\]')  # phonetic symbol
egLinePtn = re.compile(r'.*\{\{x\}\}(.+)\{\{/x\}\}.*')         # example

isValidWord = False
isHeadOfSection = False
try:
    dslFileLines = dslFileObj.readlines()
    for line in dslFileLines:                   # read each line
        if re.match(scLinePtn, line):           # begin of a section
            res = dwLinePtn.match(line)
            if res != None:                     # it is a word
                if not isHeadOfSection:         # add word in last section to list
                    for node in wordBuf:
                        writeNodeToFile(node, txtFileObj)
                    del wordBuf[:]
                isValidWord = True
                node = WordNode(res.group(1))
                wordBuf.append(node)
            else:                               # it is a idiom
                isValidWord = False
            isHeadOfSection = True
        else:
            isHeadOfSection = False
        if isValidWord:                         # in a valide word
            res = psLinePtn.match(line)
            if res != None:                     # read phonetic symbol
                for node in wordBuf:
                    phonetic = res.group(1)
                    node.AddPhonetic(phonetic)
            res = egLinePtn.match(line)
            if res != None:                     # read example
                for node in wordBuf:
                    example = res.group(1)
                    node.AddExample(example)
            res = exLinePtn.match(line)
            if res != None:                     # read explain
                for node in wordBuf:
                    explain = res.group(1)
                    # remove {{xx}} {{/xx}} block
                    while re.search(r'{{[/_a-z]*}}', explain) != None: 
                        explain = re.sub(r'{{[/_a-z]*}}', '', explain)
                    # remove up<<xx>> block
                    while re.search(r'.<<[ \-a-z]*>>', explain) != None: 
                        explain = re.sub(r'.<<([ \-a-z]*)>>', r'\1', explain)
                    # remove [xx] block
                    while re.search(r'\[[^\]]+\]*\]', explain) != None: 
                        explain = re.sub(r'\[[^\]]+\]*\]', '', explain)
                    # remove empty explain
                    if re.search(r'^[ ]*\(.*\)[ ]*$', explain):
                        continue
                    # remove redundant spaces
                    if explain.find(r'  ') > -1:
                        explain = re.sub(r'[ ]{2,}', ' ', explain)
                    if not explain.isspace() and explain != '':
                        node.AddExplain(explain)
    for node in wordBuf:                        # add the last word in buffer
        writeNodeToFile(node, txtFileObj)
        

finally:
    dslFileObj.close()
    txtFileObj.close()
