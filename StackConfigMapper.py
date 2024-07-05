import os
import yaml

VERSION = "1.0-SNAPSHOT"


class Color:

    black = '\33[30m'
    red = '\33[31m'
    green = '\33[32m'
    gold = '\33[33m'
    blue = '\33[34m'
    purple = '\33[35m'
    cyan = '\33[36m'
    lightgray = lightgrey = '\33[37m'
    gray = grey = '\33[38m'
    white = reset = '\33[39m'

    bblack = '\33[40m'
    bred = '\33[41m'
    bgreen = '\33[42m'
    bgold = '\33[43m'
    bblue = '\33[44m'
    bpurple = '\33[45m'
    bcyan = '\33[46m'
    blightgray = blightgrey = '\33[47m'
    bgray = bgrey = '\33[48m'
    bwhite = '\33[49m'


def error(string, end='\n'):
    print(f'{Color.red}{string}', end=end)


def getYamlContext(file):
    try:
        result = yaml.load(file, Loader=yaml.FullLoader)
        if result is None:
            return {}
        return result
    except FileNotFoundError:
        error(f'文件 {file} 未找到')
        return {}
    except PermissionError:
        error(f'无权限打开文件 {file}')
        return {}


class CombinedDumper(yaml.Dumper):
    def __init__(self, *args, **kwargs):
        super(CombinedDumper, self).__init__(*args, **kwargs)
        self.sort_keys = lambda x: x

    def ignore_aliases(self, data):
        return True

    def represent_list(self, data):
        return self.represent_sequence('tag:yaml.org,2002:seq', data)

    def represent_mapping(self, tag, mapping, flow_style=None):
        value = []
        node = yaml.MappingNode(tag, value, flow_style=flow_style)
        if self.alias_key is not None:
            self.represented_objects[self.alias_key] = node
        best_style = True
        if hasattr(mapping, 'items'):
            mapping = getattr(mapping, 'items')()
        for item_key, item_value in mapping:
            node_key = self.represent_data(item_key)
            node_value = self.represent_data(item_value)
            node_type = yaml.ScalarNode
            if (not (isinstance(node_key, node_type) and not node_key.style) or not (isinstance(node_value, node_type) and not node_value.style)):
                best_style = False
            value.append((node_key, node_value))
        if flow_style is None:
            if self.default_flow_style is not None:
                node.flow_style = self.default_flow_style
            else:
                node.flow_style = best_style
        return node


CombinedDumper.add_representer(list, CombinedDumper.represent_list)
CombinedDumper.add_representer(dict, CombinedDumper.represent_dict)


def arg_sort(x):
    try:
        return ORDER.index(x[0])
    except ValueError:
        error(f'Unknown key: {x[0]}')
        return len(ORDER)


def dump(file, item):
    yaml.dump(
        item,
        file,
        allow_unicode=True,
        encoding='utf-8',
        Dumper=CombinedDumper,
        sort_keys=arg_sort,
        default_flow_style=False
    )


def mkFolder(folder):
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass
    finally:
        return


def copyTo(new_string, old_string, translate={}):
    global new, data
    new_split1 = new_string.split('.')
    old_split1 = old_string.split('.')

    new_split = []
    for a in new_split1:
        try:
            if a[0] == a[-1] and a[0] in {'\'', '\"'}:
                new_split.append(a[1:-1])
            else:
                new_split.append(int(a))
        except ValueError:
            new_split.append(a)
    old_split = []
    for a in old_split1:
        try:
            old_split.append(int(a))
        except ValueError:
            old_split.append(a)

    ndat = new
    odat = data
    for dddkey in old_split:
        try:
            odat = odat[dddkey]
        except KeyError:
            try:
                odat = odat[str(dddkey)]
            except KeyError:
                odat = NULL
    for dddkey in new_split:
        if dddkey == new_split[-1]:
            ndat[dddkey] = odat
            break
        if dddkey not in ndat:
            ndat[dddkey] = {}
        ndat = ndat[dddkey]
    if translate != {}:
        ndat[dddkey] = translate.get(odat, odat)


MATERIAL_TYPE_MAP = {"mc": "mc", "slimefun": "sf", "saveditem": "untranslatable", "none": "none"}
ORDER = (
    "machine",
    "recipes",
    "name",
    "duration",
    "energy",
    "input",
    "output",
    "type",
    "id",
    "amount"
)

NULL = "INVAILD_VALUE-MAPPER"
new = {}
old = {}


def main():
    mkFolder("output-configs")
    mkFolder("output-configs/recipe_machines")
    mkFolder("output-configs/generators")
    mkFolder("output-configs/solar_generators")
    mkFolder("output-configs/mat_generators")
    yml_files = [
        file for file in os.listdir('.')
        if os.path.isfile(file)
        and file.endswith('.yml')
    ]
    for file in yml_files:
        if file == "recipe_machines.yml":
            with open(file, 'r', encoding='utf-8') as f1:
                old = getYamlContext(f1)
                for machine_id in old:
                    with open("output-configs/recipe_machines/"+machine_id+".yml", 'w', encoding='utf-8') as f2:
                        new = {
                            "machine": machine_id,
                            "recipes": []
                        }
                        
                        energy = old[machine_id].get("energyPerCraft", 1)
                        speed = old[machine_id].get("speed", 1)
                        recipes = old[machine_id].get("recipes", {})
                        
                        for key in recipes:
                            recipe = recipes[key]
                            duration = recipe.get("seconds", 1)
                            raw_inputs = recipe.get("input", {})
                            raw_outputs = recipe.get("output", {})
                            inputs = []
                            outputs = []
                            for key2 in raw_inputs:
                                itemstack = raw_inputs[key2]
                                itemstack['material_type'] = MATERIAL_TYPE_MAP.get(itemstack.get('material_type', 'mc' if itemstack.get('material', NULL) != NULL else 'none'), "untranslatable")
                                if itemstack['material_type'] == "untranslatable":
                                    continue
                                if itemstack['material_type'] == "none":
                                    continue
                                itemstack['amount'] = itemstack.get('amount', 1)
                                inputs.append({
                                    "type": itemstack['material_type'],
                                    "id": itemstack['material'],
                                    "amount": itemstack['amount']
                                })
                                
                            lst = []
                            for key3 in raw_outputs:
                                itemstack = raw_outputs[key3]
                                itemstack['material_type'] = MATERIAL_TYPE_MAP.get(itemstack.get('material_type', 'mc' if itemstack.get('material', NULL) != NULL else 'none'), "untranslatable")
                                if itemstack['material_type'] == "untranslatable":
                                    continue
                                if itemstack['material_type'] == "none":
                                    continue
                                itemstack['amount'] = itemstack.get('amount', 1)
                                if itemstack.get("chance", -1) != -1:
                                    lst.append({
                                        "type": itemstack['material_type'],
                                        "id": itemstack['material'],
                                        "amount": itemstack['amount'],
                                        "weight": itemstack.get("chance", 100)
                                    })
                                else:
                                    outputs.append({
                                        "type": itemstack['material_type'],
                                        "id": itemstack['material'],
                                        "amount": itemstack['amount']
                                    })
                            if lst != []:
                                if recipe.get("chooseOne", False):
                                    c = 0
                                    for t in lst:
                                        chance = t.get("weight")
                                        c += chance
                                    if c < 100:
                                        lst.append({
                                            "type": "mc",
                                            "id": "air",
                                            "amount": 0,
                                            "weight": 100-c
                                        })
                                    outputs.append({
                                        "type": "weight",
                                        "list": lst
                                    })
                                else:
                                    for t in lst:
                                        chance = t.get("weight")
                                        outputs.append({
                                            "type": "weight",
                                            "list": [
                                                itemstack,
                                                {
                                                    "type": "mc",
                                                    "id": "air",
                                                    "amount": 0,
                                                    "weight": 100-chance
                                                }
                                            ]
                                        })
                            new['recipes'].append(
                                {
                                    "name": key,
                                    "duration": duration//speed,
                                    "energy": energy,
                                    "input": inputs,
                                    "output": outputs
                                }
                            )
                            
                        dump(f2, new)
        if file == "generators.yml":
            with open(file, 'r', encoding='utf-8') as f1:
                old = getYamlContext(f1)
                for machine_id in old:
                    with open("output-configs/generators/"+machine_id+".yml", 'w', encoding='utf-8') as f2:
                        new = {
                            "machine": machine_id,
                            "recipes": []
                        }
                        
                        energy = old[machine_id].get("production", 1)
                        fuels = old[machine_id].get("fuels", {})
                        
                        for key in fuels:
                            recipe = fuels[key]
                            duration = recipe.get("seconds", 1)
                            consume = recipe.get("item", {})
                            consume['material_type'] = MATERIAL_TYPE_MAP.get(consume.get('material_type', 'mc' if consume.get('material', NULL) != NULL else 'none'), "untranslatable")
                            if consume['material_type'] == "untranslatable":
                                continue
                            if consume['material_type'] == "none":
                                continue
                            consume['amount'] = consume.get('amount', 1)
                            consume = {
                                "type": consume['material_type'],
                                "id": consume['material'],
                                "amount": consume['amount']
                            }
                            output = recipe.get("output", {})
                            output['material_type'] = MATERIAL_TYPE_MAP.get(output.get('material_type', 'mc' if output.get('material', NULL) != NULL else 'none'), "untranslatable")
                            if output['material_type'] == "untranslatable":
                                continue
                            if output['material_type'] == "none":
                                continue
                            output['amount'] = output.get('amount', 1)
                            output = {
                                "type": output['material_type'],
                                "id": output['material'],
                                "amount": output['amount']
                            }
                            new['recipes'].append(
                                {
                                    "name": key,
                                    "duration": duration,
                                    "energy": energy,
                                    "input": [consume],
                                    "output": [output]
                                })
                        
                        dump(f2, new)
        if file == "solar_generators.yml":
            times = {
                4: [13670, 22330, 13670, 22330],
                5: [22331, 22491, 13509, 13669],
                6: [22492, 22652, 13348, 13508],
                7: [22653, 22812, 13188, 13347],
                8: [22813, 22973, 13027, 13187],
                9: [22974, 23134, 12867, 13026],
                10: [23135, 23296, 12705, 12866],
                11: [23297, 23459, 12542, 12704],
                12: [23460, 23623, 12377, 12541],
                13: [23624, 23790, 12210, 12376],
                14: [23791, 23960, 12041, 12209],
                15: [23961, 24000, 0, 12040]
            }
            with open(file, 'r', encoding='utf-8') as f1:
                old = getYamlContext(f1)
                for machine_id in old:
                    with open("output-configs/solar_generators/"+machine_id+".yml", 'w', encoding='utf-8') as f2:
                        new = {
                            "machine": machine_id,
                            "recipes": []
                        }
                        
                        de = old[machine_id].get("dayEnergy", 1)
                        ne = old[machine_id].get("nightEnergy", 1)
                        lightLevel = old[machine_id].get("lightLevel", 15)
                        
                        if lightLevel >= 4:
                            for level in range(4, lightLevel+1):
                                new['recipes'] += (
                                    {
                                        "name": key,
                                        "duration": 1,
                                        "energy": de,
                                        "conditions": [
                                            {
                                                "type": "time",
                                                "range": f"{times[level][0]}..{times[level][1]}",
                                                "display": f"要求光照等级为{level}"
                                            }
                                        ]
                                    },
                                    {
                                        "name": key,
                                        "duration": 1,
                                        "energy": de,
                                        "conditions": [
                                            {
                                                "type": "time",
                                                "range": f"{times[level][2]}..{times[level][3]}",
                                                "display": f"要求光照等级为{level}"
                                            }
                                        ]
                                    }
                                )
                            for level in range(lightLevel+1, 16):
                                new['recipes'] += (
                                    {
                                        "name": key,
                                        "duration": 1,
                                        "energy": ne,
                                        "conditions": [
                                            {
                                                "type": "time",
                                                "range": f"{times[level][0]}..{times[level][1]}",
                                                "display": f"要求光照等级为{level}"
                                            }
                                        ]
                                    },
                                    {
                                        "name": key,
                                        "duration": 1,
                                        "energy": ne,
                                        "conditions": [
                                            {
                                                "type": "time",
                                                "range": f"{times[level][2]}..{times[level][3]}",
                                                "display": f"要求光照等级为{level}"
                                            }
                                        ]
                                    }
                                )
                        
                        dump(f2, new)
        if file == "mat_generators.yml":
            with open(file, 'r', encoding='utf-8') as f1:
                old = getYamlContext(f1)
                for machine_id in old:
                    with open("output-configs/mat_generators/"+machine_id+".yml", 'w', encoding='utf-8') as f2:
                        new = {
                            "machine": machine_id,
                            "empty": []
                        }
                        
                        ready = []
                        duration = old[machine_id].get("tickRate", 1)
                        energy = old[machine_id].get("per", 1)
                        outputItem = old[machine_id].get("outputItem", {})
                        outputItem['material_type'] = MATERIAL_TYPE_MAP.get(outputItem.get('material_type', 'mc' if outputItem.get('material', NULL) != NULL else 'none'), "untranslatable")
                        if outputItem['material_type'] == "untranslatable":
                            continue
                        if outputItem['material_type'] == "none":
                            continue
                        outputItem['amount'] = outputItem.get('amount', 1)
                        outputItem = {
                            "type": outputItem['material_type'],
                            "id": outputItem['material'],
                            "amount": outputItem['amount']
                        }
                        
                        ready.append({
                            "name": machine_id,
                            "duration": duration,
                            "energy": energy,
                            "output": [outputItem]
                        })
                        
                        outputs = old[machine_id].get("outputs", {})
                        for itemstack in outputs.values():
                            itemstack['material_type'] = MATERIAL_TYPE_MAP.get(itemstack.get('material_type', 'mc' if itemstack.get('material', NULL) != NULL else 'none'), "untranslatable")
                            if itemstack['material_type'] == "untranslatable":
                                continue
                            if itemstack['material_type'] == "none":
                                continue
                            itemstack['amount'] = itemstack.get('amount', 1)
                            ready.append({
                                "name": machine_id,
                                "duration": duration,
                                "energy": energy,
                                "output": [itemstack]
                            })

                        new["empty"] = ready
                        dump(f2, new)


main()
