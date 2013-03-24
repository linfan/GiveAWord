import sys, re, os, signal

WORK_DIR = sys.path[0]
DICT_FILE = WORK_DIR + '/dict'
USER_REPO = WORK_DIR + '/usrword'
OLD_REPO  = WORK_DIR + '/oldword'

SHOW_PHONETIC = True

def help():
    print('HELP !')
    sys.exit(0)

def grep(string, list, reverse = False):
    expr = re.compile(string)
    if reverse:
        return [elem for elem in list if not expr.match(elem)]
    else:
        return [elem for elem in list if expr.match(elem)]

def insertUserWord(word, info):
    ''' Add a new word into user repository '''
    if not os.access(USER_REPO, os.W_OK):
        print('[ ERROR ] User repostory file missing.')
        sys.exit(1)
    with open(USER_REPO, 'r+') as fileObj:
        lines = fileObj.readlines()
        res = grep('.*@' + word + ' ', lines)
        if res != []:
            print('[ INFO ] Word \'', word, '\' already in user repository.')
        else:
            fileObj.seek(0, os.SEEK_END)
            fileObj.write('0 ' + info + '\n')
            print('[ ADDED ] ', word)

def removeUserWord(word, notifyNoExist = False):
    ''' Remove a word from user repository '''
    if not os.access(USER_REPO, os.W_OK):
        print('[ ERROR ] User repostory file missing.')
        sys.exit(1)
    with open(USER_REPO, 'r') as fileObj:
        lines = fileObj.readlines()
        if notifyNoExist and grep('.*@' + word + ' ', lines) == []:
            print('>> Word \'', word, '\' no exist in repostory.')
            return
        newLines = grep('.*@' + word + ' ', lines, True)
    with open(USER_REPO, 'w') as fileObj:            # truncate the file
        fileObj.writelines(newLines)
    if notifyNoExist:
        print('[ INFO ] Word \'', word, '\' removed.')

def updateUserWord(word, info):
    ''' Modify a word in user repository '''
    removeUserWord(word)
    with open(USER_REPO, 'a') as fileObj:
        fileObj.write(info)

def lookUpWordInDict(word):
    ''' Find a word's define in diction file '''
    if not os.access(DICT_FILE, os.R_OK):
        print('[ ERROR ] Dictionary file missing.')
        sys.exit(1)
    with open(DICT_FILE) as fileObj:
        allWordInfos = fileObj.readlines()
        infos = grep('@' + word + ' ', allWordInfos)
        if infos != []:
            return infos[0]
        else:
            return None

def addUserWord(word):
    ''' Add a word into user repository '''
    if not os.access(DICT_FILE, os.R_OK):
        print('[ ERROR ] Dictionary file missing.')
        sys.exit(1)
    with open(DICT_FILE) as fileObj:
        allWordInfos = fileObj.readlines()
    wordInfos = grep('@' + word + ' ', allWordInfos)
    if wordInfos != []:
        info = wordInfos[0]
        insertUserWord(word, info.rstrip('\r\n'))
    else:
        print('>> Word \'', word, '\' no exist in dictionary.')

def addUserWordsFromFile(file):
    ''' Read a file, put words in the file to user repository '''
    if not os.access(DICT_FILE, os.R_OK):
        print('[ ERROR ] Dictionary file missing.')
        sys.exit(1)
    if not os.access(file, os.W_OK):
        print('[ ERROR ] Cannot write file ', file)
        sys.exit(1)
    with open(DICT_FILE) as fileObj:
        allWordInfos = fileObj.readlines()
    with open(file, 'r') as fileObj:
        unresolvedLines = []
        fileLines = fileObj.readlines()
        for line in fileLines:
            word = line.rstrip(' \t\r\n')
            if word == "":                      # skip empty line
                continue
            wordInfos = grep('@' + word + ' ', allWordInfos)
            if wordInfos != []:
                info = wordInfos[0]
                insertUserWord(word, info.rstrip('\r\n'))
            else:
                print('[ WARNING ] \'', word, '\' no exist in dictionary.')
                unresolvedLines.append(line)
    with open(file, 'w') as fileObj:              # truncate the file
        fileObj.writelines(unresolvedLines)

def selectWordFromRepo():
    ''' Choose a word from user repository to play '''
    if not os.access(USER_REPO, os.R_OK):
        print('[ ERROR ] User repostory file missing.')
        sys.exit(1)
    fileObj = open(USER_REPO, 'r')
    lines = fileObj.readlines()
    level = 10
    selectedLine = ""
    for line in lines:
        if len(line) > 1 and line[0].isdigit() and int(line[0]) < level:
            level = int(line[0])
            selectedLine = line
    if level < 0:
        print('[ ERROR ] User repostory is empty.')
        sys.exit(0)
    return selectedLine

def parseWordInfo(wordInfo):
    ''' Parse word info to separate fields '''
    wordInfo = re.sub(r' \^[0-9]\^ ', ' ^^^ ', wordInfo)
    infos = wordInfo.split(' @', 1)
    level = int(infos[0])
    infos = infos[1].split(' ^^^ ', 3)
    word = infos[0]
    explains = infos[1].split(' ### ')
    examples = infos[2].split(' ### ')
    phonetics = infos[3].split(' ### ')
    return level, word, explains, examples, phonetics

def showWordExplain(explains, showIndex = False):
    ''' Show word's explains in a regular format '''
    i = 1
    for ex in explains:
        if showIndex:
            print(i, ') ', ex.rstrip('\r\n'))
            i += 1
        else:
            print(ex.rstrip('\r\n').lstrip(' '))

def showWordExample(examples, showIndex = False):
    ''' Show word's examples a regular format '''
    i = 1
    for eg in examples:
        if re.search(r'[a-z]', eg) == None:     # Diction bug !
            continue
        if showIndex:
            print(i, ') ', eg.rstrip('\r\n ').lstrip(' '))
            i += 1
        else:
            print(eg.rstrip('\r\n').lstrip(' '))

def showWordPhonetic(phonetics):
    ''' Show word's examples a regular format '''
    print('[', phonetics[0].rstrip('\r\n '), ']')

def lookUpAWord(word):
    ''' Main enter of looking up a word '''
    info = lookUpWordInDict(word)
    if info != None:
        level, word, explains, examples, phonetics = parseWordInfo('0 @' + info)
        if SHOW_PHONETIC:
            showWordPhonetic(phonetics)
        showWordExplain(explains, True)
        print('E.g.')
        showWordExample(examples, True)
    else:
        print('>> Word \'', word, '\' no exist in dictionary.')

def giveAWord():
    ''' Main enter of guessing word game '''
    info = selectWordFromRepo()
    level, word, explains, examples, phonetics = parseWordInfo(info)
    showWordExplain(explains)
    ans = ""
    correct = True
    times = 0
    while ans != word:
        ans = input('it\'s : ')
        if ans == '?':
            print(word)
            correct = False
            break
        times += 1
    if SHOW_PHONETIC:
        showWordPhonetic(phonetics)
    if correct and times <= 2:
        level += 1
    elif level > 1:
        level -= 1
    info = str(level) + ' @' + word + ' ^1^ ' + ' ### '.join(explains) \
            + ' ^2^ ' + ' ### '.join(examples) + ' ^3^ ' + ' ### '.join(phonetics);
    updateUserWord(word, info)

def handle(signum, frame):
    os.system('clear')
    exit(0)

signal.signal(signal.SIGINT, handle)
if len(sys.argv) == 3:
    if sys.argv[1] == '-i':
        os.system('touch ' + USER_REPO)
        os.system('touch ' + OLD_REPO)
        addUserWordsFromFile(sys.argv[2])
    elif sys.argv[1] == '-d':
        removeUserWord(sys.argv[2], True)
    elif sys.argv[1] == '-a':
        addUserWord(sys.argv[2])
elif len(sys.argv) == 2:
    lookUpAWord(sys.argv[1])
elif len(sys.argv) == 1:
    giveAWord()
else:
    help()
