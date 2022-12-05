import pandas as pd

SUPERSENSES = list(map(str.strip, '''
n.act
n.animal
n.artifact
n.attribute
n.body
n.cognition
n.communication
n.event
n.feeling
n.food
n.group
n.location
n.motive
n.natural_object
n.other
n.person
n.phenomenon
n.plant
n.possession
n.process
n.quantity
n.relation
n.shape
n.state
n.substance
n.time
v.body
v.change
v.cognition
v.communication
v.competition
v.consumption
v.contact
v.creation
v.emotion
v.motion
v.perception
v.possession
v.social
v.stative
v.weather
'''.strip().split()))

SUPER_SCHEME=dict()
for i in range(len(SUPERSENSES)):
    SUPER_SCHEME[SUPERSENSES[i]]=i
SUPER_SCHEME['unknown']=41
index2super = {i: l for l, i in SUPER_SCHEME.items()}
super2index = SUPER_SCHEME
#print('index2super: ', index2super)
#print('super2index: ', super2index)

LABEL_SCHEME = {'O': 0, 'o': 1, 'B': 2, 'b': 3, 'I': 4, 'i':5}
index2label = {i: l for l, i in LABEL_SCHEME.items()}
label2index = LABEL_SCHEME
#print('index2label: ', index2label)
#print('label2index: ', label2index)
file3 = open('/dimsumeval/dimsum16.test', 'r')
Lines = file3.readlines()

problem_line = 0

Results = []
count = 0
for line in Lines:
    part = line.split('\t')
    if len(part) > 1:
        if part[8] == 'tweebank.91\n':
            problem_line = count
            #print("problem line")
    else:
        count+=1
    Results.append(part)
       

#print(len(Results))


file1 = open('/dimsumeval/dimsum16.test.pred.mwe', 'r')
Lines = file1.readlines()
pred_mwe = []
for line in Lines:
    pred_mwe.append(index2label[int(line)])

#print(pred_mwe)

file2 = open('/dimsumeval/dimsum16.test.pred.ss', 'r')
Lines = file2.readlines()
pred_ss = []
for line in Lines:
    pred_ss.append(index2super[int(line)])

parent_offsets = [0] * len(pred_mwe)
token_offsets = [0] * len(pred_mwe)
df = pd.DataFrame(list(zip(token_offsets,pred_mwe, pred_ss, parent_offsets)),
               columns =['token_id','MWE', 'SS','offset'])
#print(df)
print(df.shape)
# print(df.loc[df['MWE'].isin(['B'])])
# #print(df.loc[df['SS'] != 'unknown'])

# #first find the loc of B and b
# idx_B = df.index[df['MWE'] == 'B']
# print(idx_B)
# print(type(idx_B))
# idxB_list = idx_B.values.tolist()
# print(type(idxB_list))

#split df to df list for each sentence
df_list = []

i = 0
j = 0
count = 0
for result in Results:
    if len(result) == 9:
        if result[1] != '"' and result[1] != '"£' and result[4] != '0' and result[7] != '0':
            df.at[j,'token_id'] = result[0]
            j += 1
    else:
        new_df = df.iloc[i:j,:].copy()
        i = j
        new_df.reset_index()
        df_list.append(new_df)
        count += 1

#print(df_list[0]) 
#print(df_list[3]) 
# print(df_list[problem_line])
# print("len of df_list: " + str(len(df_list)))
# idx_B = df_list[problem_line].index[df_list[problem_line]['MWE'] == 'B']
# idxB_list = idx_B.values.tolist()
# print(idxB_list)


count = 0
#for each df in df_list process mwe label
for df_sent in df_list:
    #print("sentID " + str(count))
    first_index = df_sent.index[0]
    if count == problem_line:
        print("first index = " + str(first_index))
    idx_B = df_sent.index[df_sent['MWE'] == 'B']
    idxB_list = idx_B.values.tolist()
    # if count == problem_line:
    #     print(idxB_list)
    #no B in the sentence, simply set all label to O
    if len(idxB_list) == 0:
        df_sent.loc[:,'MWE'] = 'O'
    else:
        #set the MWE label before first B to O
        id = idxB_list[0]
        for i in range(first_index,id):
            df_sent.at[i,'MWE'] = 'O'
        #for each B find I and edit offset accordingly
        for id_index in range(len(idxB_list)):
            #print("id_index: " + str(id_index))
            id = idxB_list[id_index]
            id = id - first_index
            parent_offset = df_sent.at[id+first_index,'token_id']
            last_I_index = -1
            exist_I = False
            #set up the search range for I, from current B to next B or to the end of the sentence
            max_index = df_sent.shape[0]
            if id_index+1 < len(idxB_list):
                max_index = idxB_list[id_index+1]-first_index
            for i in range(id,max_index):
                if df_sent.at[i+first_index,'MWE'] == 'I':
                    df_sent.at[i+first_index,'offset']= parent_offset
                    parent_offset = df_sent.at[i+first_index,'token_id']
                    last_I_index = i
                    exist_I = True
            #no I for B, set B as O
            if exist_I == False:
                df_sent.at[id+first_index,'MWE'] = 'O'
            
            #find b between B and last I
            if last_I_index != -1:
                #find b
                idxb_list = []
                for i in range(id,last_I_index):
                    if df_sent.at[i+first_index,'MWE'] == 'b':
                        idxb_list.append(i+first_index)
                #no b in the sentence, remove all i
                if len(idxb_list) == 0:
                    #print("no b")
                    for i in range(id,last_I_index):
                        if df_sent.at[i+first_index,'MWE'] == 'i':
                            print("exist i:" + str(df_sent.at[i+first_index,'MWE']))
                            df_sent.at[i+first_index,'MWE'] = 'o'
                else:
                    #remove i befor first b
                    for i in range(id,idxb_list[0]-first_index):
                        if df_sent.at[i+first_index,'MWE'] == 'i':
                            df_sent.at[i+first_index,'MWE'] = 'o'
                    #for each b, find i 
                    for id_b_index in range(len(idxb_list)):
                        id_b = idxb_list[id_b_index]
                        id_b = id_b - first_index
                        parent_offset = df_sent.at[id_b+first_index,'token_id']
                        exist_i = False
                        for i in range(id_b,last_I_index):
                            if df_sent.at[i+first_index,'MWE'] == 'i':
                                df_sent.at[i+first_index,'offset']= parent_offset
                                parent_offset = df_sent.at[i+first_index,'token_id']
                                exist_i = True
                        #no I for B, set B as O
                        if exist_i == False:
                            df_sent.at[id_b+first_index,'MWE'] = 'o'
    #after post processing, no B in the sentence       
    idx_B = df_sent.index[df_sent['MWE'] == 'B']
    idxB_list = idx_B.values.tolist()
    #no B in the sentence, simply set all label to O
    if len(idxB_list) == 0:
        df_sent.loc[:,'MWE'] = 'O'          
    count += 1
    #print(count)

    
print("len of df_list[0]: " + str(df_list[0].shape[0]))
print(df_list[problem_line]) 
#print(df[43:60])

def listToString(s):
 
    # initialize an empty string
    str1 = ""
    size = len(s)

    # traverse in the string
    i = 0
    for ele in s:
        str1 += ele
        if i < size-1:
            str1 += '\t'
        i += 1
 
    # return string
    return str1

file4 = open('/dimsumeval/dimsum16.test.pred', 'w')


Pred_results = []
count = 0
i = 0
#print(df_list[1].at[15,'MWE'])

for result in Results:
    r = []
    r = result.copy()
    if len(r) == 9:
        if r[1] != '"' and r[1] != '"£' and r[4] != '0' and r[7] != '0':
            #print("frameid = " + str(i))
            r[4] = str(df_list[count].at[i,'MWE'])
            r[5] = str(df_list[count].at[i,'offset'])
            if df_list[count].at[i,'SS'] != 'unknown':
                r[7] = str(df_list[count].at[i,'SS'])
            else:
                r[7] = ''
            i = i+1
        else:
            r[4] = 'O'
            r[5] = '0'
            r[7] = ''
    else:
        #print(i)
        #print("sentID = " + str(count))
        count += 1
        # break
    Pred_results.append(r)

print(count)
for result in Pred_results:
    line = listToString(result)
    file4.write(line)