class Unification:
    """
    A class to unify two sentences (strings) that may contain wildcard variables.
    Wildcards are tokens beginning with '?'.

    Features:
      - Case-insensitive (optional).
      - Disallows zero-word matches for wildcards (optional).
      - Both sentences can have wildcards.
    
    Usage:
      unifier = Unification(disallow_zero_word_match=True, ignore_case=True)
      result = unifier.unify("My name is Bob", "My name is ?name")
      if result is not None:
          # result is a dict of wildcard -> list_of_matched_tokens
          # e.g. { '?name': ['bob'] }
    """

    def __init__(self, disallow_zero_word_match=True, ignore_case=True):
        """
        :param disallow_zero_word_match: If True, wildcards cannot match an empty sequence.
        :param ignore_case: If True, compare ordinary tokens case-insensitively.
        """
        self.disallow_zero_word_match = disallow_zero_word_match
        self.ignore_case = ignore_case

    def unify_text(self, sent1, sent2):
        """
        Attempt to unify sent1 with sent2 under this unifier's rules.

        :param sent1: First sentence (string).
        :param sent2: Second sentence (string).
        :return: A dict { '?var': [list, of, tokens], ... } if unification succeeds, or None if it fails.
        """
        # 1. Preprocess (case, tokenization)
        if self.ignore_case:
            sent1 = sent1.lower()
            sent2 = sent2.lower()
        w1_list = sent1.split()
        w2_list = sent2.split()

        # 2. We'll store wildcard assignments in a dict
        assignments = {}

        # 3. Kick off the recursion
        return self._unify_lists(w1_list, w2_list, assignments)

    def _unify_lists(self, lst1, lst2, assignments):
        """
        Recursively unify two lists of tokens, updating `assignments`.

        :param lst1: Tokens from the first sentence (list of strings).
        :param lst2: Tokens from the second sentence (list of strings).
        :param assignments: Dict of wildcard -> list_of_tokens so far.
        :return: Updated assignments on success, or None on failure.
        """

        # CASE A: Both lists empty => success
        if not lst1 and not lst2:
            return assignments

        # CASE B: One list empty, the other is not
        if not lst1 and lst2:
            # Next token in lst2 must be a wildcard that can consume leftover
            if not lst2[0].startswith('?'):
                return None
            var = lst2[0]
            # Remove the wildcard token from lst2 before chunking
            lst2_tail = lst2[1:]
            return self._unify_one_wildcard(
                wildcard_token=var,
                wildcard_list=lst2_tail,
                other_list=lst1,       # empty
                assignments=assignments,
                flipped=True
            )

        if lst1 and not lst2:
            # Symmetric scenario
            if not lst1[0].startswith('?'):
                return None
            var = lst1[0]
            lst1_tail = lst1[1:]
            return self._unify_one_wildcard(
                wildcard_token=var,
                wildcard_list=lst1_tail,
                other_list=lst2,       # empty
                assignments=assignments,
                flipped=False
            )

        # CASE C: Both lists have at least one token
        t1, t2 = lst1[0], lst2[0]
        is_var1 = t1.startswith('?')
        is_var2 = t2.startswith('?')

        # CASE C1: Both ordinary tokens => must match exactly
        if not is_var1 and not is_var2:
            if t1 != t2:
                return None
            # Match => unify the remainder
            return self._unify_lists(lst1[1:], lst2[1:], assignments)

        # CASE C2: Both are wildcards
        if is_var1 and is_var2:
            return self._unify_both_wildcards(t1, t2, lst1, lst2, assignments)

        if is_var1 and not is_var2:
            # We still remove the wildcard token from lst1,
            # but we set the *wildcard_list* to the other side 
            # (which still has real tokens to unify).
            lst1_tail = lst1[1:]  # leftover in the first list (might be empty or not)
            return self._unify_one_wildcard(
                wildcard_token=t1,
                wildcard_list=lst2,    # <-- CHUNK FROM HERE, since "Bob" is in lst2
                other_list=lst1_tail,  
                assignments=assignments,
                flipped=True           # Usually flipped, because now "other_list" is the remainder of lst1
            )

        if is_var2 and not is_var1:
            # Remove wildcard token from lst2
            lst2_tail = lst2[1:]  
            # But chunk from the FIRST list, because that's where the real word is
            return self._unify_one_wildcard(
                wildcard_token=t2,
                wildcard_list=lst1,      # <-- chunk from lst1
                other_list=lst2_tail,    # leftover from lst2
                assignments=assignments,
                flipped=False
            )

        # Should not get here logically
        return None

    def _unify_both_wildcards(self, v1, v2, lst1, lst2, assignments):
        """
        Handle the case where both lst1[0] and lst2[0] are wildcards.

        :param v1: Wildcard token (e.g. "?x")
        :param v2: Wildcard token (e.g. "?y")
        :param lst1: Entire list for the first side (including v1 at index 0)
        :param lst2: Entire list for the second side (including v2 at index 0)
        :param assignments: Current wildcard assignments
        :return: Updated assignments on success, or None on failure
        """
        a1 = assignments.get(v1)
        a2 = assignments.get(v2)

        # A) Both assigned => must match
        if a1 is not None and a2 is not None:
            if a1 == a2:
                return self._unify_lists(lst1[1:], lst2[1:], assignments)
            return None

        # B) One assigned, the other not => unify them
        if a1 is not None and a2 is None:
            assignments[v2] = a1
            res = self._unify_lists(lst1[1:], lst2[1:], assignments)
            if res is None:
                del assignments[v2]  # backtrack
            return res

        if a1 is None and a2 is not None:
            assignments[v1] = a2
            res = self._unify_lists(lst1[1:], lst2[1:], assignments)
            if res is None:
                del assignments[v1]
            return res

        # C) Assign both wilcards to each other
        assignments[v1] = v2
        assignments[v2] = v1
        r = self._unify_lists(lst1[1:], lst2[1:], assignments)
        if r is not None:
            return r
        return None

        # C) Neither assigned => unify the same (non-zero) slice from both sides
        # max_len = min(len(lst1), len(lst2)) - 1
        # start_size = 1 if self.disallow_zero_word_match else 0

        # for size in range(start_size, max_len + 1):
        #     slice1 = lst1[1 : 1 + size]
        #     slice2 = lst2[1 : 1 + size]

        #     if slice1 == slice2:
        #         assignments[v1] = slice1
        #         assignments[v2] = slice2
        #         r = self._unify_lists(lst1[1 + size:], lst2[1 + size:], assignments)
        #         if r is not None:
        #             return r
        #         del assignments[v1]
        #         del assignments[v2]
        # return None

    def _unify_one_wildcard(
        self,
        wildcard_token,
        wildcard_list,
        other_list,
        assignments,
        flipped=False
    ):
        """
        Handle the case where exactly one side is a wildcard, the other is ordinary or empty.

        :param wildcard_token: The wildcard (e.g. "?x").
        :param wildcard_list: The tokens in the wildcard's side, AFTER removing the wildcard token.
        :param other_list: The entire token list on the other side (could be empty or non-empty).
        :param assignments: Current dict of wildcard -> list_of_tokens.
        :param flipped: If True, it means "other_list" is effectively lst1 in unify_lists,
                        and "wildcard_list" is effectively lst2, so we reverse them when recursing.
        :return: Updated assignments or None on failure.
        """
        already = assignments.get(wildcard_token, None)
        length_w = len(wildcard_list)

        start_size = 1 if self.disallow_zero_word_match else 0

        # Try all possible chunk sizes for the wildcard match
        for size in range(start_size, length_w + 1):
            chunk = wildcard_list[:size]  # wildcard absorbs these
            remainder_w = wildcard_list[size:]

            # If this wildcard already has an assignment, it must match exactly
            if already is not None and already != chunk:
                continue

            newly_assigned = False
            if already is None:
                assignments[wildcard_token] = chunk
                newly_assigned = True

            # Now unify the remainder with the other list
            if flipped:
                # other_list is effectively the first arg to _unify_lists
                # remainder_w is effectively the second arg
                result = self._unify_lists(other_list, remainder_w, assignments)
            else:
                # remainder_w is the first arg
                # other_list is the second arg
                result = self._unify_lists(remainder_w, other_list, assignments)

            if result is not None:
                return result

            # Backtrack
            if newly_assigned:
                del assignments[wildcard_token]

        return None