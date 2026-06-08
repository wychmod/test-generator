import json

s = json.load(open(r'D:\pycharm\test-generator\config\testcase-config-schema.json', encoding='utf-8'))
e = json.load(open(r'D:\pycharm\test-generator\config\example-config.json', encoding='utf-8'))

print('SCHEMA_ID=' + str(s.get('$id')))
print('EXAMPLE_ID=' + str(e.get('$id')))

# Walk schema and collect all required keys (top-level only)
top_required = s.get('required', [])
print('TOP_REQUIRED=' + str(top_required))

# Check that all top-level required keys exist in example
missing_top = [k for k in top_required if k not in e]
print('MISSING_TOP=' + str(missing_top if missing_top else 'NONE'))

# Validate $id match
id_match = (s.get('$id') == e.get('$id'))
print('ID_MATCH=' + ('PASS' if id_match else 'FAIL'))

print('RESULT=' + ('PASS' if not missing_top and id_match else 'FAIL'))
