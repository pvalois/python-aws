#!/usr/bin/env python3

from aws_local import client
from pathlib import Path

s3 = client("s3")

p = Path("~/Images/Mangas/").expanduser()
files=[f for f in p.glob("*") if f.is_file()]

for cpt, file in enumerate(files[:20]):
    ext=file.suffix
    tname=f'{(cpt+1):04d}{ext}'
    tname=tname.strip()
    print ("Uploading",file,"as",tname)
    s3.upload_file(file,"test",tname)
