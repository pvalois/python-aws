#!/usr/bin/env python3
import os
from aws_local import client

s3 = client("s3")
bucket_name = "test"
response = s3.list_objects_v2(Bucket=bucket_name)

with open("/tmp/index.html", "w", encoding="utf-8") as f:
    f.write("<html><head><title>Index MinIO</title></head><body>\n")
    f.write(f"<h1>Photos dans {bucket_name}</h1><hr/>\n")

    # On itère sur le contenu renvoyé par le client
    for obj in response.get("Contents", []):
        fname = obj["Key"]

        # On évite d'inclure l'index lui-même dans la liste
        if fname == "index.html": continue

        if fname.lower().endswith(".jpg"):
            f.write(f'<a href="{fname}">{fname}</a><br/>\n')

    f.write("</body></html>")

print(f"Upload de index.html vers le bucket {bucket_name}...")
s3.upload_file( "/tmp/index.html", bucket_name, "index.html", ExtraArgs={'ContentType': 'text/html'})
