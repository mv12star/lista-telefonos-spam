#!/bin/bash

INPUT_FILE="${1:-contactos_spam.vcf}"
CHUNK_SIZE="${2:-500}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: El archivo $INPUT_FILE no existe"
    exit 1
fi

python3 - "$INPUT_FILE" "$CHUNK_SIZE" << 'PYEOF'
import re
import sys
import os
import zipfile

input_file = sys.argv[1]
chunk_size = int(sys.argv[2])

if not os.path.exists(input_file):
    print(f"Error: El archivo {input_file} no existe")
    sys.exit(1)

with open(input_file, 'r') as f:
    content = f.read()

telefonos = re.findall(r'item\d+\.TEL:(\d+)', content)
print(f"Total de telefonos: {len(telefonos)}")

base_name = input_file.replace('.vcf', '')
created_files = []

for i in range(0, len(telefonos), chunk_size):
    chunk = telefonos[i:i+chunk_size]
    num_file = i // chunk_size + 1
    
    vcf_content = f"BEGIN:VCARD\nVERSION:3.0\nFN:Spam{num_file}\n"
    for j, tel in enumerate(chunk, 1):
        vcf_content += f"item{j}.TEL:{tel}\n"
    vcf_content += "END:VCARD\n"
    
    filename = f"{base_name}_{num_file:03d}.vcf"
    with open(filename, 'w') as f:
        f.write(vcf_content)
    created_files.append(filename)
    print(f"Creado {filename} con {len(chunk)} contactos")

with open(f"{base_name}_todos.vcf", 'w') as f:
    f.write(content)
created_files.append(f"{base_name}_todos.vcf")
print(f"Creado {base_name}_todos.vcf (archivo general)")

zip_filename = f"{base_name}_chunks.zip"
with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in created_files:
        zipf.write(file)
        os.remove(file)
print(f"Creado {zip_filename} con {len(created_files)} archivos")
PYEOF
