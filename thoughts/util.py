
def convert_to_list(item):
    if isinstance(item, list):
        result = []
        for sub_item in item:
            result.extend(convert_to_list(sub_item))
        return result
    elif isinstance(item, str):
        return item.split('\n')
    else:
        return [item]
