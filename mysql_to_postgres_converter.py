import re

def convert_sql(input_file_path, output_file_path):
    input_file_path = input_file_path.strip('"')
    output_file_path = output_file_path.strip('"')
    
    with open(input_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    with open(output_file_path, 'w', encoding='utf-8') as file:
        in_create_table = False
        table_name = ""
        comments = []
        enums = {}
        
        for line in lines:
            if line.strip().startswith('SET') or line.strip().startswith('/*!') or line.strip().startswith('START TRANSACTION'):
                continue

            # Remove MySQL-specific storage and charset settings
            line = re.sub(r" ENGINE=\w+", "", line)
            line = re.sub(r" DEFAULT CHARSET=\w+", "", line)
            line = re.sub(r" COLLATE=\w+", "", line)

            # Convert MySQL data types and syntax to PostgreSQL
            line = line.replace('`', '"').replace('longtext', 'text').replace('tinyint(1)', 'boolean')
            line = re.sub(r"int\(\d+\)", "integer", line)
            line = re.sub(r"double\(\d+,\d+\)", "numeric", line)
            line = line.replace('datetime', 'timestamp')
            line = re.sub(r"char\(.*?\)", "char", line)
            line = re.sub(r"varchar\(.*?\)", "varchar", line)
            line = line.replace('biginteger UNSIGNED', 'bigint').replace('UNSIGNED', '')
            line = re.sub(r"bigint\(20\) UNSIGNED", "bigint", line)
            line = re.sub(r"decimal\(\d+,\d+\)", "numeric", line)
            line = re.sub(r"CHARACTER SET utf8mb4 COLLATE utf8mb4_bin", "", line)

            # Detecting and handling ENUM creation
            enum_match = re.search(r"'(.+?)'=>'(.+?)'", line)
            if enum_match:
                enum_name = table_name + "_" + enum_match.group(1)
                if enum_name not in enums:
                    enums[enum_name] = []
                enums[enum_name].append(enum_match.group(2))
                line = line.replace(enum_match.group(0), enum_name)
            
            create_table_match = re.match(r"CREATE TABLE \"(\w+)\" \(", line)
            if create_table_match:
                in_create_table = True
                table_name = create_table_match.group(1)
                file.write(line)
                continue

            comment_match = re.search(r"COMMENT '([^']+)'", line)
            if comment_match and in_create_table:
                column_name_match = re.match(r'\s*"(\w+)"', line)
                if column_name_match:
                    column_name = column_name_match.group(1)
                    comments.append((table_name, column_name, comment_match.group(1)))
                line = re.sub(r" COMMENT '([^']+)'", "", line)

            if in_create_table and line.strip().startswith(');'):
                in_create_table = False

            file.write(line)

        # Write ENUM definitions
        for enum_name, values in enums.items():
            file.write(f"CREATE TYPE {enum_name} AS ENUM ({', '.join(map(lambda v: f'\'{v}\'', values))});\n")

        # Append comments at the end
        for table, column, comment in comments:
            comment_statement = f"COMMENT ON COLUMN \"{table}\".\"{column}\" IS '{comment}';\n"
            file.write(comment_statement)

if __name__ == '__main__':
    input_path = input('Enter the path to the input SQL file: ')
    output_path = input('Enter the path to the output SQL file: ')
    convert_sql(input_path, output_path)
    print('Conversion completed. The adjusted SQL is saved in:', output_path)
