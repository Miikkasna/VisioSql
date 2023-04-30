from vsdx import VisioFile

class SqlGen:
    def __init__(self, fname, schema=None, path="", auto_extract=False):
        self.MAX_FIELD_LEN = 32 # max length of a field name
        if auto_extract:
            self.tables = self.extract_data(path + fname, schema)

    def extract_data(self, path, schema):
        with VisioFile(path) as vis:
            tables = {}
            for pg in vis.pages:
                for shape in pg.all_shapes:
                    group = shape.shape_value('Type')
                    if group == 'Group':
                        child_chapes = shape.all_shapes
                        table_name = child_chapes[0].text.strip()
                        field_data = child_chapes[1].text
                        if table_name in tables.keys(): continue
                        if schema is None: 
                            schema = table_name.split('.')[0]
                            table_name = table_name.split('.')[1]
                        tables[table_name] = {'schema':schema, 'fields':{}}
                        for field in field_data.split('\n'):
                            if field != "":
                                data = field.split(chr(0x09))
                                key = data[0][:2]
                                field_name = data[1]
                                dtype = data[2]
                                tables[table_name]['fields'][field_name] = {'key':key, 'dtype':dtype}
        return tables

    def create_files(self, object_type, path):
        if object_type == 'tables': return self.create_tables(path)
        elif object_type == 'constraints': return self.create_constraints(path)
        else: return 0

    def create_tables(self, path):
        file_count = 0
        for table_name in self.tables.keys():
            schema = self.tables[table_name]['schema']
            table_sql = "-- " + schema + "." + table_name + " -table" + "\n" + "CREATE TABLE " + schema + "." + table_name + "("
            file_name = path + schema + "." + table_name + ".sql"
            file_count += 1
            with open(file_name, "w") as f:
                for field_name in self.tables[table_name]['fields'].keys():
                    dType = self.tables[table_name]['fields'][field_name]['dtype']
                    n_spaces = self.MAX_FIELD_LEN - len(field_name)
                    table_sql += "\n" + "\t" + field_name + " "*n_spaces + dType + ","
                table_sql = table_sql[:-1]
                table_sql = table_sql + "\n);"
                f.write(table_sql)
        return file_count

    def create_constraints(self, path):
        file_count = 0
        for table_name in self.tables.keys():
            schema = self.tables[table_name]['schema']
            for field_name in self.tables[table_name]['fields'].keys():
                key = self.tables[table_name]['fields'][field_name]['key']
                if key == "FK":
                    for table2_name in self.tables.keys():
                        schema2 = self.tables[table2_name]['schema']
                        for field2_name in self.tables[table2_name]['fields'].keys():
                            key2 = self.tables[table2_name]['fields'][field2_name]['key']
                            if key2 == "PK" and field_name == field2_name:
                                key_name = "FK_" + table_name + "_" + table2_name + "_" + field_name
                                file_name = path + key_name + ".sql"
                                file_count += 1
                                with open(file_name, "w") as f:
                                    sql_str = "-- foreign key between " + table_name + " and " + table2_name + " at " + field_name + "\n"
                                    sql_str += "ALTER TABLE " + schema + "." + table_name + " ADD CONSTRAINT " + key_name + "\n"
                                    sql_str += "FOREIGN KEY (" + field_name + ") REFERENCES " + schema2 + "." + table2_name + "(" + field2_name + ");"
                                    f.write(sql_str)
        return file_count

