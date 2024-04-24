# Escrever um script Python que converta arquivos SQL do MySQL para PostgreSQL.

script_content = """
import re

def convert_sql(input_file_path, output_file_path):
    # Lê o arquivo SQL de entrada e adapta para PostgreSQL
    with open(input_file_path, 'r') as file:
        lines = file.readlines()
    
    with open(output_file_path, 'w') as file:
        in_create_table = False
        for line in lines:
            # Remove configurações específicas do MySQL e comandos não suportados
            if line.strip().startswith('SET') or line.strip().startswith('/*!') or line.strip().startswith('START TRANSACTION'):
                continue
            
            # Checar início de uma definição de tabela
            if line.strip().startswith('CREATE TABLE'):
                in_create_table = True
                line = line.replace('`', '\"')
            
            # Se estiver dentro de uma definição de tabela, continuar substituições
            if in_create_table:
                if line.strip().startswith(') ENGINE='):
                    in_create_table = False
                    line = ');\\n'  # Finalizar definição da tabela
                else:
                    # Substituir longtext por text e tinyint(1) por boolean
                    line = line.replace('`', '\"').replace('longtext', 'text').replace('tinyint(1)', 'boolean')
                    # Remover configurações de charset e collate específicas do MySQL
                    line = re.split('CHARACTER SET|COLLATE', line)[0] + '\\n'

            # Escrever a linha adaptada no novo arquivo
            if in_create_table or not line.strip().startswith(') ENGINE='):
                file.write(line)

if __name__ == '__main__':
    input_path = input('Enter the path to the input SQL file: ')
    output_path = input('Enter the path to the output SQL file: ')
    convert_sql(input_path, output_path)
    print('Conversion completed. The adjusted SQL is saved in:', output_path)
"""

# Vamos salvar este script em um arquivo Python para o usuário poder usar.
script_path = './mysql_to_postgres_converter.py'
with open(script_path, 'w') as file:
    file.write(script_content)

script_path
