def unify(term1, term2):

    if (term1 is None and term2 is None): return {}
    if (term1 is None or term2 is None): return None

    # https://www.javatpoint.com/ai-unification-in-first-order-logic 

    if type(term1) is str: term1 = str.lower(term1)
    if type(term2) is str: term2 = str.lower(term2)

    # quick check - if equal then return
    if (term1 == term2): return {}

    # Step. 1: If Ψ1 or Ψ2 is a variable or constant, then:
    if (type(term1) is str or type(term2) is str):
    
        sTerm1 = str(term1)

        #  if term1 is a standalone variable
        if (sTerm1.startswith("?")) and (" " not in sTerm1):
        
            #  then just unify it with term2
            unification = {}
            unification[sTerm1] = term2
            return unification
        
        else:
        
            sTerm2 = str(term2)

            #  if term2 is a standalone variable
            if (sTerm2.startswith("?")) and (" " not in sTerm2):
        
                #  then just unify it with term1
                unification = {}
                unification[sTerm2] = term1
                return unification
            
            else:
                # return Text.TextbookUnifyStrings(sTerm1, sTerm2)
                return unify_strings(term1, sTerm2)
        
    elif (type(term1) is dict and type(term2) is dict):

        joTerm1 = term1
        joTerm2 = term2

        #  Step.2: If the initial Predicate symbol in Ψ1 and Ψ2 are not same, then return FAILURE.
        #  Relaxed - JSON Objects will not have a "head" predicate argument

        #  Step. 3: IF Ψ1 and Ψ2 have a different number of arguments, then return FAILURE.
        #  Relaxed - Will allow term1 to match term2 as long as term1 contains all arguments
        #  that are in term2 (term1 may contain more arguments than term2). Arguments will be
        #  matched by name

        # Step. 4: Set Substitution set(SUBST) to NIL. 
        subSet = {}

        # Step. 5: For i = 1 to the number of elements in Ψ1.
        for prop in joTerm2.keys():
    
            # ignore #seq (positional) information, as it is injected by the engine at runtime
            if (prop == "#seq-start"): continue
            if (prop == "#seq-end"): continue

            # can still use #seq-start and #seq-end in rules, just need to escape them with an extra #
            prop1 = prop
            if (prop == "##seq-start"): prop1 = "#seq-start"
            if (prop == "##seq-end"): prop1 = "#seq-end"

            # a) Call Unify function with the ith element of Ψ1 and ith element of Ψ2, and put the result into S.
            if prop1 not in joTerm1: return None
            jtTest1 = joTerm1[prop1]

            # b) If S = failure then returns Failure
            subSet2 = unify(jtTest1, joTerm2[prop])
            if (subSet2 is None): return None
            
            # c) If S ≠ NIL then do,
            elif (len(subSet2.keys()) > 0): subSet = {**subSet, **subSet2}
        
        return subSet
    
    return None

def unify_item_with_list(item, items:list):
    results = []
    for list_item in items:
        unification = unify_strings(item, list_item)
        if unification is not None:
            results.append(unification)
    if len(results) > 0: return results
    else: return None

def tokenize(s:str):
    s1 = s.split(' ')
    result = []
    for t in s1:
        if t.endswith("?") or t.endswith("."):
            punc = t[-1]
            text = t[:len(t)-1]
            result.append(text)
            result.append(punc)
        else:
            result.append(t)
    return result

def unify_strings(m1, m2):
    
    if (type(m1) is not str or type(m2) is not str): return None
    if (m1 == m2): return {}
    if (m1 == None) or (m2 == None): return None
    result = {}

    if "?" not in m1 and "*" not in m1 and "?" not in m2 and "*" not in m2 and m1[0] != m2[0]:
        return None
        
    # print("Comparing", m1, "to", m2)
    a1 = tokenize(m1)
    a2 = tokenize(m2)

    i1 = 0
    i2 = 0

    loop = True

    boundvalue = ""

    while (loop):

        w1 = a1[i1]
        w2 = a2[i2]

        w1 = remove_class_designation(w1)
        w2 = remove_class_designation(w2)

        if (w1 == w2):
            i1 = i1+1
            i2 = i2+1

        else:   

            v1 = v2 = wild1 = wild2 = False

            if (w1.startswith("?")): v1 = True
            if (w2.startswith("?")): v2 = True
            if (w1.startswith("*")): wild1 = True
            if (w2.startswith("*")): wild2 = True

            if (wild2 == True):

                n1 = ""
                n2 = ""

                if (i1 + 1 < len(a1)): n1 = a1[i1 + 1]
                if (i2 + 1 < len(a2)): n2 = a2[i2 + 1]

                if (w1 == n2):
                    i2 = i2+1
                else:
                    i1 = i1+1
        
            elif (wild1 == True):

                n1 = ""
                n2 = ""

                if (i1 + 1 < len(a1)): n1 = a1[i1 + 1]
                if (i2 + 1 < len(a2)): n2 = a2[i2 + 1]

                if (w2 == n1): i1 = i1+1            
                else: i2 = i2+1
            
            elif (v2 == True and v1 == False):
            
                boundvalue = boundvalue + " " + w1

                n1 = ""
                n2 = ""

                if (i1 + 1 < len(a1)): n1 = a1[i1 + 1]
                if (i2 + 1 < len(a2)): n2 = a2[i2 + 1]

                if (n1 == n2):
                
                    result[w2] = boundvalue.strip()
                    boundvalue = ""
                    i2=i2+1
                
                i1=i1+1
            
            elif (v1 == True and v2 == False):
            
                boundvalue = boundvalue + " " + w2

                n1 = ""
                n2 = ""

                if (i1 + 1 < len(a1)): n1 = a1[i1 + 1]
                if (i2 + 1 < len(a2)): n2 = a2[i2 + 1]

                if (n1 == n2):
                
                    result[w1] = boundvalue.strip()
                    boundvalue = ""
                    i1 = i1+1
            
                i2 = i2+1
            
            else:     
                loop = False
                
        # if at the end of m1 and we're sitting on a wildcard in m2, advance m2
        if (i1 == len(a1)):      
            if (i2 < len(a2)):         
                w2 = a2[i2]
                if (w2.startswith("*") == True):          
                    i2 = i2+1

        if (i1 == len(a1)): loop = False
        if (i2 == len(a2)): loop = False
    # while loop end

    if (i1 != len(a1) or i2 != len(a2)):
    
        if ((i1 + 1 == len(a1)) and (a1[i1] == "*")):
            pass
        else:
            result = None
        
    return result

def remove_class_designation(term):
    # remove class qualifiers (for now)
    if type(term) is str and str.startswith(term, "?") and ":" in term:
        idx = str.find(term, ":")
        term = term[0:idx]
    return term

def retrieve(term, unification):
    # substitute unification into the then part
    if str(term).startswith("#\\"):
        pass
    elif (term.startswith("?")) and (" " not in term):
        if term in unification:
            return unification[term]
        else:
            return term
    else:
        for key in unification.keys():
            new_val = str(unification[key])
            term = term.replace(key, new_val)
        return term
