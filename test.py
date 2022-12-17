from collections import OrderedDict

generated = OrderedDict(
    **{
        "sample": "sample_class",
        "mark": "mark_class",
        "nugat": "nugat_class",
        "hallo": "peter_class",
        "nana": "nana_class",
        "karl": "karl_class",
        "drama": "drama_class",
    }
)

classes = ["fake1", "fake2", "fake3", "mark", "fake5", "fake6", "hallo", "fake8"]

x = OrderedDict()
x["mark"] = 3
x["hallo"] = 7


l = iter(x)
print(x)

first_in = 0
missing_classes = set([key for key in generated.keys() if key not in x])
existing_classes = [key for key in generated.keys() if key in x]

print(missing_classes)
print(existing_classes)

beforemap = {}
aftermap = {}


last_key = None
for existingkey in existing_classes:
    last_key = existingkey
    for key, value in generated.items():
        if existingkey == key:
            break
        if key in missing_classes:
            missing_classes.remove(key)
            beforemap.setdefault(x[existingkey], []).append(key)  # we need to reverse
