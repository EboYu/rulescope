#!/usr/bin/python
import json
import re
import copy

output_file = open("data_to_injector.txt", 'w')

def type_parse(filename):
    fileHandle = open(filename)
    types = []
    lines = fileHandle.readlines()
    for line in lines:
        reg = re.compile(r'"(.+?)"')
        types.append(reg.findall(line)[0])
    fileHandle.close()
    return types

def rule_parse(types, rule_data):
    rule_list = []
    for i in range(len(rule_data)):
        #print rule_data[i]
        rule = []
        for feature in types:
            if feature in rule_data[i]:
                rule.append(rule_data[i][feature])
            else:
                rule.append(-1)
        #print rule
        rule_list.append([[rule]])

    return rule_list

'''def createPacket(subtraction, types):
    if subtraction == None:
        return {}

    rule = subtraction[0][0]
    packet = {}
    for i in range(len(rule)):
        if rule[i] != -1:
            value = rule[i]
            packet[types[i]] = value
    return packet
'''

import miniSAT

len_type = {}
def rule2cnf(rule, op, types):
    cur = 0
    ret = ""
    for ty in range(0,len(types)):
        typ = types[ty]
        if len_type.has_key(typ):
            ln = len_type[typ]
        else:
            ln = 1
        if rule[ty] == -1:
            cur += ln
            continue
        dt = rule[ty]
        for i in range(0,ln):
            if (dt&(1<<(ln-i-1))) > 0:
                if op > 0:
                    ret += " "+str(cur+ln-i)
                else:
                    ret += " "+"-"+str(cur+ln-i)
            else:
                if op < 0:
                    ret += " "+str(cur+ln-i)
                else:
                    ret += " "+"-"+str(cur+ln-i)
        cur += ln
    #print cur
    return ret

def ans2packet(ans, types):
    cur = 0
    ret = {}
    for ty in range(0,len(types)):
        typ = types[ty]
        if len_type.has_key(typ):
            ln = len_type[typ]
        else:
            ln = 1
        ret[typ] = 0
        for i in range(0,ln):
            ret[typ] <<= 1
            #print cur+ln-i
            if cur+ln-i>= len(ans):
                ret[typ] += 0
                continue
            f = int(ans[cur+ln-i])
            if f < 0:
                ret[typ] += 0
            else:
                ret[typ] += 1
        cur += ln
    return ret


def createPacket(subtraction, header_space, types):
    if subtraction == None:
        return {}
    cnf = "p cnf 100 "+str(len(header_space)+1)
    rule = subtraction[0][0]
    cnf += " "+rule2cnf(rule,1,types)+" 0"
    for header in header_space:
        rule = header[0][0]
        cnf += " "+rule2cnf(rule,-1,types)+" 0"
    #print cnf
    ans = miniSAT.solve(cnf)
    #print "inter:",subtraction
    #print "header_space",header_space
    print "ans:",ans
    ans = ans.split(' ')
    if ans[0] == 'SAT':
        return ans2packet(ans,types)
    packet = {}
    return packet

# problem
def findRule(sid, rid):
    return rule_list[rid]


# if rule id goes from 0 to N, and rules are sorted according to their id, works
def packetGenerator(edge_dict, rule_list, types):
    # containg all pkt, rule paris
    pairs = []

    header_space = []
    # variable rule1 and rule 2 are int.
    for rule1 in edge_dict:
        #print "rule1 =", rule1
        if edge_dict[rule1]:
            #print "rule has other rule to depend on"
            adj_list = edge_dict[rule1]
            #print "adj_list =", adj_list

            for rule2 in adj_list:
                #print data[rule]
                print "rule1 =", rule1
                print "rule2 =", rule2
                intersection = intersect_molecule(rule_list[rule1], rule_list[rule2])
                #print "intersection =", intersection
                # perhaps
                #subtraction = subtraction_wrapper(intersection, header_space)
                #print "subtraction =", subtraction
                #packet = createPacket(subtraction, types)
                packet = createPacket(intersection,header_space,types)
                #print "packet =", packet
                sendToInjector(packet)
                # include the packet and its rule pair
                header_space.append(rule_list[rule2])
                #print "header_space:"
                #print header_space

                tu = (rule2, packet)
                if tu not in pairs:
                    pairs.append(tu)
                #print "pairs =", pairs

                #header_space =
                # update header_space


        else:
            #print "rule has no ther rule depend on"
            #print "rule1 =", rule1

            #subtraction = subtraction_wrapper(rule_list[rule1], header_space)
            #print "subtraction =", subtraction

            #packet = createPacket(subtraction, types)
            packet = createPacket(rule_list[rule1],header_space,types)
            print "packet =", packet
            sendToInjector(packet)

            tu = (rule1, packet)
            if tu not in pairs:
                pairs.append(tu)
            #print "pairs =", pairs

    # should call Qi's module function, comment it for now, print instead
    # sendToInjector(pairs)
    print pairs


def sendToPostcardProcessor(rid,sid, num = 1000):
    pass

def sendToInjector(packet, switch_id = 1, num = 1000):
    output_file.write(str(packet))
    output_file.write('\n')


def include_singu(a,b):
	for i in range(0,len(a)):
		if (a[i] != b[i] and a[i] != -1):
			return False
	return True

#intersection of singu1 and singu2
# -1 means a wildcard
def intersect_singu(a,b):
	ans = []
	for i in range(0,len(a)):
		if (a[i] == b[i]):
			ans.append(a[i])
		elif (a[i] == -1):
			ans.append(b[i])
		elif (b[i] == -1):
			ans.append(a[i])
		else:             # a and b differing on any value domain indicates that they don't intersect
			return None
	return ans


# intersection of atom1 and atom2 : a new atom whose main area is the intersection of the two main areas
#                                   and whose holes are old holes of atom1 and atom2 that remain in the new main area
# Potential optimization: check repetition
def intersect_atom(a,b):
	ans=[]
	domain = intersect_singu(a[0],b[0])
	if (domain == None):
		return None
	ans.append(domain)
	for i in range(1,len(a)):
		temp = intersect_singu(domain, a[i])
		if (temp != None):
			ans.append(temp)
	for i in range(1,len(b)):
		temp = intersect_singu(domain, b[i])
		if (temp != None):
			ans.append(temp)
	for i in range(1,len(ans)):
		if (ans[i] == ans[0]):
			return None
	return ans
# using '^' to represent intersect
# atomA ([mainA, singuA1, singuA2....])  - atomB ([mainB, singuB1, singuB2, ...] =
#  [mainA, mainA ^ mainB, singuA1, singuA2.., singuAn] +
#  [singuBi ^ mainA ^ main B, singuA1, singuA2...., singuAn]
# Reason: any hole in A will still be a hole
#         intersection of mainA and mainB will be a new hole
#         the part of a hole in B that falls into (mainA^mainB) and doesn't intersect with any hole in A results in a concrete piece after A-B
#  always return a molecule
def subtract_atom(a,b):
	newAtom1 = []
	newDomain = intersect_singu(a[0],b[0])
	if (newDomain == None):
		return None
	for i in range(1,len(a)):
		if include_singu(a[i],newDomain):
			return None
	ans = []
	if (include_singu(newDomain,a[0]) == False):
		newAtom1.append(a[0])
		newAtom1.append(newDomain)
		for i in range(1,len(a)):
			if (include_singu(newDomain,a[i]) == False):
			#only subtract holes of A that don't fall into the new hole mainA^mainB
				newAtom1.append(a[i])
		ans.append(newAtom1)
	for i in range(1,len(b)):
		atomMain = intersect_singu(b[i],a[0]) #b[i] is already in mainB
		if (atomMain == None):
			continue
		newAtom = [];
		newAtom.append(atomMain)
		valid = True
		for j in range(1,len(a)):
			singu = intersect_singu(atomMain,a[j])
			if (singu != None):
				if (singu == atomMain):
					valid = False
					break
				else:
					newAtom.append(singu)
		if (valid):
			ans.append(newAtom)
	return ans
#moleculeA @ moleculeB = atoms in A @ atoms in B
# atoms in the same molecule don't intersect

# called by new_dag_generator
def intersect_molecule(a,b):
        #print "moleculeA: "
        #print a
        #print "moleculeB: "
        #print b

	ans = []
	for atomA in a:
		for atomB in b:
			newAtom = intersect_atom(atomA, atomB)
			if (newAtom != None):
				ans.append(newAtom)

        #print "ans:"
        #print ans
	if (len(ans) == 0):
		return None
	else:
		return ans


# this is not the most efficient but the correctness can be guarenteed.
# after A - B: all atoms in A don't intersect with any atom in B
# called by new_dag_generator.
def subtract_molecule(a,b):
        if a == None:
            return None

	ans = [copy.deepcopy(atom) for atom in a]
	cursor =0
	while (cursor < len(ans)):
		deleted = False
		for atom in b:
			temp = subtract_atom(ans[cursor],atom)
			if (temp != None):
				del ans[cursor]
				if (len(temp) == 0):  # A[cursor] is subtracted to empty
					deleted= True
					break
				ans.insert(cursor,temp[0]) # replace A[cursor] with a subtracted atom
				for i in range(1,len(temp)):
					ans.append(temp[i]) #append the rest subtracted atoms
		if (not deleted):
			cursor+=1
	if (len(ans) == 0):
		return None
	else:
		return ans

def subtraction_wrapper(intersection, header_space):
    subtraction = intersection
    if header_space == []:
        return subtraction

    for i in header_space:
        #print "i:"
        #print i
        subtraction = subtract_molecule(subtraction, i)
    return subtraction

#new dag generator
def new_dag_generator(rules):
	dag = []
	for i in range(len(rules)):
		match_range=copy.deepcopy(rules[i])
		if match_range == None:
			continue
		#print "loop on",i
		#print "---------------------------------"
		for j in range(i+1,len(rules)):
			#print "     and rule",j,":",rules[j]
		  if (rules[j] != None):
                        #print "rules[j]:"
                        #print rules[j]
			if intersect_molecule(match_range, rules[j])!=None:
				dag.append((i,j))
				#match_range = subtract_molecule(match_range,rules[j])
				#print "match changes to   ",match_range
				#print rules[i]
				#print rules[j]
				rules[j] = subtract_molecule(rules[j],rules[i])
				#print "rule",j,"changes to   ",rules[j]
	return dag

# without the trailing [] at the end of my rule
def new_rule_parse(types,filename):
	fileHandle = open(filename)
	rule_pattern = re.compile(r'pattern=([\s\S]*?)action=')
	content = fileHandle.read()
	#print content
	patterns = rule_pattern.findall(content)
	#print patterns
	rules=[]
	for line in patterns:
		rule=[]
		for type in types:
			pattern = type +'=(\d+?),'
			reg = re.compile(pattern)
			value = reg.findall(line)
			if len(value)==0:
				rule.append(-1)
			else:
				rule.append(int(value[0]))
		#print rule
		rules.append([[rule]])
	return rules

def LoadFile(filename):
    fileHandle = open(filename,'r');
    content = fileHandle.read()
    fileHandle.close()
    return content;
import json
def DAGLoader(filename):
    types = type_parse("typename.txt")
    f = LoadFile(filename)
    data = json.loads(f)
    dag = data["dependency"]
    ret_dag = {}
    for dep in dag:
        dep = dep.split(",")
        if not ret_dag.has_key(int(dep[0])):
            ret_dag[int(dep[0])] = []
        ret_dag[int(dep[0])].append(int(dep[1]))
    ret_rules = {}
    rules = data["table"]
    for line in rules:
        rule = {}
        for typ in types:
            if (not line.has_key(typ)) or (rule.has_key(typ)):
                continue
            if typ == "src-ip":
                dt = line[typ]
                dt = dt.split('/')
                ln = int(dt[1])
                dt = dt[0]
                dt = dt.split('.')
                ip = 0
                for i in dt:
                    ip <<=  8
                    ip += int(i)
                for i in range(0,ln):
                    if (ip&(1<<(31-i))) != 0:
                        rule["ipSrc"+str(i)] = 1
                    else:
                        rule["ipSrc"+str(i)] = 0

            elif typ == "dst-ip":
                dt = line[typ]
                dt = dt.split('/')
                ln = int(dt[1])
                dt = dt[0].split('.')
                ip = 0
                for i in dt:
                    ip <<=  8
                    ip += int(i)
                for i in range(0,ln):
                    if (ip&(1<<(31-i))) != 0:
                        rule["ipDst"+str(i)] = 1
                    else:
                        rule["ipDst"+str(i)] = 0
        rl = []
        for typ in types:
            if rule.has_key(typ):
                rl.append(rule[typ])
            else:
                rl.append(-1)
        ids = int(line["id"])
        ret_rules[ids] = [[rl]]

    return ret_rules, ret_dag
import random
import time
def IssueProbe(pkt, rules,v1,v2):
    print pkt
    if random.randint(0,1) == 0:
        return v1
    else:
        return v2
    for rule in rules:
        return rule
def packetGenerator_3(edge_dict, rule_list, types):
    S = []
    VV = []
    EE = []
    for v1 in edge_dict:
        vset = edge_dict[v1]
        for v2 in vset:
            S.append([v1,v2])
    while len(S) > 0:
        time.sleep(0.1)
        index = random.randint(0,len(S)-1)
        v1 = S[index][0]
        v2 = S[index][1]
        print len(S),index,v1,v2
        print VV,EE
        header_space = []
        for edge in EE:
            if edge[0] == v1 or edge[0] == v2:
                header_space.append(rule_list[edge[1]])
        intersection = intersect_molecule(rule_list[v1],rule_list[v2])
        T = (intersection,header_space)
        while True:
            time.sleep(0.1)
            subtraction = subtraction_wrapper(intersection, header_space)
            if subtraction == None:
                break

            pkt = createPacket(intersection,header_space,types)

            vhit = IssueProbe(pkt,rule_list,v1,v2)
            if not vhit in VV:
                VV.append(vhit)
            if vhit == v1:
                EE.append([v2,v1])
                del S[index]
                break
            if vhit == v2:
                EE.append([v1,v2])
                del S[index]
                break
            EE.append([v2,vhit])
            EE.append([v1,vhit])
            header_space.append(rule_list[vhit])
            S.remove(v1,vhit)
            S.remove(v2.vhit)
    return VV,EE




import sys
if __name__ == "__main__":

    if len(sys.argv) != 2:
        print "Usage: python algo.py dag_file"
        exit(0)
    dag_file = sys.argv[1]
    types = type_parse("typename.txt")

    #print types

    #print "len of types =", len(types)

    line_count = 1

    rule_list = {}
    edge_list = []
    edge_dict = {}

    # data preparation
    '''while True:
        line = f.readline()
        line = line[:-1]

        if line_count == 1:
            rule_list = line.split(' ')
            rule_list = [int(i) for i in rule_list]

            for i in rule_list:
                edge_dict[i] = []

        if line_count == 2:
            edge_list = line.split(' ')

            for i in edge_list:
                i = i[1:-1]
                i = i.split(',')
                edge_dict[int(i[0])].append(int(i[1]))

        if len(line) == 0:
            break

        line_count += 1

    data_file = open("data.json")
    rule_data = json.load(data_file)

    rule_list = rule_parse(types, rule_data)
    #print rule_list'''

    rule_list,edge_dict = DAGLoader(dag_file);

    #packetGenerator(edge_dict, rule_list, types)
    packetGenerator_3(edge_dict, rule_list, types)

    #print rule_list
    #print edge_list
    #print edge_dict


