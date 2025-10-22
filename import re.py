import re

class MySQLToPostgresSQLFileModifier:
    def __init__(self, input_sql_file, output_sql_file):
        self.input_sql_file = input_sql_file
        self.output_sql_file = output_sql_file

    def modify_mysql_to_postgresql(self, sql_content):
        """
        Modify MySQL SQL dump to be compatible with PostgreSQL.
        """
        # Change AUTO_INCREMENT to SERIAL
        sql_content = sql_content.replace('AUTO_INCREMENT', 'SERIAL')
        
        # MySQL TINYINT(1) to PostgreSQL BOOLEAN
        sql_content = re.sub(r'TINYINT\(1\)', 'BOOLEAN', sql_content)
        
        # Remove MySQL ENGINE=InnoDB and CHARSET=utf8
        sql_content = sql_content.replace('ENGINE=InnoDB', '')
        sql_content = sql_content.replace('CHARSET=utf8', '')
        
        # Modify date and datetime types if needed (example: MySQL DATETIME to PostgreSQL TIMESTAMP)
        sql_content = sql_content.replace('DATETIME', 'TIMESTAMP')
        sql_content = sql_content.replace('DATE', 'DATE')
        
        return sql_content

    def modify_sql_file(self):
        """
        Read the MySQL SQL file, modify it for PostgreSQL, and write to the output file.
        """
        with open(self.input_sql_file, 'r', encoding='utf-8') as file:
            sql_content = file.read()

        # Modify the SQL content for PostgreSQL compatibility
        modified_sql_content = self.modify_mysql_to_postgresql(sql_content)
        
        # Write the modified SQL content to a new file
        with open(self.output_sql_file, 'w', encoding='utf-8') as file:
            file.write(modified_sql_content)
        
        print(f"SQL file has been modified and saved to: {self.output_sql_file}")


# Example usage:
input_sql_file = 'init.sql'  # Path to your MySQL dump file
output_sql_file = 'init_postgresql.sql'  # Path where the modified file will be saved

# Create an instance of the modifier and modify the SQL file
modifier = MySQLToPostgresSQLFileModifier(input_sql_file, output_sql_file)
modifier.modify_sql_file()
