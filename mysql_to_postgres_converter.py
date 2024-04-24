import re

def convert_sql(input_file_path, output_file_path):
    input_file_path = input_file_path.strip('"')
    output_file_path = output_file_path.strip('"')
    
    with open(input_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    enums = {}
    comments = []
    
    with open(output_file_path, 'w', encoding='utf-8') as file:
        in_create_table = False
        table_name = ""

        for line in lines:
            if line.strip().startswith('SET') or line.strip().startswith('/*!') or line.strip().startswith('START TRANSACTION'):
                continue

            # Remove MySQL-specific syntax
            line = re.sub(r" ENGINE=\w+", "", line)
            line = re.sub(r" DEFAULT CHARSET=\w+", "", line)
            line = re.sub(r" COLLATE=\w+", "", line)
            line = line.replace('`', '"').replace('longtext', 'text').replace('tinyint(1)', 'smallint')
            line = re.sub(r"int\(\d+\)", "integer", line)
            line = re.sub(r"double\(\d+,\d+\)", "numeric", line)
            line = line.replace('datetime', 'timestamp')
            line = re.sub(r"char\(.*?\)", "char", line)
            line = re.sub(r"varchar\(\d+\)", "varchar", line)
            line = line.replace('biginteger UNSIGNED', 'bigint').replace('UNSIGNED', '')
            line = re.sub(r"bigint\(20\) UNSIGNED", "bigint", line)
            line = re.sub(r"decimal\(\d+,\d+\)", "numeric", line)
            line = re.sub(r"CHARACTER SET utf8mb4 COLLATE utf8mb4_bin", "", line)

            # Replace current_timestamp() with current_timestamp
            line = re.sub(r"current_timestamp\(\)", "current_timestamp", line)

            # Capture ENUM-like patterns
            enum_match = re.search(r"(\w+)\s+boolean\s+NOT NULL\s+'([^']+)'", line)
            if enum_match:
                column_name = enum_match.group(1)
                enum_values = enum_match.group(2)
                enum_name = f"{table_name}_{column_name}"
                enums[enum_name] = enum_values
                line = f'"{column_name}" {enum_name} NOT NULL,'

            # Handling inline comments
            comment_match = re.search(r"COMMENT '([^']*)'", line)
            if comment_match:
                comment_text = comment_match.group(1)
                line = re.sub(r" COMMENT '([^']*)'", "", line)  # Remove COMMENT part from the line
                column_name = line.split()[0].strip('"')  # Assuming column name is the first word
                comments.append((table_name, column_name, comment_text))

            create_table_match = re.match(r"CREATE TABLE \"(\w+)\" \(", line)
            if create_table_match:
                in_create_table = True
                table_name = create_table_match.group(1)
                file.write(line)
                continue

            if in_create_table and line.strip().endswith(','):
                line = line.rstrip(',') + '\n'

            if in_create_table and line.strip().startswith(');'):
                in_create_table = False
                file.write(line)
                # Write comments for each column
                for comment in comments:
                    comment_statement = f"COMMENT ON COLUMN \"{comment[0]}\".\"{comment[1]}\" IS '{comment[2]}';\n"
                    file.write(comment_statement)
                comments = []  # Reset comments list for the next table
                continue

            file.write(line)

        # Write ENUM definitions at the end of the file
        for enum_name, values in enums.items():
            enum_statement = f"CREATE TYPE {enum_name} AS ENUM ({values});\n"
            file.write(enum_statement)

if __name__ == '__main__':
    input_path = input('Enter the path to the input SQL file: ')
    output_path = input('Enter the path to the output SQL file: ')
    convert_sql(input_path, output_path)
    print('Conversion completed. The adjusted SQL is saved in:', output_path)
